from core.plugin_aux import *
from core.utils import *
from thirdparty.pefile import pefile


class FakeStructure:

	def get_next_name(self, field_name):
		prev_our = False

		for item in self.__field_offsets__:
			
			if item == field_name:
				prev_our = True
			else:
				if prev_our: return item

	def get_field_size(self, field_name):
		if field_name not in self.__field_offsets__: return None

		next_name = self.get_next_name(field_name)

		if next_name:
			next_offset = self.get_field_relative_offset(next_name)
		else:
			next_offset = self.__format_length__

		cur_offset = self.get_field_relative_offset(field_name)

		return next_offset - cur_offset

	def get_data_from_byte(self, i):
		return bytes([i])

	def get_field_info(self, header, name):
		offset = header.get_field_absolute_offset(name)
		size = header.get_field_size(name)
		return offset, size

	def rva_to_offset(self, input_int):
		try:
			# can raise exception if found invalid section
			return self.get_offset_from_rva(input_int)
		except:
			return None

	def offset_to_rva(self, input_int):
		return self.get_rva_from_offset(input_int)

	def va_to_rva(self, input_int):
		return input_int - self.min_va

	def rva_to_va(self, input_int):
		return input_int + self.min_va

	def pre_calc_max_sizes(self):
		max_offset = len(self.__data__)
		overlay_offset = self.get_overlay_data_start_offset()
		if overlay_offset: max_offset = overlay_offset
		self.max_offset = max_offset
		self.max_rva = self.OPTIONAL_HEADER.SizeOfImage
		self.min_va = self.OPTIONAL_HEADER.ImageBase
		self.max_va = self.min_va + self.max_rva

	def is_valid_offset(self, offset):
		return (offset >= 0) and (offset < self.max_offset)

	def is_valid_rva(self, rva):
		return (rva >= 0) and (rva < self.max_rva)

	def is_valid_va(self, va):
		return (va >= self.min_va) and (va < self.max_va)
		


def hotpatch_pefile():
	# overload original or add something new

	pefile.Structure.get_next_name = FakeStructure.get_next_name
	pefile.Structure.get_field_size = FakeStructure.get_field_size
	pefile.PE.get_data_from_byte = FakeStructure.get_data_from_byte
	pefile.PE.get_field_info = FakeStructure.get_field_info

	pefile.PE.rva_to_offset = FakeStructure.rva_to_offset
	pefile.PE.offset_to_rva = FakeStructure.offset_to_rva
	pefile.PE.va_to_rva = FakeStructure.va_to_rva
	pefile.PE.rva_to_va = FakeStructure.rva_to_va

	pefile.PE.pre_calc_max_sizes = FakeStructure.pre_calc_max_sizes
	pefile.PE.is_valid_offset = FakeStructure.is_valid_offset
	pefile.PE.is_valid_rva = FakeStructure.is_valid_rva
	pefile.PE.is_valid_va = FakeStructure.is_valid_va

	
class MODULE_PE32(MODULES_BASE):

	name = 'pe'

	def is_my_type(self):
		file_data = self.db.get_data()
		return file_data[0:4] == b'MZ\x90\x00'

	def load(self):
		try:
			pe = pefile.PE(data=self.db.get_bytes(), fast_load = True)
			pe.full_load()
			hotpatch_pefile()
			pe.pre_calc_max_sizes()

			self.repl.success('PE detected')

			return pe
		except pefile.PEFormatError:
			raise ValueError("Invalid PE file")


class MODULE_PEFILE(MODULES_BASE):

	name = 'pefile'

	def is_my_type(self):
		file_data = self.db.get_data()
		return file_data[0:4] == b'MZ\x90\x00'

	def load(self):
		# just a link to a module
		return pefile