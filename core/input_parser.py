import re

from core.utils import *


class InputParser:

	def __init__(self, core):

		self.core = core
		self.re_var = re.compile(r'(%|\$)[A-Za-z0-9_]+')
		self.re_patch = re.compile(r'p[0-9]+')
		self.re_patch_i = re.compile(r'i[0-9]+')

	def is_fpatch(self, in_str):
		# check format p+num
		match = self.re_patch.fullmatch(in_str)
		return False if match is None else True

	def is_ipatch(self, in_str):
		match = self.re_patch_i.fullmatch(in_str)
		return False if match is None else True

	def parse_fpatch(self, in_str):
		'''
		special input format
		p123 mean load patches from file #123
		'''

		if not self.is_fpatch(in_str):
			return None

		file_id = int(in_str[1:])
		patch_list = self.core.fi.get_file_info(file_id, 'patch_list')
		return RangeList(patch_list) if patch_list else None


	def parse_ipatch(self, in_str):
		'''
		special input format
		i123 = w123 - p123
		'''

		if not self.is_ipatch(in_str):
			return None

		file_id = int(in_str[1:])

		cmd_id = self.core.fi.get_file_info(file_id, 'cmd_id')
		work_range = self.core.fi.get_cmd_work_range(cmd_id)

		if work_range is None:
			return None

		patch_list = self.core.fi.get_file_info(file_id, 'patch_list')

		ipatch_list = RangeTools.substract_list2(work_range, patch_list)
		return ipatch_list


	def parse_range_str(self, in_str):
		try:
			return RangeTools.parse_str(in_str, self.core.db.len())
		except ValueError:
			return None


	def format_RangeList(self, out):

		if isinstance(out, RangeList):

			if len(out) == 1:
				return out[0]

			elif len(out) == 0:
				raise ValueError('Empty RangeList')

			else:
				return out


	def parse_special(self, in_str):
		# return RangeList, Range, Null or ValueError

		fpatch = self.parse_fpatch(in_str)

		ipatch = self.parse_ipatch(in_str)

		if fpatch:
			return self.format_RangeList(fpatch)

		elif ipatch:
			return self.format_RangeList(ipatch)


	def parse_special_str(self, in_str):
		special = self.parse_special(in_str)
		return str(special) if special else None


	def parse_range(self, in_str):
		# return RangeList, Range or ValueError
		return self.parse_special(in_str) or self.parse_range_str(in_str)

