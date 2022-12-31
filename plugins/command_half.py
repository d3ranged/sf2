from core.plugin_aux import *
from core.utils import *


class COMMAND_HALF(COMMANDS_BASE):


	'''
	DESCRIPTION

	        Divide the range in half any number of times

	EXAMPLES

	        half
	                by default, divide whole file twice by 6 files 

	        half 0+1024 -n 3
	                divide custom range three times by 14 files

	        half p30
	                use patch list from file #30 as input range 

	        half i30
	                use inversed p30 

	        half 0+100 300+200
	                divide any range list  
	'''

	def __init__(self):
		self.name = 'half'
		self.desc = 'cleaning; recursive division in half'
		self.category = 'clean'


	def replace_virt(self, data, offset, size):
		mod_list = self.mapper.map_range(Range(offset, size))

		for offset, size in mod_list:
			data.replace_standard(offset, size)


	def halfing(self, data, offset, size, prefix = ''):

		if len(prefix) == self.max_deep:
			return

		size_r = size // 2
		size_l = size - size_r

		offset_l = offset
		offset_r = size_l + offset

		if size_l:
			new_data = data.copy()
			self.replace_virt(new_data, offset_l, size_l)
			new_name = prefix + 'l'
			self.fi.new_file(new_data, 'half_' + new_name)

			self.halfing(new_data, offset_r, size_r, new_name)

		if size_r:
			new_data = data.copy()
			self.replace_virt(new_data, offset_r, size_r)
			new_name = prefix + 'r'
			self.fi.new_file(new_data, 'half_' + new_name)

			self.halfing(new_data, offset_l, size_l, new_name)


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


	def execute(self, *in_list):

		in_list = in_list or [self.get_default_range_str()]

		self.max_deep = self.get_flag_int('n', 2)
		if self.max_deep > 10:
			raise ValueError('Max halfing depth is 10')

		range_list = self.get_range_list(in_list)
		self.mapper = RangeMapper(range_list)

		self.halfing(self.db, 0, self.mapper.get_size())
