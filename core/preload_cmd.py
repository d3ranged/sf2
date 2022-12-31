from thirdparty.rich.table import Table, box

from core.plugin_aux import *
from core.data_buffer import *
from core.utils import *
from core.config import *

import subprocess
import importlib
import inspect
import hashlib
import sys


class COMMAND_ECHO(COMMANDS_BASE):

	req_attr = ['repl', 'inp']
	no_flags = True

	def __init__(self):
		self.name = 'echo'
		self.desc = 'display text and variables'

	def replace_special(self, *sub_args):
		return [self.inp.parse_special_str(item) or item for item in sub_args]

	def execute(self, *sub_args):

		sub_args = self.replace_special(*sub_args)

		self.repl.print(' '.join(sub_args))



class COMMAND_HELP(COMMANDS_BASE):
	'''no one can help you'''

	req_attr = ['repl', 'riposte']

	def __init__(self):
		self.name = 'help'
		self.desc = 'this help message'

	def show_all(self):

		table = Table(box=None, show_header=False)

		table.add_column("name", justify="left", style="bold", no_wrap=True)
		table.add_column("description", justify="left", style="")

		cmd_list = sorted(self.riposte.get_cmd_list(), key = lambda x: x[0])

		for name, desc, man in cmd_list:
			table.add_row(name, desc)

		self.repl.print(table)

	def get_cmd_man(self, cmd_name):

		for name, desc, man in self.riposte.get_cmd_list():
			if name == cmd_name:
				return man

		return False

	def show_man(self, cmd_name):

		cmd_man = self.get_cmd_man(cmd_name)

		if cmd_man is False:
			self.repl.error(f'unknown command - {cmd_name}')
			return

		if cmd_man is None:
			self.repl.status('manual not found')
			return

		man_clean = inspect.cleandoc(cmd_man)
		self.repl.print(man_clean)
			
	def execute(self, *cmd_name):

		if not cmd_name:
			self.show_all()
		else:
			cmd_name = ' '.join(cmd_name)
			self.show_man(cmd_name)


class COMMAND_FILE_INFO(COMMANDS_BASE):

	'''
	DESCRIPTION

	        Detailed information about the selected file

	OPTIONS

	        info
	                size and path of the loaded file

	        info 12
	                same about any file by its number

	        info -h
	                hashes (MD5, SHA1, SHA256)
	'''

	req_attr = ['repl', 'fi', 'loaded_id']
	
	def __init__(self):
		self.name = 'info'
		self.desc = 'path, size and hash of the file'

	def read_data(self, file_id):
		# can't use self.db.get_bytes()
		self.dt = self.fi.read_file(file_id)

	def show_hashes(self):
		hash_md5 = hashlib.md5(self.dt).hexdigest()
		self.repl.status(f"MD5: {hash_md5}")
		hash_sha1 = hashlib.sha1(self.dt).hexdigest()
		self.repl.status(f"SHA1: {hash_sha1}")
		hash_sha2 = hashlib.sha256(self.dt).hexdigest()
		self.repl.status(f"SHA256: {hash_sha2}")

	def show_parent_info(self, file_id):

		is_output = self.fi.get_file_info(file_id, 'type') == 'output'

		self.repl.new_line()
		parent_path = self.fi.get_file_info(file_id, 'full_path')

		if is_output:
			cmd_id = self.fi.get_file_info(file_id, 'cmd_id')
			file_str = f'({file_id}) Command: #{cmd_id}'

		else:
			file_str = f'({file_id}) {parent_path}'

		self.repl.status(f"File: {file_str}")

		if is_output:

			patch_list = self.fi.get_file_info(file_id, 'patch_list')
			self.repl.status(f"Patch: {patch_list}")

			parent_id = self.fi.get_file_info(file_id, 'parent_id')
			self.show_parent_info(parent_id)

	def show_basic_info(self, file_id):

		file_size = len(self.dt)
		self.repl.status(f"Size: {format_bytes(file_size)} ({file_size})")

	def execute(self, file_id : int = None):

		if file_id == 0:
			raise ValueError('Invalid file_id')

		if file_id is None:
			file_id = self.loaded_id

		if file_id == 0:
			raise ValueError('No file loaded')

		if not self.fi.is_valid_file_id(file_id):
			raise ValueError('Invalid file_id')		

		self.read_data(file_id)

		if self.is_flag('h'):
			self.show_hashes()
			return

		self.show_basic_info(file_id)

		self.show_parent_info(file_id)


