import sys
import math
from collections import Counter


class ByteTools:

	@staticmethod
	def str2bytes(new_bytes):
		if sys.version_info >= (3, 0):
			return bytes(new_bytes, 'utf-8')
		# python 2 have only 'str'
		return new_bytes

	@staticmethod
	def bytes2str(new_bytes):
		return new_bytes.decode("utf-8") 

	@staticmethod
	def entropy(data):
		"""Calculate the entropy of a chunk of data."""

		if not data:
			return 0.0

		occurences = Counter(bytearray(data))

		entropy = 0
		for x in occurences.values():
			p_x = float(x) / len(data)
			entropy -= p_x * math.log(p_x, 2)

		return entropy

	@staticmethod
	def bytes2int(raw_bytes):
		return int.from_bytes(raw_bytes, 'big', signed = False)

	@staticmethod
	def int2bytes(number, fill_size = 0):
		assert(number > 0)
		bytes_required = max(1, math.ceil(number.bit_length() / 8))
		if fill_size > 0: return number.to_bytes(fill_size, 'big')
		return number.to_bytes(bytes_required, 'big', signed = False)