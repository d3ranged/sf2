from thirdparty.rich.table import Table

from core.plugin_aux import *
from core.utils import *
from core.config import * 


class COMMAND_ELF_INFO(COMMANDS_BASE):

	def __init__(self):
		self.name = 'elf'
		self.desc = 'elf header parser'
		self.req_mods = ['elf']

	def execute(self):
		try:
			self.head = self.elf.header
			self.print_header()
			self.print_segments()
			self.print_sections()
			self.add_special()
		except Exception as e:
			raise ValueError("Something went wrong =)")

	def print_header(self):

		table = Table(box=None, show_header=False)
		table.add_column("name", style='bold')
		table.add_column("value")

		table.add_row('Machine', self.head.e_machine)
		table.add_row('Class', self.head.e_ident['EI_CLASS'])
		table.add_row('Ep Addr', hex(self.head.e_entry))

		self.repl.print(table)

	def print_segments(self):

		table = Table(box=None, show_header=True)
		table.add_column("offset")
		table.add_column("size")
		table.add_column("type")

		for seg in self.elf.iter_segments():
			table.add_row(str(seg['p_offset']), str(seg['p_filesz']), seg['p_type'])

		self.repl.new_line()
		self.repl.print(table)

	def print_sections(self):			

		table = Table(box=None, show_header=True)
		table.add_column("name")
		table.add_column("offset")
		table.add_column("size")
		table.add_column("type")

		for sec in self.elf.iter_sections():
			if sec.is_null(): continue
			table.add_row(sec.name, str(sec['sh_offset']), str(sec['sh_size']), sec['sh_type'])

		self.repl.new_line()
		self.repl.print(table)

	def add_special(self):
		self.repl.new_line()

		header = Range(0, self.head.e_ehsize)
		head_prog = Range(self.head.e_phoff, self.head.e_phentsize * self.head.e_phnum)
		head_sect = Range(self.head.e_shoff, self.head.e_shentsize * self.head.e_shnum)
		head = [header, head_prog, head_sect]

		full = self.get_default_range()
		body = RangeTools.substract_list2(full, head)

		self.set_spec_var(f'head', f'{header} {head_prog} {head_sect}')
		self.set_spec_var(f'body', f'{body}')

		
