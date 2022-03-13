
"""Module describing program behaviour for running scripts on remote pumps."""

from argparse import ArgumentParser
import logging
from .base_frpc import BaseFRPC
from .script_executor import ScriptExecutor, get_scripts


logger = logging.getLogger(__name__)


class FRPCScript(BaseFRPC):
    """CLI implementation for running scripts on remote pumps."""

    def __init__(self):
        """CLI implementation constructor."""
        self.argparser = ArgumentParser(
                description="Run a bash script on a list of remote pumps")

        super().__init__()

        scripts = ", ".join(get_scripts())

        self.argparser.add_argument("--script", type=str, nargs="+",
                                    required=True, help=f"\
either built-in script name ({scripts}) or a path to a script")

    def exec(self):
        """Go over the list of macs and run the specified script on them."""
        try:
            script_bodies = [ScriptExecutor.get_script_body(script)
                             for script in self.args.script]

            self._exec(ScriptExecutor(script_bodies=script_bodies))
        except OSError as err:
            logger.critical(f"couldn't load script {self.args.script}: {err}")


#    def exec(self):
#        """Go over the list of macs and run the specified script on them."""
#        with self.args.interface.to_cls()(self.macs,
#                                          self.args.boson_index) as interface:
#            with CommandBuffer() as command_list:
#                command_list.add_exec("echo hello!")
#
#                interface.execute(command_list)