class COMMAND_ALIAS(COMMANDS_BASE):

	'''
	DESCRIPTION

	        Create, delete or show aliases

	EXAMPLES

	        alias
	                show alias table

	        alias abc
	                delete alias with name "abc"

	        alias abc 'cmd args -flag1 "substring" -flag2'
	                create alias named "abc"

	        alias abc 'echo $all ; echo %1'
	                we can separate commands with semicolon
	                and use any variables as arguments
	'''

	req_attr = ['repl', 'riposte']

	def __init__(self):
		self.name = 'alias'
		self.desc = 'replace any text to short command'  

	def show_all(self):

		aliases = self.riposte.aliases.get_data()

		if aliases:
			table = Table(show_lines = True, show_header=False, expand=True)
			table.add_column("name", justify='center', overflow=None, no_wrap=True)
			table.add_column("value", justify='center', overflow='ellipsis', no_wrap=False)

			for name, value in aliases.items():
				table.add_row(name, value)

			self.repl.print(table)
		else:
			self.repl.status(f'nothing to see here')

	def set_or_del(self, name: str, arg_line: str):

		if arg_line:

			new_value = remove_quotes(arg_line)

			if new_value:
				self.riposte.aliases.set(name, new_value)
				self.repl.success(f'alias: {name}')
			else:
				raise ValueError('empty arguments string')
		else:
			if self.riposte.aliases.delete(name):
				self.repl.status(f'alias deleted: {name}')
			else:
				self.repl.status(f'unknown alias')

	def execute(self, name: str = '', arg_line: str = ''):
		
		if name:
			self.set_or_del(name, arg_line)
		else:
			self.show_all()


class COMMAND_VAR(COMMANDS_BASE):

	'''
	DESCRIPTION

	        Create, delete or show variables

	EXAMPLES

	        var
	                show variables table

	        var 123
	                delete user variable %123

	        var 123 'aa bb cc'
	                create user variable %123 = aa bb cc
	'''

	req_attr = ['repl', 'riposte']
	no_vars = False

	def __init__(self):
		self.name = 'var'
		self.desc = 'shell variables management'

	def show_var(self):

		variables = self.riposte.vars.get_data()

		if variables:

			table = Table(show_lines = True, show_header=False, expand=True)
			table.add_column("name", justify='center', overflow=None, no_wrap=True)
			table.add_column("value", justify='center', overflow='ellipsis', no_wrap=False)

			for name, value in variables.items():

				table.add_row(name, value)

			self.repl.print(table)

		else:
			self.repl.status(f'nothing to see here')

	def set_or_del(self, var_name: int, arg_line: str):

		if var_name < 0:
			raise ValueError('invalid variable id')

		name = f'%{var_name}'

		if arg_line:

			new_value = remove_quotes(arg_line)

			if new_value:
				self.riposte.vars.set(name, new_value)
				self.repl.status(f'var: {name} = {new_value}')
			else:
				raise ValueError('empty arguments string')
		else:
			if self.riposte.vars.delete(name):
				self.repl.status(f'variable deleted: {name}')
			else:
				self.repl.status(f'unknown variable {name}')

	def execute(self, var_name: int = None, new_value:str = None):
		
		if var_name is None:
			self.show_var()
		else:
			self.set_or_del(var_name, new_value)


class COMMAND_CMD_LIST(COMMANDS_BASE):

	'''
	DESCRIPTION

	        Shows file commands and the number of files created

	EXAMPLES

	        cmd
	                no options here
	'''

	req_attr = ['repl', 'fi']

	def __init__(self):
		self.name = 'cmd'
		self.desc = 'history of file commands'


	def count_files(self, cmd_id):

		self.all = 0
		self.clean = 0
		self.deleted = 0

		for file_id in self.fi.get_file_list(cmd_id):

			if self.fi.is_file_exist(file_id):
				self.clean += 1
			else:
				self.deleted += 1

			self.all += 1


	def execute(self):

		cmd_list = self.fi.get_cmd_list()

		if not cmd_list:
			self.repl.status('output files not found')
			return

		table = Table(box=box.ROUNDED, show_lines=True, show_header=True, expand=False)

		#table = Table(box=box.ROUNDED, show_lines=False,
		#	show_header=True, expand=False, title=title,
		#	title_style='')

		table.add_column("id", justify="center")
		table.add_column("not", justify="center")
		table.add_column("del", justify="center")
		table.add_column("command", justify="center")
		table.add_column("file_id", justify="center")

		for cmd_id in cmd_list:

			self.count_files(cmd_id)

			cmd_line = self.fi.get_cmd_info(cmd_id, 'cmd_line')
			cmd_id_str = f'{cmd_id}' 

			parent_id =	self.fi.get_cmd_info(cmd_id, 'loaded_file_id')
			parent_str = f'{parent_id}'

			table.add_row(cmd_id_str, str(self.clean), str(self.deleted), cmd_line, parent_str)

		self.repl.print(table)


