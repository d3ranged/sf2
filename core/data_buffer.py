import unittest

from core.utils import *


class standard_replacement:

	def get_replacement(self, offset, size, new_data = None):
		# if you insist
		if new_data: return new_data
		# standard replacement
		return b'\x00' * size

	def __repr__(self):
		return 'fill zero'


class DataBuffer:

	def __init__(self, data):
		self.data = bytearray(data)
		self.patches = list()
		self.set_replacement()

	def add_patch(self, offset, size):
		self.patches.append(Range(offset, size))

	def get_patches(self):
		return self.patches

	def len(self):
		return len(self.get_data())

	def _replace(self, offset, new_data):
		assert new_data
		assert len(new_data)
		assert offset >= 0
		assert (len(new_data) + offset) <= self.len()
		size = len(new_data)
		self.data[offset:offset+size] = new_data
		self.add_patch(offset, size)

	def get_replacement(self, offset, size, new_data = None):
		pass

	@staticmethod
	def set_replacement(new_func = None):
		if new_func:
			DataBuffer.get_replacement = new_func
		else:
			method = standard_replacement().get_replacement
			DataBuffer.get_replacement = method

	def replace_standard(self, offset, size):
		data = self.get_replacement(offset, size)
		self._replace(offset, data)

	def replace_custom(self, offset, data):
		data = self.get_replacement(offset, len(data), data)
		self._replace(offset, data)

	def read(self, offset, size):
		assert offset >= 0
		assert size > 0
		assert (size + offset) <= self.len()
		return self.data[offset:offset+size]

	def get_data(self):
		return self.data

	def get_bytes(self):
		return bytes(self.get_data())

	def __repr__(self):
		return f'DataBuffer({self.len()})'

	def copy(self):
		instance = DataBuffer(self.get_data())
		instance.patches = list() + self.patches
		return instance

	def replace_from(self, buf, offset, size):
		orig_data = buf.read(offset, size)
		self.replace_custom(offset, orig_data)


############################################################
# UNIT TEST
############################################################


class Test_DataBuffer(unittest.TestCase):

	def test_replace(self):

		buf = DataBuffer(b'0123456789')
		buf.replace_custom(1, b'---')
		self.assertEqual(buf.get_bytes(), b'0---456789')

		with self.assertRaises(AssertionError):
			# out of boundaries
			buf = DataBuffer(b'123')
			buf.replace_custom(3, b'---')

	def test_db_init(self):
		db1 = DataBuffer(ByteTools.str2bytes('123'))
		db2 = DataBuffer(b'123') 
		db3 = DataBuffer(bytearray(b'123'))
		self.assertEqual(db1.get_data(), db2.get_data())
		self.assertEqual(db2.get_data(), db3.get_data())

	def test_db_replace(self):
		db = DataBuffer(b'1234567890')
		db.replace_custom(9, b'!')
		self.assertEqual(db.get_bytes(), b'123456789!')

		db.replace_custom(0, b'0123456789')
		self.assertEqual(db.get_bytes(), b'0123456789')

		# over & under flow
		with self.assertRaises(AssertionError):
			db.replace_custom(9, b'!!')
		with self.assertRaises(AssertionError):
			db.replace_custom(10, b'!')
		with self.assertRaises(AssertionError):
			db.replace_custom(-1, b'!')
		with self.assertRaises(AssertionError):
			db.replace_custom(0, b'0123456789!')

	def test_db_read(self):
		db = DataBuffer(b'0123456789')
		self.assertEqual(db.read(0,3), b'012')
		self.assertEqual(db.read(1,2), b'12')
		self.assertEqual(db.read(9,1), b'9')

		with self.assertRaises(AssertionError):
			db.read(-1,2)
		with self.assertRaises(AssertionError):
			db.read(0,11)
		with self.assertRaises(AssertionError):
			db.read(1,10)
		with self.assertRaises(AssertionError):
			db.read(1,0)
		with self.assertRaises(AssertionError):
			db.read(1,-1)
		with self.assertRaises(AssertionError):
			db.read(10,1)			

	def test_db_patches(self):
		db = DataBuffer(b'0123456789')
		db.replace_custom(0, b'!')
		db.replace_custom(0, b'@@')
		db.read(0, 3)
		db.replace_standard(3, 3)
		self.assertEqual(db.get_patches(), [Range(0,1), Range(0,2), Range(3,3)])
		

if __name__ == '__main__':

	unittest.main()

