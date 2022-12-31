import importlib
from core.utils import *


class MODULES_BASE():

	name = 'name'
	req_mods = []
	req_attr = ['path', 'repl', 'db']
	

	def is_my_type(self):
		# return True
		raise NotImplementedError("You have to define your own 'is_my_type' method.")

	def load(self):
		# return module_instance
		raise NotImplementedError("You have to define your own 'load' method.")

	def can_run(self):
		# check import if any
		return True

	def __repr__(self):
		return f'mod({self.name})'

	def manual_import(self, name):
		try:
			return importlib.import_module(name)
		except ImportError:
			return None


class COMMANDS_MISC:

	def get_default_range(self):
		return Range(0, self.db.len())

	def get_default_range_str(self):
		return str(self.get_default_range())
		
	def parse_input_range(self, in_range, max_len = None):
		max_len = max_len or self.db.len()
		self.in_offset, self.in_size = RangeTools.parse_str(in_range, max_len)
		self.in_offset_2 = self.in_offset + self.in_size
		self.repl.status(f'offset: {self.in_offset} size: {self.in_size}')

	def parse_input(self, in_str):
		in_range = self.inp.parse_range(in_str)

		if in_range is None:
			raise ValueError('invalid input range')

		self.in_offset, self.in_size = in_range
		self.in_offset_2 = self.in_offset + self.in_size
		self.repl.status(f'offset: {self.in_offset} size: {self.in_size}')

	def parse_input_range_list(self, range_list, max_len = None):
		max_len = max_len or self.db.len()
		self.in_list = [RangeTools.parse_str(item, max_len) for item in range_list]

	def parse_input_line(self, in_args):
		self.in_line = ' '.join([str(exp) for exp in in_args]) 

	def get_flag(self, name, if_not = None):
		return list(self.flags[name]) if (name in self.flags) else if_not

	def get_flag_one(self, name, if_not = None):
		
		data = self.get_flag(name, if_not)
		if data == if_not: return if_not

		if len(data) == 0:
			return if_not

		if len(data) != 1:
			raise ValueError('too many flag arguments')

		return data[0]

	def get_flag_int(self, name, if_not = None):

		data = self.get_flag_one(name, if_not)
		if data == if_not: return if_not
		return int(data)

	def is_flag(self, name):
		return name in self.flags

	def get_last_cmd_id(self):
		last_cmd_id = self.fi.get_last_cmd_id()

		if last_cmd_id == 0:
			raise ValueError('output files not found')

		return last_cmd_id 

	def vaidate_cmd_id(self, cmd_id):
		last_cmd_id = self.get_last_cmd_id()

		if (cmd_id <= 0) or cmd_id > last_cmd_id:
			raise ValueError('invalid cmd_id')

		return cmd_id

	def get_file_list(self, cmd_id = None):
		cmd_id = cmd_id or self.get_last_cmd_id()
		self.vaidate_cmd_id(cmd_id)

		file_list = self.fi.get_file_list(cmd_id)

		if not file_list:
			raise ValueError('empty file_list')

		return file_list


class COMMANDS_BASE(COMMANDS_MISC):
	'''
	full text manual
	'''

	req_mods = []
	req_attr = ['path', 'repl', 'db', 'fi', 'set_spec_var', 'inp', 'loaded_id']
	flags = []

	no_flags = False
	no_vars = False

	def __init__(self):
		self.name = 'command name'
		self.desc = 'short command description'

	def __repr__(self):
		return f'cmd({self.name}, {self.req_attr}, {self.req_mods})'

	def execute(self, arg_list):
		raise NotImplementedError("You have to define your own 'execute' method.")

