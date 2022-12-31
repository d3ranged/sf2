from thirdparty.rich.table import Table

from core.plugin_aux import *
from core.utils import *
from core.config import * 
import time


class COMMAND_PE_INFO(COMMANDS_BASE):

	def __init__(self):
		self.name = 'pe'
		self.desc = 'pe32 header parser'
		self.req_mods = ['pe']


	def get_pe_attr(self, *attr_list):

		attr = self.pe

		for item in attr_list:
			attr = getattr(attr, item, None)
			if attr is None: return None

		return attr


	def execute(self):

		try:

			if 'f' in self.flags:
				self.show_full_info()
			else:
				self.show_sect_info()
				self.repl.new_line()
				self.show_dir_info()
				self.show_opt_info()
				#self.show_warnings()

				self.init_special_vars()

		except Exception as e:
			raise ValueError("Something went wrong =)")


	def get_size_percent(self, size):
		percent = 100 * size / self.db.len()
		return format_float(percent)


	def parse_sect_char(self, char):

		attr = {	
					'MEM_EXECUTE':0x20000000,
					'MEM_READ':0x40000000,
					'MEM_WRITE':0x80000000,
					'MEM_DISCARDABLE':0x02000000,

					'CNT_CODE':0x00000020,
					'CNT_INITIALIZED_DATA':0x00000040,
					'CNT_UNINITIALIZED_DATA':0x00000080,

					'KNOWN_FLAGS':0xE20000E0,
					'UNKNOWN_FLAGS':0x1DFFFF1F,
				}

		mem = ''
		if char & attr['MEM_READ']: mem += 'R'
		if char & attr['MEM_WRITE']: mem += 'W'
		if char & attr['MEM_EXECUTE']: mem += 'E'
		if char & attr['MEM_DISCARDABLE']: mem += 'D'

		# maybe add some flags later

		if char & attr['CNT_CODE']: mem += 'c'
		if char & attr['CNT_INITIALIZED_DATA']: mem += 'd'
		if char & attr['CNT_UNINITIALIZED_DATA']: mem += 'u'

		if char & attr['UNKNOWN_FLAGS']: mem += '?'

		return mem


	def show_sect_info(self):

		table = Table(box=None)
		table.add_column("(#)")
		table.add_column("PERCENT")
		table.add_column("ENTROPY")
		table.add_column("FLAGS")
		table.add_column("NAME")
		table.add_column("OFFSET")
		table.add_column("SIZE")

		for idx, sect in enumerate(self.pe.sections):
			if sect.SizeOfRawData < MAX_CALC_ENTROPY_SIZE:
				if sect.SizeOfRawData > 0:
						sect_data = self.db.read(sect.PointerToRawData, sect.SizeOfRawData)
						ent_data = ByteTools.entropy(sect_data)
				else:
					ent_data = 0
				ent = format_float(ent_data)
			else:
				ent = '????'

			sp = self.get_size_percent(sect.SizeOfRawData)
			name = sect.Name.decode('utf-8').replace('\x00', '')
			char = self.parse_sect_char(sect.Characteristics)

			table.add_row(f"({idx})", sp, ent, char, name, str(sect.PointerToRawData), str(sect.SizeOfRawData))

		# add overlay as last section
		overlay_offset = self.pe.get_overlay_data_start_offset()

		if overlay_offset:
			overlay_size = self.db.len() - overlay_offset
			idx = len(self.pe.sections)
			sp = self.get_size_percent(overlay_size)

			if overlay_size < MAX_CALC_ENTROPY_SIZE:
				sect_data = self.db.read(overlay_offset, overlay_size)
				ent_data = ByteTools.entropy(sect_data)
				ent = format_float(ent_data)
			else:
				ent = '????'

			table.add_row(f"({idx})", sp, ent, '---', 'overlay', str(overlay_offset), str(overlay_size))

		self.repl.print(table)


	def show_dir_info(self):

		table = Table(box=None)
		table.add_column("(#)")
		table.add_column("DIRECTORY")
		table.add_column("OFFSET")
		table.add_column("SIZE")
		
		for idx, entry in enumerate(self.pe.OPTIONAL_HEADER.DATA_DIRECTORY):
			if entry.Size == 0: continue

			offset = self.pe.get_offset_from_rva(entry.VirtualAddress)
			name = entry.name[22:].lower()

			table.add_row(f"({idx})", name, str(offset), str(entry.Size))

		self.repl.print(table)


	def show_opt_info(self):
		fh = self.pe.FILE_HEADER
		opt = self.pe.OPTIONAL_HEADER
	
		table = Table(box=None, show_header=False)
		table.add_column("name", style='bold')
		table.add_column("value")

		ep_rva = opt.AddressOfEntryPoint
		ep_offset = self.pe.get_offset_from_rva(ep_rva)
		
		imp_api_count = 0
		imp_lib_count = 0

		if hasattr(self.pe, 'DIRECTORY_ENTRY_IMPORT'):

			imp_lib_count = len(self.pe.DIRECTORY_ENTRY_IMPORT)

			for item in self.pe.DIRECTORY_ENTRY_IMPORT:
				imp_api_count += len(item.imports)

		try:
			value = fh.TimeDateStamp
			time_date = time.strftime("%d.%m.%Y", time.gmtime(value))
		except Exception:
			time_date = 'invalid'

		table.add_row('ImageBase', hex(opt.ImageBase))
		table.add_row('Ep Offset', str(ep_offset))
		table.add_row('Import Libs', str(imp_lib_count))
		table.add_row('Import Apis', str(imp_api_count))
		table.add_row('TimeDate', str(time_date))

		self.repl.new_line()
		self.repl.print(table)


	def show_warnings(self):
		if not self.pe.get_warnings(): return

		self.repl.new_line()
		self.repl.status('Warnings:')

		for item in self.pe.get_warnings():
			self.repl.print(item)


	def show_full_info(self):
		self.repl.print(self.pe)


	def init_special_vars(self):

		self.repl.new_line()

		for idx, sect in enumerate(self.pe.sections):
			offset, size = sect.PointerToRawData, sect.SizeOfRawData
			self.set_spec_var(f'sect{idx}', f'{offset}+{size}')

		# header & overlay
		overlay_offset = self.pe.get_overlay_data_start_offset()
		if overlay_offset:
			overlay_size = self.db.len() - overlay_offset
			self.set_spec_var(f'over', f'{overlay_offset}+{overlay_size}')

		# file alignment - 0x400
		headers_size = self.pe.OPTIONAL_HEADER.SizeOfHeaders
		self.set_spec_var(f'head', f'{0}+{headers_size}')

		body_size =  self.db.len() - headers_size
		self.set_spec_var(f'body', f'{headers_size}+{body_size}')		
