from core.plugin_aux import *
from core.utils import *


class COMMAND_DIV(COMMANDS_BASE):

	'''
	DESCRIPTION

	        Divide custom range by N parts and replace it one by one

	EXAMPLES

	        div
	                divide whole file by 10 pieces

	        div -n 3
	                same, but divide by 3

	        div 0x1024+3000 -n 5
	                divide custom range by 5

	        div -i
	                inverted mode
	                replace all but one at once 

	        div p30
	                use patch list from file #30 as input range 

	        div i30
	                use inversed p30 

	        div 0+100 300+200
	                divide any range list  
	'''

	def __init__(self):
		self.name = 'div'
		self.desc = 'cleaning; division into N parts'
		self.category = 'cleaning'


	def div_normal_list(self):
		
		for sub_range in self.offsets:

			new_data = self.db.copy()

			for offset, size in sub_range:
				new_data.replace_standard(offset, size)

			self.fi.new_file(new_data, 'DIV')

	def div_inversed_list(self):

		full_range = [y for x in self.offsets for y in x]

		for sub_range in self.offsets:

			new_data = self.db.copy()

			for sub_item in RangeTools.substract_list(full_range, sub_range):
				new_data.replace_standard(sub_item.offset, sub_item.size)

			self.fi.new_file(new_data, 'DIV_I')


	def div_range_list(self, in_range_list, num):

		mapper = RangeMapper(in_range_list)

		self.virt_offsets = RangeTools.divide_range(0, mapper.get_size(), num)

		self.offsets = RangeList()

		for item in self.virt_offsets:
			self.offsets.append(mapper.map_range(item))

		if self.get_flag('i', True):
			self.div_normal_list()
		else:
			self.div_inversed_list()	


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


	def execute(self, *in_list: str):

		in_list = in_list or [self.get_default_range_str()]

		num = self.get_flag_int('n', 10)

		range_list = self.get_range_list(in_list)
		
		self.div_range_list(range_list, num)

		