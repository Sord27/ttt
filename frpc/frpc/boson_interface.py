
"""module containing boson interface class."""


from io import BytesIO
import logging
import os
from random import randint
import subprocess
import tarfile
from tempfile import NamedTemporaryFile
import threading
from typing import List, Tuple
from .argparse_type import irange
from .command import CommandType, CommandBuffer
from . import interface
from .ratelimit import Ratelimit
from . import targeting
from . import template


FIRST_INDEX = 1
LAST_INDEX = 99


logger = logging.getLogger(__name__)


def escape_script_body(script_body: str):
    """Escape special character for script body to be safe in cat command."""
    return (script_body
            .replace("\\", "\\\\")
            .replace("$", "\\$")
            .replace("`", "\\`"))


class BosonIndexGenerator:
    """Deterministic index generator that uniformely distributes load."""

    def __init__(self, seed: int = None):
        """Class constructor.

        Arguments:
            seed: seed for index generation. Use this to get reproducible
                  index sequences.
        """
        self.__lock = threading.Lock()
        self.__index = randint(FIRST_INDEX, LAST_INDEX) if seed is None \
            else seed

    def __call__(self, first: int = None, last: int = None) -> int:
        """Generate an index in range [first;last]."""
        if first is None:
            first = FIRST_INDEX

        if last is None:
            last = LAST_INDEX

        if first >= last:
            raise ValueError("expected last index to be greater than the last \
index, but got first ({}) >= last ({})".format(first, last))

        with self.__lock:
            index = self.__index % (last - first + 1) + first
            self.__index += 1

        return index


