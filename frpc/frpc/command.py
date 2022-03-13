
"""Module containing remote command containers and helpers."""

from enum import Enum, auto
import os
import tarfile
from tempfile import NamedTemporaryFile
from typing import List


class CommandType(Enum):
    """Enumeration of remote command types."""

    EXEC = auto()
    UPLOAD = auto()


class CommandBuffer:
    """A container to optimize the number of interface calls."""

    def __init__(self):
        """Construct an empty buffer."""
        self.__buf = []
        self.__handlers = {
                CommandType.EXEC: self.__handle_exec,
                CommandType.UPLOAD: self.__handle_upload,
                }

        self.__last_cmd = None
        self.__last_script_body = ""
        self.__last_uploads = []
        self.__last_index = 0
        self.__files_to_unlink = []

    def __del__(self):
        """Class destructor to unlink temp files."""
        self.__unlink()

    def __enter__(self):
        """Enter function to make the class context manager compatible."""
        return self

    def __exit__(self, *_):
        """Exit context manager function to unlink temp files."""
        self.__unlink()

    def __iter__(self):
        """Flush queued commands into a list and return an iterator for it."""
        return iter(self.flush())

    def add_exec(self, script_body: str):
        """Queue up an EXEC command."""
        self.__cmd(CommandType.EXEC)
        self.__last_script_body += f"{script_body}\n"

    def add_upload(self, remote_path: str, local_path: str):
        """Queue up an UPLOAD command."""
        self.__cmd(CommandType.UPLOAD)
        self.__last_uploads.append((remote_path, local_path))

    def flush(self) -> List[tuple]:
        """Flush queued-up commands into a list."""
        self.__cmd(None)

        buf = self.__buf
        self.__buf = []
        self.__last_index = 0

        return buf

    def __cmd(self, cmd: CommandType):
        """Finalize last command group, if necessary."""
        if self.__last_cmd is None:
            self.__last_cmd = cmd
        elif self.__last_cmd is not cmd:
            self.__handlers[self.__last_cmd]()

            self.__last_cmd = cmd

    def __mkindex(self):
        i = self.__last_index
        self.__last_index += 1

        return i

    def __handle_exec(self):
        self.__buf.append((CommandType.EXEC, self.__last_script_body))

        self.__last_script_body = ""

    def __handle_upload(self):
        fileobj = NamedTemporaryFile(suffix=".tar.gz", prefix=__name__,
                                     delete=False)

        fileobj_name = os.path.basename(fileobj.name)
        unpack_cmd = f"""\
#!/bin/bash
cd /tmp
tar -xf '{fileobj_name}'
rm -v '{fileobj_name}'
"""

        with tarfile.open(mode="w:gz", fileobj=fileobj) as tarobj:
            for remote_path, local_path in self.__last_uploads:
                local_name = os.path.basename(local_path)
                arcname = f"{local_name}.{fileobj_name}{self.__mkindex()}"
                unpack_cmd += f"""\
mv -v '{arcname}' '{remote_path}'
rm -v '{arcname}'
"""

                tarobj.add(local_path, arcname=arcname)

        self.__files_to_unlink.append(fileobj.name)
        self.__buf.append(CommandType.UPLOAD, f"/tmp/{fileobj_name}",
                          fileobj.name)

        self.__last_uploads = []

        self.add_exec(unpack_cmd)

    def __unlink(self):
        for filepath in self.__files_to_unlink:
            os.unlink(filepath)

        self.__files_to_unlink = []
