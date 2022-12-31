import secrets

from core.plugin_manager import *
from core.file_manager import *
from core.data_buffer import *
from core.config import *
from core.utils import *
from core.riposte_sf import *
from core.input_parser import *


class ReplPrinter:

	'''proxy class for riposte'''

	def __init__(self, riposte):
		self.repl = riposte

	def print(self, *args):
		self.repl.print(*args)

	def new_line(self):
		self.repl.print('')

	def success(self, *args):
		self.repl.success(*args)
		
	def error(self, *args):
		self.repl.error(*args)

	def status(self, *args):
		self.repl.status(*args)

	def debug(self, *args):
		self.repl.print('[yellow1]\[debug][/yellow1]', *args)

	def get_max_width(self):
		return self.repl.get_max_width()


class SF_CORE:

	def __init__(self, top_file):
		self.top_dir = FileTools.GetDirPath(top_file)
		self.init_riposte()
		self.repl = ReplPrinter(self.riposte)

		self.path = None
		self.db = None
		self.loaded_id = 0		

		self.fm = FileManager(self)
		self.fi = FileInterface(self.fm)
		self.inp = InputParser(self)

		self.update_prompt()
		self.__set_fm_hook()

	def start_cli(self):
		self.init_commands()
		self.riposte.run()

	def init_riposte(self):
		history = FileTools.MakePath(SF_HIST_NAME, self.top_dir)
		autoconf = FileTools.MakePath(SF_AUTO_NAME, self.top_dir)
		banner = None if SF_SKIP_BANNER else SF_BANNER

		self.prompt = SF_PROMPT
		self.riposte = RiposteSF(self.prompt, banner, SF_CLI_VER, history, SF_HIST_LEN, autoconf, SF_CLS_AFTER, SF_DOUBLE_MARGIN)

	def update_prompt(self):
		cmd_id = self.fi.get_last_cmd_id()
		self.riposte.set_prompt(f'{self.prompt}({self.loaded_id}#{cmd_id}): ')

	def __set_fm_hook(self):
		self.old_func = self.fm._update_cmd_id
		self.fm._update_cmd_id = self.__fm_hook

	def __fm_hook(self):
		retval = self.old_func()
		self.update_prompt()
		return retval

	def init_commands(self):
		self.riposte.free_commands()

		self.pm = PluginManager(self)

		# init without loaded file
		self.riposte.add_command('quit', 'exit from SF2', self.cmd_exit)
		self.riposte.add_command('cls', 'screen cleanup', self.cmd_cls)
		self.riposte.add_command('load', 'open a file for work', self.cmd_load_file, self.cmd_load_file.__doc__)

	def set_spec_var(self, name, value):
		# imported by plugins
		self.riposte.vars.set(f'${name}', value)
		self.repl.success(f'${name}')

	def erase_spec_var(self):
		self.riposte.vars.del_by_prefix('$')

	def init_spec_var(self):
		# delete old special vars
		self.erase_spec_var()
		# init basic variables
		self.set_spec_var('size', self.db.len())
		self.set_spec_var('all', f'0+{self.db.len()}')
		self.set_spec_var('path', self.path)

	def _validate_file(self, path, force_flag):

		if not FileTools.IsFile(path):
			raise ValueError(F'file not found! {path}')
	
		in_size = FileTools.GetSize(path)

		if in_size == 0:
			raise ValueError('file is empty')

		if in_size > MAX_INPUT_FILE_SIZE:
			if not force_flag:
				raise ValueError('file is too big, change config or use -f key')


	def cmd_load_file(self, path:str, *args):

		'''
		DESCRIPTION

		        Opening a file for work through a path or number

		EXAMPLES

		        load prog_name
		                for paths without spaces

		        load "/path/soft/ab cd"
		                and with it

		        load 123
		                opening the output file by file_id
		'''

		if args:

			no_space = 'load C:\\Program Files\\test.exe\n\n\t\t->\n\nload "C:\\Program Files\\test.exe"'
			self.repl.print(no_space)
			return

		try:

			if path.isnumeric():
				idx, path, dt = self.fm.load_by_index(int(path))
			else:
				force_flag = 'f' in self.flags

				path = remove_quotes(path)

				self._validate_file(path, force_flag)

				idx, path, dt = self.fm.load_by_path(path)

			self.path = path
			self.db = DataBuffer(dt)
			self.loaded_id = idx
			self.init_commands()

			# show current file index in prompt
			self.update_prompt()
			
			self.repl.status("File parsed")

			# new file -> new variables
			self.init_spec_var()

		except ValueError as err:

			self.repl.error(err)
			self.repl.status("Can't load this file, try another one")

			self.path = None
			self.db = None
			self.loaded_id = 0
			self.init_commands()
			self.erase_spec_var()
			self.update_prompt()

	def cmd_exit(self):
		phrases = [
			'Have a nice day',
			'Make Malware great again',
			'From Russia with love',
			]

		if not SF_SKIP_GOODBYE:
			self.repl.success(secrets.choice(phrases))
			if SF_DOUBLE_MARGIN:
				self.repl.new_line()

		sys.exit()

	def cmd_cls(self):
		os.system('cls' if os.name=='nt' else 'clear')

