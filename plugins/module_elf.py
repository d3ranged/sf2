import io

from core.plugin_aux import *
from core.utils import *
from thirdparty.elftools.elf.elffile import ELFFile


class MODULE_ELF(MODULES_BASE):

	name = 'elf'

	def is_my_type(self):
		file_data = self.db.get_data()
		return file_data[0:4] == b'\x7fELF'

	def load(self):
		try:

			stream = io.BytesIO(self.db.get_bytes())

			readelf = ELFFile(stream)

			self.repl.success('ELF detected')

			return readelf

		except Exception as e:
			raise ValueError("Invalid ELF file")




