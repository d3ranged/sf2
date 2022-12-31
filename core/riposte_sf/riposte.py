'''
RiposteSF - fork of riposte-0.4.1 for SignFinder-2.0
'''

from pathlib import Path
import itertools
import argparse
import atexit
import sys
import os


USE_POSIX = os.name != 'nt'


import shlex
from typing import Callable, Dict, Iterable, List, Optional, Sequence

from . import input_streams
from .command import Command
from .exceptions import CommandError, RiposteException, StopRiposteException
from .flag_parser import *
from .data_vars import *
from .completer import *


from thirdparty.rich.console import Console
console = Console()

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style as PromptStyle
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit import print_formatted_text, HTML


class PrinterSF:

    block_stdout = False
    console = console

    def print(self, *objects, sep=' ', end='\n', file=sys.stdout, flush=False):
        if self.block_stdout: return
        self.console.print(*objects, sep = sep, end = end, highlight=False)

    def error(self, *args):
        self.print('[red][!][/red]', *args)

    def status(self, *args):
        self.print('[blue][*][/blue]', *args)

    def info(self, *args):
        self.print('[i]', *args)

    def success(self, *args):
        self.print('[green][+][/green]', *args)  

    def disable(self):
        self.block_stdout = True

    def enable(self):
        self.block_stdout = False

    def get_max_width(self):
        return self.console.width