class COMMAND_EVAL(COMMANDS_BASE):

	'''
	DESCRIPTION

	        Evaluate python expression              

	EXAMPLES

	        eval print(123)
	                code must be in the first argument

	        eval 'print("1 2 3")'
	                code with tabs requires quotation marks
	'''

	req_attr = ['repl']

	def __init__(self):
		self.name = 'eval'
		self.desc = 'python code evaluation'
		self.no_flags = True
		self.category = 'debug'

	def execute(self, arg_line: str):

		in_line = remove_quotes(arg_line)

		self.repl.print(f'expr: {in_line} ({len(in_line)})')

		try:
			result = eval(in_line)
			if result is not None:
				self.repl.print(result)

		except Exception as err:
			self.repl.status(err)


class COMMAND_RUN(COMMANDS_BASE):

	'''
	DESCRIPTION

	        Runs an external program and waits 600 seconds for it to be forcibly terminated

	EXAMPLES

	        run dir
	                program path is the first argument

	        run 'dir -s'
	                path with spaces requires quotation marks

	        run 'dir -s' -v
	                save $stdout and $stderr as var 

	        run 'echo 1' -s
	                show stdout and stderr 

	        run 'readelf -h {}' -f $path
	                format shell command like python string 

	        run 'echo {} {} {}' -s -f '1 2' 3 "4"
	            formating support quotation marks
	'''

	#        run 'echo {{}}' -s -f '1'
	#            double bracket allow to use run formating with aliases

	req_attr = ['repl', 'set_spec_var']

	def __init__(self):
		self.name = 'run'
		self.desc = 'run an external program'

	def add_vars(self):
		if not self.is_flag('v'): return
		self.set_spec_var('stdout', self.stdout)
		self.set_spec_var('stderr', self.stderr)

	def show_out(self):
		if not self.is_flag('s'): return
		if self.stdout: self.repl.print('\n' + self.stdout)
		if self.stderr: self.repl.print('\n' + self.stderr)

	def format_cmd(self, shell_str):
		if not self.is_flag('f'):
			return shell_str

		f_arg = [remove_quotes(x) for x in self.get_flag('f')]

		# replace special mark
		shell_str = shell_str.replace('{{', '{').replace('}}', '}')

		# check arg count
		need_args = get_format_arg_count(shell_str)
		if len(f_arg) != need_args:
			raise ValueError(f"invalid argument's count, need {need_args}, get {len(f_arg)}")

		try:
			out_str = shell_str.format(*f_arg)
		except IndexError:
			raise ValueError('not enough format arguments')

		return out_str

	def execute(self, shell_str: str):

		shell_str = remove_quotes(shell_str)
		shell_str = self.format_cmd(shell_str)
	
		self.repl.status(shell_str)

		try:

			out = subprocess.run(shell_str, shell = True, capture_output = True, timeout=600)
			
			self.repl.status(f'exit code: {out.returncode} ')
			self.stdout = out.stdout.decode('utf-8').strip()
			self.stderr = out.stderr.decode('utf-8').strip()

			self.add_vars()
			self.show_out()

		except Exception as err:
			self.repl.status(err)


class CMD_PATCHED(COMMANDS_BASE):

	'''
	DESCRIPTION

	        File list from the last file command

	EXAMPLES

	        p
	                output files by last command

	        p 123
	                output files by command #123
	'''

	req_attr = ['repl', 'fi', 'set_spec_var', 'loaded_id']

	def __init__(self):
		self.name = 'files'
		self.desc = 'output file history'

	def print_ranges(self, patch_list):
		return ' '.join([str(x) for x in patch_list])

	def execute(self, cmd_id: int = None):
		self.show_files(cmd_id)

	def build_del(self, file_id):
		is_exist = self.fi.is_file_exist(file_id)		
		return '[bold green]not[/]' if is_exist else '[bold red]del[/]'

	def get_patches(self, file_id):
		patch_list = self.fi.get_file_info(file_id, 'patch_list')

		if 'r' not in self.flags:
			patch_list = RangeTools.concat_list(patch_list)

		return str(patch_list)

	def get_comment(self, file_id):
		comment = self.fi.get_file_info(file_id, 'comment')
		return comment if comment else ''

	def get_cmd_id(self, cmd_id):
		cmd_id = cmd_id or self.get_last_cmd_id()
		return self.vaidate_cmd_id(cmd_id)

	def show_files(self, cmd_id_in):

		cmd_id = self.get_cmd_id(cmd_id_in)
		parent_id =	self.fi.get_cmd_info(cmd_id, 'loaded_file_id')

		if cmd_id_in is None and parent_id != self.loaded_id:
			raise ValueError('Output files not found')

		file_list = self.get_file_list(cmd_id)

		title = None
		table = Table(box=box.ROUNDED, show_lines=False,
			show_header=True, expand=False, title=title,
			title_style='')

		table.add_column("id", justify="center")
		table.add_column("del", justify="center")
		table.add_column("comment", justify="left")
		table.add_column("patches", justify="left")

		for file_id in file_list:

			patches = self.get_patches(file_id)
			comment = self.get_comment(file_id)
			deleted = self.build_del(file_id)
			
			table.add_row(str(file_id), deleted, comment, patches)

		self.repl.print(table)