class BosonInterface(interface.Interface):
    """Boson interface implementation."""

    SCRIPT_NAME = "boson_base.sh"

    validate_index = irange(FIRST_INDEX, LAST_INDEX)

    # since all boson requests go through the `boson-ssh`,
    # we have to ratelimit the number of connections per second to 4
    __ratelimit = Ratelimit(1 / 4)

    __index_generator = BosonIndexGenerator()

    def __init__(self, macs: List[str], *args, boson_index=None,
                 index_generator=None, **kwargs):
        """Boson interface contructor.

        Arguments:
            macs (:list:`str`): pump MACs to connect to.
            boson_index (:obj:`tuple`|:obj:`int`, None): boson server index to
                use, leave this as None to randomly generate a suitable index,
                or pass a tuple to specify the index range for the
                random generator.
        """
        super().__init__(macs, *args, **kwargs)

        if index_generator is None:
            index_generator = self.__index_generator

        if boson_index is None:
            self.boson_index = index_generator()
        elif isinstance(boson_index, (tuple, list)) and len(boson_index) == 2:
            self.boson_index = index_generator(*boson_index)
        else:
            self.boson_index = BosonInterface.validate_index(boson_index)

    def open(self):
        """Open a connection over boson."""
        if self.is_open:
            logger.debug("interface already open")

            return

        logger.info(f"using {self.__mkserver()}")
        logger.debug("trying to open an interface")

        try:
            salt = self.__mksalt()
            cproc = self.__execute(f"ssh {{server}} 'echo -n {salt}'",
                                   capture_output=True, timeout=15)

            if cproc.stdout != salt:
                raise interface.FatalInterfaceError(
                        f"Expected `{salt}` from boson, got `{cproc.stdout}`")

            self.is_open = True
        except subprocess.CalledProcessError as err:
            raise interface.FatalInterfaceError(f"\
ssh call failed with code {err.returncode} (no vpn?): \
cmd = `{err.cmd}`, \
stdout = `{err.stdout}`, \
stderr = `{err.stderr}`") from err
        except subprocess.TimeoutExpired as err:
            raise interface.FatalInterfaceError("Boson connection timeout. \
(bad VPN connection?)") from err

    def execute(self, command_buffer: CommandBuffer) \
            -> List[interface.ExecutionResult]:
        """Execute the list of commands stored in the command_buffer."""
        commands = command_buffer.flush()
        filename, work_dir = self.__create_tar(commands)
        results = []

        try:
            remote_tar = f"{work_dir}.tar.gz"
            self.__execute(f"\
cat '{filename}' \
| ssh {{server}} '\
tar -xz --warning=no-timestamp \
&& cd {work_dir} \
&& ./scripts/{self.SCRIPT_NAME}; \
rc=$?; \
cd $OLDPWD; \
[[ $rc -eq 0 ]] && tar -czf {remote_tar} {work_dir}; \
rm -r {work_dir}; \
exit $rc\
'")

            self.__execute(f"scp {{server}}:{remote_tar} {filename}")
            self.__execute(f"ssh {{server}} 'rm {remote_tar}'")

            results = self.__unpack_results(commands, filename, work_dir)
        except subprocess.CalledProcessError as err:
            raise interface.InterfaceError(f"""\
One of the ssh calls failed (no vpn?), \
you may have to manually log into boson and remove temporary files.
The command failed with code {err.returncode}:
cmd = `{err.cmd}`,
stdout = `{err.stdout}`,
stderr = `{err.stderr}`""") from err
        # pylint: disable=fixme
        # TODO: add a timeout handler
        finally:
            os.unlink(filename)

        return results

    def get_online(self) -> List[str]:
        """Return list of active devices in `self.mac`.

        Throws:
            InterfaceError: operation failed because there was no connection or
                            the script returned invalid MAC list.
        """
        try:
            suffixes = {mac[-2:] for mac in self.macs}
            suffixes = f'suffixes="{" ".join(suffixes)}"'
            eof = f"{__name__}EOF{self.__mksalt()}"
            script_body = template.load_template("boson_get_online.sh",
                                                 suffixes=suffixes)

            script_body_esc = (escape_script_body(script_body)
                               .replace("{", "{{")
                               .replace("}", "}}"))

            cproc = self.__execute(f"""\
script_body=$(cat << {eof}
{script_body_esc}
{eof}
)
ssh {{server}} "$script_body"
""", capture_output=True)

            prefixes_online = targeting.fix_macs(cproc.stdout.splitlines())
            devices_online = targeting.device_registry_select(
                    self.macs, prefixes_online)

            logger.debug(f"prefixes_online = {len(prefixes_online)}, \
online from device registry = {len(devices_online)}")

            return devices_online
        except subprocess.CalledProcessError as err:
            raise interface.InterfaceError("SSH call failed") from err
        except targeting.ParseError as err:
            raise interface.InterfaceError("script output format error") \
                    from err

    @staticmethod
    def __mksalt():
        return str(randint(0, 10 ** 9))

    def __mkserver(self):
        return f"boson-boson{self.boson_index}"

    def __execute(self, cmd_format: str, capture_output: bool = False,
                  timeout: int = None) -> subprocess.CompletedProcess:

        cmd = cmd_format.format(server=self.__mkserver())

        with self.__ratelimit:
            logger.debug(f"running shell command `{cmd}`")

            cproc = subprocess.run(cmd, shell=True, text=True,
                                   capture_output=capture_output, check=True,
                                   timeout=timeout)

            logger.debug(f"shell command complete: {cproc}")

            return cproc

    def __mkscript(self, commands: List[tuple]) -> Tuple[str, List[tuple]]:
        iter_body = ""
        uploads = []

        for i, (command_type, *command_args) in enumerate(commands):
            if command_type is CommandType.EXEC:
                script_body_esc = escape_script_body(command_args[0])
                eof = f"{__name__}EOF{self.__mksalt()}"
                iter_body += f'''
    script_body{i}=$(cat << {eof}
{script_body_esc}
{eof}
)
    boson_ssh {i} $mac "$script_body{i}"'''
            elif command_type is CommandType.UPLOAD:
                remote_path, local_path = command_args
                local_name = os.path.basename(local_path)
                boson_path = f"uploads/{i}/{local_name}"
                iter_body += f"boson_scp {i} $mac {boson_path} \
$mac:\\'{remote_path}\\''"

                uploads.append((boson_path, local_path))

        return iter_body, uploads

    def __create_tar(self, commands: List[tuple]) -> Tuple[str, str]:
        suffix = ".tar.gz"
        fileobj = NamedTemporaryFile(suffix=suffix, prefix=__name__,
                                     delete=False)

        work_dir = os.path.basename(fileobj.name.replace(suffix, ""))
        iter_body, uploads = self.__mkscript(commands)

        with tarfile.open(mode="w:gz", fileobj=fileobj) as tarobj:
            for boson_path, local_path in uploads:
                tarobj.add(local_path,
                           arcname=os.path.join(work_dir, boson_path))

            macs = f'macs="{" ".join(self.macs)}"'
            script_bytes = template.load_template(self.SCRIPT_NAME,
                                                  macs=macs,
                                                  iter_body=iter_body).encode()

            tarinfo = tarfile.TarInfo(
                    os.path.join(work_dir, "scripts", self.SCRIPT_NAME))

            tarinfo.size = len(script_bytes)
            tarinfo.mode = 0o755

            tarobj.addfile(tarinfo, BytesIO(script_bytes))

        fileobj.close()

        return fileobj.name, work_dir

    @staticmethod
    def __read_param(tarobj: tarfile.TarFile, filepath):
        try:
            reader = tarobj.extractfile(filepath)
        except KeyError:
            return None

        if reader is None:
            logger.error(f"boson archive: `{filepath}` is not a file")

            return None

        return reader.read().decode("utf-8")

    def __unpack_results(self, commands, filename, work_dir):
        results = []

        with tarfile.open(filename) as tarobj:
            for mac in self.macs:
                for i, _ in enumerate(commands):
                    returncode = self.__read_param(
                            tarobj, f"{work_dir}/results/{mac}/rc.{i}")

                    if returncode is not None:
                        try:
                            returncode = int(returncode)
                        except ValueError:
                            logger.exception(f"\
returncode `{returncode}` is not an integer")

                            returncode = None

                    stdout = self.__read_param(
                            tarobj, f"{work_dir}/results/{mac}/stdout.{i}")

                    stderr = self.__read_param(
                            tarobj, f"{work_dir}/results/{mac}/stderr.{i}")

                    result = interface.ExecutionResult(
                            mac=mac, returncode=returncode,
                            success=returncode == 0,
                            stdout=stdout, stderr=stderr)

                    results.append(result)

        return results


class BosonInterfaceFactory(interface.InterfaceFactory):
    """Boson interface factory."""

    interface_cls = BosonInterface