class RiposteSF(PrinterSF):

    def __init__(
        self,
        prompt: str = "RiposteSF:~ $ ",
        banner: Optional[str] = None,
        version: Optional[str] = 'Unknown version',
        history_file: Path = Path.home() / ".RiposteSF",
        history_length: int = 100,
        autoconf_file = None,
        cls_after_cmd = False,
        double_newline = False,
    ):
        self.file_stream = None
        self.banner = banner
        self.version = version
        self.autoconf_file = Path(autoconf_file)
        self.cls_after_cmd = cls_after_cmd
        self.double_newline = double_newline

        self.print_banner = True
        self.cli_parser = None
        self.cli_arguments = None

        self.set_prompt(prompt)
        self.prompt_session = PromptSession(history=FileHistory(history_file))

        self.completer = CmdCompleter(lambda: self._cmd_list(), sentence = True)
        self.repl_stream = input_streams.any_input(self._run_prompt)
        self.input_stream = self.repl_stream

        self.aliases = VarManager()
        self.vars = VarManager2()

        self._commands: Dict[str, Command] = {}
        self.cmd_counter = 0

        self.setup_cli()
        

    def _run_prompt(self):
        return self.prompt_session.prompt(
            self.prompt,
            completer = self.completer,
            complete_style = CompleteStyle.READLINE_LIKE
        )

    def ask_prompt(self, text):
        return self.prompt_session.prompt(text)

    def _cmd_list(self) -> List[str]:
        # append space -> separate cmd and args
        return list(cmd + ' ' for cmd in self._commands.keys())


    @staticmethod
    def _split_inline_commands(line: str) -> List[str]:
        """ Split multiple inline commands. """
        parsed = shlex.split(line, posix=False)
        
        commands = []
        command = []
        for element in parsed:
            if element[-2:] == "\\;":
                command.append(element)
            elif element[-2:] == ";;":
                raise CommandError("unexpected token: ;;")
            elif element[-1] == ";" and element[:-1] != "":
                command.append(element[:-1])
                commands.append(command)
                command = []
            elif element[-1] == ";" and element[:-1] == "":
                commands.append(command)
                command = []
            else:
                command.append(element)

        if command:
            commands.append(command)

        return [" ".join(command) for command in commands if command]


    @staticmethod
    def _parse_line(line: str) -> List[str]:
        """ Split input line into command's name and its arguments. """
        try:
            return shlex.split(line, posix=USE_POSIX)
        except ValueError as err:
            raise RiposteException(err)


    def _get_command(self, command_name: str) -> Command:
        """ Resolve command name into registered `Command` object. """
        try:
            return self._commands[command_name]
        except KeyError:
            raise CommandError(f"Unknown command")


    def setup_cli(self):
        """Initialize CLI

        Overwrite this method in case of adding custom arguments.
        """
        self.cli_parser = argparse.ArgumentParser()
        self.cli_parser.add_argument(
            "file", nargs="?", default=None,
            help="stdin as file (try without args first)"
            )
        self.cli_parser.add_argument(
            "-c", "-C",
            metavar="commands",
            help="commands list, delimited with semicolon",
        )
        self.cli_parser.add_argument(
            "-v", "-V",
            help="show version",
            action='store_true'
        )


    def parse_cli_arguments(self) -> None:
        """Parse passed CLI arguments

        Overwrite this method in order to parse custom CLI arguments.
        """
        self.cli_arguments = self.cli_parser.parse_args()

        if self.cli_arguments.c:
            self.print_banner = False
            self.input_stream = input_streams.cli_input(self.cli_arguments.c)
        elif self.cli_arguments.file:
            self.print_banner = False
            self.input_stream = input_streams.file_input(
                Path(self.cli_arguments.file)
            )
            self.file_stream = self.input_stream
        elif self.cli_arguments.v:
            self.print(self.version)
            sys.exit()


    def set_prompt(self, prompt):
        prefix = '\n' if self.double_newline else ''
        self.prompt = prefix + prompt
        self.prompt = HTML('<lightgreen>' + self.prompt + '</lightgreen>')


    def set_noflags(self, cmd_name, value = True):
        cmd_obj = self.repl._commands[cmd_name] 
        setattr(cmd_obj, 'no_flags', value)


    def _check_noflags(self, obj):
        if hasattr(obj, 'no_flags'):
            return obj.no_flags


    def check_noflags(self, command):
        if self._check_noflags(command): return True
        cmd_instance = command._func.__self__
        return self._check_noflags(cmd_instance)


    def attach_flags(self, command, *args):
        cmd_instance = command._func.__self__
        # add flags support
        flags = FlagParser().parse(args)
        setattr(cmd_instance, 'flags', flags)
        args = FlagParser().remove_flags(args)
        return args, flags


    def _execute(self, command_name, *args):
        try:
            command = self._get_command(command_name)

            # move flags to command attribute
            # so riposte can work as usual

            if not self.check_noflags(command):
                args, flags = self.attach_flags(command, *args)

            command.execute(*args)

            self.cmd_counter += 1

        except (ValueError) as err:
            self.error(err)


    def _replace_aliases(self, line):
        cmd_name, *args = self._parse_line(line)

        for alias in self.aliases.names():
            if cmd_name == alias:
                full = self.aliases.get(alias)
                line = line.replace(alias, full, 1)
                break # only one at time
        return line


    def _check_novars(self, obj):
        if hasattr(obj, 'no_vars'):
            return obj.no_vars

    def check_novars(self, cmd_name):
        command = self._get_command(cmd_name)
        if self._check_novars(command): return True
        cmd_instance = command._func.__self__
        return self._check_novars(cmd_instance)


    def _get_cmd_and_args(self, line):

        last_cmd = ''
        last_args = list()
        tokens = self._parse_line(line)

        for idx, token in enumerate(tokens):

            temp_cmd = ' '.join(tokens[0:idx+1])

            if temp_cmd in self._commands:
                last_cmd = temp_cmd
                last_args = tokens[idx+1:]

        return last_cmd, *last_args


    def clear_screen(self):
        os.system('cls' if os.name=='nt' else 'clear')

    def _double_line_margin(self):
        if self.double_newline:
            self.print() 

    def _save_cmd_line(self, command_name, *args):
        self.cmd_line = command_name + ' ' + ' '.join(*args)

    def get_cmd_line(self):
        return self.cmd_line

    def is_interactive(self):
        return self.input_stream == self.repl_stream

    def is_file_input(self):
        return self.input_stream == self.file_stream

    def _process(self) -> None:

        user_input = next(self.input_stream)()
        if not user_input:
            return

        if self.cls_after_cmd & self.is_interactive():
            self.clear_screen()
            print_formatted_text(self.prompt, user_input, sep='')

        self._double_line_margin()

        for line in self._split_inline_commands(user_input):

            new_line = self._replace_aliases(line)

            for sub_line in self._split_inline_commands(new_line):

                # for external script - show input cmd
                if self.is_file_input():
                    print_formatted_text(self.prompt, sub_line, sep='')

                # parse input line, etc
                command_name, *args = self._get_cmd_and_args(sub_line)

                if not self.check_novars(command_name):
                    # unknown variable will raise ValueError
                    args = self.vars.replace_list(args)
                
                self._save_cmd_line(command_name, args)

                # run main
                self._execute(command_name, *args)


    def _process_autoconf(self):
        if not self.autoconf_file: return
            
        if not self.autoconf_file.exists():
            open(self.autoconf_file, 'a').close()
            return

        old_stream = self.input_stream
        self.input_stream = input_streams.file_input(Path(self.autoconf_file))

        while True:
            try:
                self._process()
            except (ValueError, RiposteException) as err:
                self.error(err)
            except StopRiposteException as err:
                self.error(err)
                break
            except EOFError:
                break
            except StopIteration:
                break
            finally:
                pass

        self.input_stream = old_stream
    

    def run(self) -> None:

        self.disable()
        self._process_autoconf()
        self.enable()        

        self.parse_cli_arguments()

        if self.banner and self.print_banner:
            self.print(self.banner, end='')

        while True:
            try:
                self._process()
            except (ValueError, RiposteException) as err:
                self.error(err)
            except StopRiposteException as err:
                self.error(err)
                break
            except EOFError:
                break
            except StopIteration:
                break
            except KeyboardInterrupt:
                self.print()
            finally:
                pass


    def _remove_multi_tabs(self, input):
        return ' '.join(self._parse_line(input))

    def add_command(self, name, description, func, manual = None):

        name = self._remove_multi_tabs(name)

        if name not in self._commands:
            self._commands[name] = Command(name, func, description, None, manual)
        else:
            raise RiposteException(f"'{name}' command already exists.")

    def free_commands(self):
        self._commands: Dict[str, Command] = {}


    def get_cmd_counter(self):
        return self.cmd_counter

    def get_cmd_list(self):
        for cmd in self._commands:
            instance = self._commands[cmd]
            yield [cmd, instance.description, instance.manual]


    def attach_completer_list(self, cmd_name, sub_list):

        class sub_cmd_completer:

            def __init__(self, sub_list):
                self.sub_list = sub_list

            def execute(self, text, line, start_index, end_index):
                return [subcommand for subcommand in self.sub_list if subcommand.startswith(text)]

        command = self._get_command(cmd_name)
        instance = sub_cmd_completer(sub_list)
        command._completer_function = instance.execute

