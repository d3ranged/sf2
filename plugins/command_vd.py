from core.plugin_aux import *
from core.utils import *
from core.config import *

import hashlib


class COMMAND_VD(COMMANDS_BASE):

	'''
	DESCRIPTION

	        Visualization of file changes

	OPTIONS

	        vd
	                show graph of files from the last command

	        vd 3
	                build graph from the command #3

		    vd -r 0+1024
	                use custom range, instead of guessed
	'''


	def __init__(self):
		self.name = 'vd'
		self.desc = 'visualization of file changes'


	def is_file_exist(self, file_id):
		full_path = self.fi.get_file_info(file_id, 'full_path')
		return FileTools.IsFile(full_path)


	def get_file_size(self, file_id):
		return self.fi.get_file_info(file_id, 'file_size')


	def get_cmd_id(self, cmd_id):
		cmd_id = cmd_id or self.get_last_cmd_id()
		return self.vaidate_cmd_id(cmd_id)


	def guess_range(self, cmd_id, file_size):
		work_range = self.fi.get_cmd_work_range(cmd_id)
		return work_range or Range(0, file_size)
			

	def get_intersection_percent(self, patch, item):
		intersection = RangeTools.intersect(patch, item)
		if not intersection: return 0

		return int(intersection.size / item.size * 100)


	def bar_by_perfent(self, intersection_percent):
		bar = '#'

		if intersection_percent == 0:
			bar = SF_BAR_FULL

		if intersection_percent > 0:
			bar = SF_BAR_PART

		if intersection_percent >= 99:
			bar = SF_BAR_EMPTY

		return bar


	def render_bar(self, file_id):
		bar_line = ''
		patch_list = self.fi.get_file_info(file_id, 'patch_list')

		for item in self.divided:
			intersected = 0
			
			for patch in patch_list:

				intersected += self.get_intersection_percent(patch, item)

			bar_line += self.bar_by_perfent(intersected)

		return bar_line


	def built_line(self, file_id, max_id_len):
		bar_line = self.render_bar(file_id)
		del_mark = ' ' if self.is_file_exist(file_id) else '[red bold]*[/]'
		self.repl.print(f'\n{del_mark}{file_id:0>{max_id_len}} {bar_line} ')


	def max_id_len(self, file_list):
		max_file_id = max(file_list)
		return len(str(max_file_id))


	def built_lines(self, file_list):
		max_id_len = self.max_id_len(file_list)
		max_line_len = self.repl.get_max_width()
		bar_count = max_line_len - (max_id_len + 3)

		self.divided = RangeTools.divide_range(self.in_offset, self.in_size, bar_count)

		for file_id in file_list:
			self.built_line(file_id, max_id_len)


	def execute(self, cmd_id_in: int = None):

		cmd_id = self.get_cmd_id(cmd_id_in)
		parent_id =	self.fi.get_cmd_info(cmd_id, 'loaded_file_id')
		file_size = self.get_file_size(parent_id)
		file_list = self.get_file_list(cmd_id)

		if cmd_id_in is None and parent_id != self.loaded_id:
			raise ValueError('Output files not found')

		guessed_range = self.guess_range(cmd_id, file_size)
		in_range = self.get_flag_one('r', None)
		in_range = in_range or str(guessed_range)

		self.parse_input_range(in_range, file_size)

		self.built_lines(file_list)

