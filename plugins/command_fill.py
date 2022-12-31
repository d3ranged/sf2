from core.plugin_aux import *
from core.utils import *


class COMMAND_FILL(COMMANDS_BASE):

	'''
	DESCRIPTION

	        Replace data in specific ranges

	EXAMPLES

	        fill
	                no args, write a copy of current file

	        fill 0+100
	                replace first 100 bytes

	        fill 0+10 300+10 400-500
	                we can use as many ranges as we want
	'''

	def __init__(self):
		self.name = 'fill'
		self.desc = 'cleaning; replacement by list'
		self.no_flags = False
		self.category = 'clean'


	def get_range_list(self, in_list):
		range_list = list()

		for item in in_list:

			in_range = self.inp.parse_range(item)

			if isinstance(in_range, RangeList):
				range_list += in_range

			if isinstance(in_range, Range):
				range_list.append(in_range)

			if in_range is None:
				raise ValueError(f'invalid arg - {item}')

		optimized = RangeTools.concat_list(range_list)
		self.repl.status(f'list: {optimized}')
		return optimized


	def execute(self, *range_str):

		range_list = self.get_range_list(range_str)

		new_data = self.db.copy()

		for offset, size in range_list:
			new_data.replace_standard(offset, size)

		self.fi.new_file(new_data, 'FILL')

