import math
import unittest
from dataclasses import astuple, dataclass


@dataclass
class Range:

	offset: int
	size: int

	def __init__(self, offset, size = 0, offset2 = None):
		self.offset = offset
		self.size = size

		if offset2 is not None:
			assert(offset2 > offset)
			self.size = offset2 - offset

		if self.size <= 0:
			raise ValueError('range size <= 0')

		self.offset2 = self.offset + self.size

	def __iter__(self):
		return iter(astuple(self))

	def __repr__(self):
		return self.print_plus()

	def __eq__(self, other):
		return (self.offset == other.offset) & (self.size == other.size)

	def __hash__(self):
		return hash(('offset', self.offset,'size', self.size))

	def print_plus(self):
		return f'{self.offset}+{self.size}'

	def print_minus(self):
		return f'{self.offset}-{self.offset2}'


class RangeList(list):
	''' not used in RangeTools but can be used later for type checking'''
	
	def __repr__(self):
		full_list = ''
		for item in self:
			if full_list: full_list += ' '
			full_list += item.print_plus()
		return full_list
			

class RangeParser:

	@staticmethod
	def parse_str(in_range, max_len):
			
		if not isinstance(in_range, str):
			raise ValueError("invalid range")

		# it can be used as standard argument
		if in_range == '$all':
			in_range = f'0+{max_len}'

		sp = '-' if '-' in in_range else '+'
		r = in_range.split(sp)

		if (not r) or len(r) != 2:	
			raise ValueError("invalid range")

		try:
			in_offset = int(r[0], 0)
			in_size = int(r[1], 0)
		except ValueError:
			raise ValueError("invalid range")

		if(sp == '-'):
			if in_offset >= in_size:
				raise ValueError("start_offset >= end_offset")
			in_size = in_size - in_offset

		if in_size <= 0:
			raise ValueError("size <= 0")

		# check file boundaries
		if (in_offset + in_size) > max_len:
			raise ValueError("offset + size > file_size ")

		return Range(in_offset, in_size)
	

class RangeSubstract:

	def _is_a_overlap_b(self, r1, r2):
		if RangeTools.in_range(r1, r2.offset):
			if not RangeTools.in_range(r1, r2.offset2):
				if r2.offset2 != r1.offset2:
					if r2.offset != r1.offset:
						return True

	def _is_b_inside_a(self, r1, r2):
		if RangeTools.in_range(r1, r2.offset):
			if RangeTools.in_range(r1, r2.offset2):
				if r2.offset > r1.offset:
					return True

	def _is_not_touched(self, r1, r2):
		if r1.offset2 < r2.offset:
			return True

	def _is_common_border(self, r1, r2):
		if r1.offset2 == r2.offset:
			return True

	def _is_a_inside_b_l(self, r1, r2):
		if r1.offset == r2.offset:
			if r2.offset2 > r1.offset2:
				return True

	def _is_a_inside_b_r(self, r1, r2):
		if r1.offset2 == r2.offset2:
			if r1.offset < r2.offset:
				return True

	def substract(self, r1, r2):
		# 0+10 5+10 -> 0+5

		if r1 == r2: # 3
			return None

		if self._is_a_overlap_b(r1, r2): #1
			return Range(offset = r1.offset, offset2 = r2.offset)

		if self._is_a_overlap_b(r2, r1): #1
			return Range(offset = r2.offset2, offset2 = r1.offset2)

		if self._is_b_inside_a(r1, r2): #2
			r3 = Range(offset = r1.offset, offset2 = r2.offset)
			r4 = Range(offset = r2.offset2, offset2 = r1.offset2)
			return [r3, r4]

		if self._is_b_inside_a(r2, r1): #2
			return None

		if self._is_not_touched(r1, r2): #4
			return r1

		if self._is_not_touched(r2, r1): #4
			return r1

		if self._is_common_border(r1, r2): #5
			return r1

		if self._is_common_border(r2, r1): #5
			return r1
		
		if self._is_a_inside_b_l(r1, r2): #6
			return None

		if self._is_a_inside_b_l(r2, r1): #6
			return Range(offset = r2.offset2, offset2 = r1.offset2)	

		if self._is_a_inside_b_r(r1, r2): #7
			return Range(offset = r1.offset, offset2 = r2.offset)

		if self._is_a_inside_b_r(r2, r1): #7
			return None	


class RangeConcater:
	# concat if Ranges have common border or intersection

	def get_last(self):
		if len(self.new_list) == 0:
			return None
		return self.new_list[-1]

	def set_last(self, item):
		self.new_list[-1] = item

	def concat(self, item):
		last = self.get_last()

		if last and RangeTools.is_overlapped(last, item):
			self.set_last(RangeTools.maximize(last, item))	
		else:
			self.new_list.append(item)	

	def optimize(self, offsets):
		self.new_list = []

		for item in RangeTools.unique_sorted_list(offsets):
			self.concat(item)

		return self.new_list


class RangeListSubstracter:

	def _substract_one(self, r1_list, r2):
		new_r1_list = list()

		for r1 in r1_list:
			r_out = RangeTools.substract(r1, r2)

			if isinstance(r_out, Range):
				new_r1_list.append(r_out)

			if isinstance(r_out, list):
				new_r1_list += r_out 

		return new_r1_list

	def execute(self, r1, r2_list):

		if isinstance(r1, Range):
			new_r1_list = [r1]
		else:
			new_r1_list = r1

		for r2 in r2_list:

			new_r1_list2 = self._substract_one(new_r1_list, r2)
			new_r1_list = new_r1_list2

		return RangeTools.concat_list(new_r1_list)


class RangeDivider:

	def _divide_info(self, size, num):
		part_size = size // num
		full_size = part_size * num
		tail_size = size - full_size
		return part_size, tail_size

	def _divide_range(self, offset, size, num):
		part, tail = self._divide_info(size, num)
		r_offset = offset

		for i in range(num):
			r_size = part + 1 if (i < tail) else part 
			if r_size == 0: break
			yield Range(r_offset, r_size)
			r_offset += r_size

	def execute(self, offset, size, num):
		return list(self._divide_range(offset, size, num))


class RangeTools:

	@staticmethod
	def in_range(range_1, offset):
		return (range_1.offset <= offset) & (range_1.offset2 > offset) 

	@staticmethod
	def is_overlapped(range_1, range_2):
		if RangeTools.in_range(range_1, range_2.offset): return True
		if RangeTools.in_range(range_1, range_2.offset2): return True
		if RangeTools.in_range(range_2, range_1.offset): return True
		if RangeTools.in_range(range_2, range_1.offset2): return True
		return False

	@staticmethod
	def is_next_to(range_1, range_2):
		# border touched, not overlapped
		if range_1.offset2 == range_2.offset: return True
		if range_2.offset2 == range_1.offset: return True
		return False

	@staticmethod
	def is_intersected(range_1, range_2):
		if RangeTools.is_next_to(range_1, range_2):
			return False
		return RangeTools.is_overlapped(range_1, range_2)

	@staticmethod
	def maximize(range_1, range_2):
		# can be not overlapped
		offset = min(range_1.offset, range_2.offset)
		offset2 = max(range_1.offset2, range_2.offset2)
		return Range(offset = offset, offset2 = offset2)

	@staticmethod
	def substract(r1, r2):
		# return: None, Range, [Range, Range]
		return RangeSubstract().substract(r1, r2)

	@staticmethod
	def substract2(r1, r2):
		# return: [], [Range], [Range, Range]
		out = RangeTools.substract(r1, r2)

		if isinstance(out, list):
			return out

		if isinstance(out, Range):
			return [out]

		return []

	@staticmethod
	def intersect(r1, r2):
		# return: None, Range
		if not RangeTools.is_intersected(r1 ,r2): return None

		if RangeTools.in_range(r1, r2.offset):
			if RangeTools.in_range(r1, r2.offset2):
				return Range(r2.offset, r2.size)
			else:
				return Range(offset = r2.offset, offset2 = r1.offset2)
		
		if RangeTools.in_range(r2, r1.offset):
			if RangeTools.in_range(r2, r1.offset2):
				return Range(r1.offset, r1.size)
			else:
				return Range(offset = r1.offset, offset2 = r2.offset2)

		raise ValueError('intersect')

	@staticmethod
	def unique_list(range_list):
		return list(set(range_list))

	@staticmethod
	def sorted_list(range_list):
		return sorted(range_list, key = lambda x: x.offset)

	@staticmethod
	def unique_sorted_list(range_list):
		return RangeTools.sorted_list(RangeTools.unique_list(range_list))

	@staticmethod
	def concat_list(range_list):
		return RangeConcater().optimize(range_list)

	@staticmethod
	def parse_str(range_str, max_len):
		return RangeParser.parse_str(range_str, max_len)

	@staticmethod
	def substract_list(r1_list, r2_list):
		# return: [Range, Range]
		return RangeListSubstracter().execute(r1_list, r2_list)

	@staticmethod
	def substract_list2(r1_list, r2_list):
		# return: RangeList
		return RangeList(RangeTools.substract_list(r1_list, r2_list))

	@staticmethod
	def divide_range(offset, size, num):
		return RangeDivider().execute( offset, size, num)


class RangeMapper:

	def __init__(self, range_list):
		self.rl = RangeTools.concat_list(range_list)

		self.size = self.calc_size()

		self.virt = self.make_virtual_list()

	def calc_size(self):
		full = 0

		for item in self.rl:
			full += item.size

		return full

	def get_size(self):
		return self.size
		
	def make_virtual_list(self):
		virt_offset = 0
		virt_list  = list()

		for item in self.rl:
			
			virt_range = Range(virt_offset,item.size)
			virt_list.append(virt_range)
			virt_offset += item.size

		return virt_list

	def map_offset(self, offset):
		virt_offset = 0

		for item in self.rl:

			virt_range = Range(virt_offset, item.size)

			if RangeTools.in_range(virt_range, offset):

				return item.offset + offset - virt_offset

			virt_offset += item.size

		return None

	def map_range(self, need_range):
		assert(need_range.offset + need_range.size <= self.size)

		out_list = list()
		
		for index, virt_range in enumerate(self.virt):

			virt_intersect = RangeTools.intersect(virt_range, need_range)
			if virt_intersect is None: continue

			# map virt to real
			real_range = self.rl[index]
			real_offset = real_range.offset + virt_intersect.offset - virt_range.offset

			out_list.append(Range(real_offset, virt_intersect.size))

		return out_list


############################################################
# UNIT TEST
############################################################


class Test_Range(unittest.TestCase):

	def test_init(self):
		item = Range(0, 10)
		self.assertEqual(item.offset, 0)
		self.assertEqual(item.size, 10)

	def test_init_2(self):
		item = Range(offset = 1, offset2 = 3)
		self.assertEqual(item.offset, 1)
		self.assertEqual(item.size, 2)

		# of2 < of1
		with self.assertRaises(AssertionError):
			item = Range(offset = 2, offset2 = 1)

	def test_unpack(self):
		a,b = Range(10, 20)
		self.assertEqual(a, 10)
		self.assertEqual(b, 20)

	def test_equal(self):
		self.assertEqual(Range(10, 20), Range(10, 20))
		self.assertNotEqual(Range(10, 20), Range(0, 20))


class Test_RangeParser(unittest.TestCase):

	def test_all(self):
		item = RangeParser.parse_str('$all', 10)
		self.assertEqual(item.offset, 0)
		self.assertEqual(item.size, 10)
		
	def test_plus(self):
		item = RangeParser.parse_str('10+20', 100)
		self.assertEqual(item.offset, 10)
		self.assertEqual(item.size, 20)

	def test_minus(self):
		item = RangeParser.parse_str('10-20', 100)
		self.assertEqual(item.offset, 10)
		self.assertEqual(item.size, 10)

	def test_oversize(self):
		with self.assertRaises(ValueError):
			item = RangeParser.parse_str('10-20', 10)
		with self.assertRaises(ValueError):
			item = RangeParser.parse_str('11+20', 30)

	def test_a_over_b(self):
		with self.assertRaises(ValueError):
			item = RangeParser.parse_str('20-10', 100)

	def test_undersize(self):
		with self.assertRaises(ValueError):
			item = RangeParser.parse_str('20-20', 100)

	# def test_list(self):
	# 	item = RangeParser.parse_str('10-30 30-40', 100)
	# 	self.assertEqual(item, RangeList([Range(10,20), Range(30, 10)]))

class Test_RangeTools(unittest.TestCase):

	def test_in_range(self):
		item = Range(0, 10)
		self.assertEqual(RangeTools.in_range(item, 0), True)
		self.assertEqual(RangeTools.in_range(item, 5), True)
		self.assertEqual(RangeTools.in_range(item, 9), True)
		self.assertEqual(RangeTools.in_range(item, 10), False)
		self.assertEqual(RangeTools.in_range(item, 11), False)
		
	def test_overlapped(self):
		# same border
		self.assertEqual(RangeTools.is_overlapped(Range(0, 3), Range(3, 2)), True)
		self.assertEqual(RangeTools.is_overlapped(Range(3, 2), Range(0, 3)), True)
		# a over b
		self.assertEqual(RangeTools.is_overlapped(Range(0, 3), Range(2, 4)), True)
		self.assertEqual(RangeTools.is_overlapped(Range(2, 4), Range(0, 3)), True)
		# a in b
		self.assertEqual(RangeTools.is_overlapped(Range(0, 3), Range(1, 1)), True)
		self.assertEqual(RangeTools.is_overlapped(Range(1, 1), Range(0, 3)), True)
		# b after a
		self.assertEqual(RangeTools.is_overlapped(Range(0, 3), Range(4, 2)), False)
		self.assertEqual(RangeTools.is_overlapped(Range(4, 2), Range(0, 3)), False)

	def test_is_next_to(self):
		self.assertEqual(RangeTools.is_next_to(Range(0, 3), Range(3, 2)), True)
		self.assertEqual(RangeTools.is_next_to(Range(3, 2), Range(0, 3)), True)
		# not touched
		self.assertEqual(RangeTools.is_next_to(Range(0, 3), Range(4, 3)), False)
		self.assertEqual(RangeTools.is_next_to(Range(4, 3), Range(0, 3)), False)
		# overlapped
		self.assertEqual(RangeTools.is_next_to(Range(0, 3), Range(0, 5)), False)
		self.assertEqual(RangeTools.is_next_to(Range(0, 5), Range(0, 3)), False)
		# same
		self.assertEqual(RangeTools.is_next_to(Range(3, 5), Range(3, 5)), False)
		# inside
		self.assertEqual(RangeTools.is_next_to(Range(0, 10), Range(5, 2)), False)
		self.assertEqual(RangeTools.is_next_to(Range(5, 2), Range(0, 10)), False)

	def test_maximize(self):
		# common border
		self.assertEqual(RangeTools.maximize(Range(0, 3), Range(3, 2)), Range(0, 5))
		self.assertEqual(RangeTools.maximize(Range(3, 2), Range(0, 3)), Range(0, 5))
		# not touched
		self.assertEqual(RangeTools.maximize(Range(0, 3), Range(5, 5)), Range(0, 10))
		self.assertEqual(RangeTools.maximize(Range(5, 5), Range(0, 3)), Range(0, 10))
		# inside
		self.assertEqual(RangeTools.maximize(Range(0, 10), Range(5, 1)), Range(0, 10))
		self.assertEqual(RangeTools.maximize(Range(5, 1), Range(0, 10)), Range(0, 10))

	def test_substract(self):
		# b overlap a #1
		self.assertEqual(RangeTools.substract(Range(0, 3), Range(2, 3)), Range(0, 2))
		self.assertEqual(RangeTools.substract(Range(2, 3), Range(0, 3)), Range(3, 2))
		# b inside a #2
		self.assertEqual(RangeTools.substract(Range(0, 5), Range(2, 1)), [Range(0, 2), Range(3, 2)])
		self.assertEqual(RangeTools.substract(Range(2, 3), Range(0, 6)), None)
		# same range #3
		self.assertEqual(RangeTools.substract(Range(2, 3), Range(2, 3)), None)
		# not touched # 4
		self.assertEqual(RangeTools.substract(Range(0, 3), Range(4, 2)), Range(0, 3))
		self.assertEqual(RangeTools.substract(Range(4, 2), Range(0, 3)), Range(4, 2))
		# common borders, but not overlapped #5
		self.assertEqual(RangeTools.substract(Range(0, 3), Range(3, 2)), Range(0, 3))
		self.assertEqual(RangeTools.substract(Range(3, 2), Range(0, 3)), Range(3, 2))
		# a in b, same left border #6
		self.assertEqual(RangeTools.substract(Range(0, 2), Range(0, 3)), None)
		self.assertEqual(RangeTools.substract(Range(0, 3), Range(0, 2)), Range(2, 1))
		# a in b, same right border #7
		self.assertEqual(RangeTools.substract(Range(0, 3), Range(2, 1)), Range(0, 2))
		self.assertEqual(RangeTools.substract(Range(2, 1), Range(0, 3)), None)

	def test_substract_2a(self):
		self.assertEqual(RangeTools.substract(Range(0, 3), Range(4, 3)), Range(0, 3))
		self.assertEqual(RangeTools.substract(Range(1, 3), Range(4, 3)), Range(1, 3))
		self.assertEqual(RangeTools.substract(Range(2, 3), Range(4, 3)), Range(2, 2))
		self.assertEqual(RangeTools.substract(Range(3, 3), Range(4, 3)), Range(3, 1))
		self.assertEqual(RangeTools.substract(Range(4, 3), Range(4, 3)), None)
		self.assertEqual(RangeTools.substract(Range(5, 3), Range(4, 3)), Range(7, 1))
		self.assertEqual(RangeTools.substract(Range(6, 3), Range(4, 3)), Range(7, 2))
		self.assertEqual(RangeTools.substract(Range(7, 3), Range(4, 3)), Range(7, 3))
		self.assertEqual(RangeTools.substract(Range(8, 3), Range(4, 3)), Range(8, 3))
		
	def test_substract_2b(self):
		self.assertEqual(RangeTools.substract(Range(4, 3), Range(0, 3)), Range(4, 3))
		self.assertEqual(RangeTools.substract(Range(4, 3), Range(1, 3)), Range(4, 3))
		self.assertEqual(RangeTools.substract(Range(4, 3), Range(2, 3)), Range(5, 2))
		self.assertEqual(RangeTools.substract(Range(4, 3), Range(3, 3)), Range(6, 1))
		self.assertEqual(RangeTools.substract(Range(4, 3), Range(4, 3)), None)
		self.assertEqual(RangeTools.substract(Range(4, 3), Range(5, 3)), Range(4, 1))
		self.assertEqual(RangeTools.substract(Range(4, 3), Range(6, 3)), Range(4, 2))
		self.assertEqual(RangeTools.substract(Range(4, 3), Range(7, 3)), Range(4, 3))
		self.assertEqual(RangeTools.substract(Range(4, 3), Range(8, 3)), Range(4, 3))

	def test_intersect_2a(self):
		self.assertEqual(RangeTools.intersect(Range(0, 3), Range(4, 3)), None)
		self.assertEqual(RangeTools.intersect(Range(1, 3), Range(4, 3)), None)
		self.assertEqual(RangeTools.intersect(Range(2, 3), Range(4, 3)), Range(4, 1))
		self.assertEqual(RangeTools.intersect(Range(3, 3), Range(4, 3)), Range(4, 2))
		self.assertEqual(RangeTools.intersect(Range(4, 3), Range(4, 3)), Range(4, 3))
		self.assertEqual(RangeTools.intersect(Range(5, 3), Range(4, 3)), Range(5, 2))
		self.assertEqual(RangeTools.intersect(Range(6, 3), Range(4, 3)), Range(6, 1))
		self.assertEqual(RangeTools.intersect(Range(7, 3), Range(4, 3)), None)
		self.assertEqual(RangeTools.intersect(Range(8, 3), Range(4, 3)), None)

	def test_intersect_2b(self):
		self.assertEqual(RangeTools.intersect(Range(4, 3), Range(0, 3)), None)
		self.assertEqual(RangeTools.intersect(Range(4, 3), Range(1, 3)), None)
		self.assertEqual(RangeTools.intersect(Range(4, 3), Range(2, 3)), Range(4, 1))
		self.assertEqual(RangeTools.intersect(Range(4, 3), Range(3, 3)), Range(4, 2))
		self.assertEqual(RangeTools.intersect(Range(4, 3), Range(4, 3)), Range(4, 3))
		self.assertEqual(RangeTools.intersect(Range(4, 3), Range(5, 3)), Range(5, 2))
		self.assertEqual(RangeTools.intersect(Range(4, 3), Range(6, 3)), Range(6, 1))
		self.assertEqual(RangeTools.intersect(Range(4, 3), Range(7, 3)), None)
		self.assertEqual(RangeTools.intersect(Range(4, 3), Range(8, 3)), None)

	def test_sorted_list(self):
		self.assertEqual(RangeTools.sorted_list([Range(0,2), Range(3,1)]), [Range(0,2), Range(3,1)])
		self.assertEqual(RangeTools.sorted_list([Range(5,1), Range(1,3)]), [Range(1,3), Range(5,1)])
		self.assertEqual(RangeTools.sorted_list([Range(0,2), Range(0,2)]), [Range(0,2), Range(0,2)])

	def test_unique_sorted_list(self):
		self.assertEqual(RangeTools.unique_sorted_list([Range(0,2), Range(3,1)]), [Range(0,2), Range(3,1)])
		self.assertEqual(RangeTools.unique_sorted_list([Range(3,1), Range(0,2)]), [Range(0,2), Range(3,1)])
		init = [Range(0,2), Range(3,2), Range(0,2)]
		self.assertEqual(RangeTools.unique_sorted_list(init), [Range(0,2), Range(3,2)])
		self.assertEqual(init, [Range(0,2), Range(3,2), Range(0,2)])

	def test_concat_list(self):
		self.assertEqual(RangeTools.concat_list([Range(0,1), Range(1,2)]), [Range(0,3)])
		self.assertEqual(RangeTools.concat_list([Range(1,2), Range(0,1)]), [Range(0,3)])
		self.assertEqual(RangeTools.concat_list([Range(0,2), Range(3,1)]), [Range(0,2), Range(3,1)])
		# check original list mod
		init = [Range(0,108800), Range(108800,54400)]
		self.assertEqual(RangeTools.concat_list(init), [Range(0,163200)])
		self.assertEqual(init, [Range(0,108800), Range(108800,54400)])

	def test_substract_list(self):
		self.assertEqual(RangeTools.substract_list([Range(0,4)], [Range(0,1), Range(3,1)]), [Range(1,2)])
		self.assertEqual(RangeTools.substract_list([Range(0,5)], [Range(1,1), Range(3,1)]), [Range(0,1), Range(2,1), Range(4,1)])
		self.assertEqual(RangeTools.substract_list([Range(0,100)], [Range(1,1), Range(5,2)]), [Range(0,1), Range(2,3), Range(7,93)])

		r1 = Range(0,52800)
		r2 = [Range(50781,0,50903), Range(50903,0,50964), Range(50964,0,50995)]
		out = RangeTools.substract_list(r1,r2)

		r1b = Range(0,52800)
		r2b = [Range(50781,0,50903), Range(50903,0,50964), Range(50995,0,51026)]
		outb = RangeTools.substract_list(r1b,r2b)

	def test_divide_range(self):
		self.assertEqual(RangeTools.divide_range(0,10,3), [Range(0,4), Range(4,3), Range(7,3)])
		out = RangeTools.divide_range(10,244,70)
		self.assertEqual(len(out), 70)
		self.assertEqual(out[1], Range(14,4))
		self.assertEqual(out[33].size, 4)
		self.assertEqual(out[34].size, 3)
		self.assertEqual(RangeTools.divide_range(1,3,4), [Range(1,1), Range(2,1), Range(3,1)])


class Test_RangeMapper(unittest.TestCase):

	def test_1(self):

		real_list = [Range(1,3), Range(6,3)]
		mapper = RangeMapper(real_list)

		self.assertEqual(mapper.calc_size(), 6)

		self.assertEqual(mapper.map_offset(0), 1)
		self.assertEqual(mapper.map_offset(1), 2)
		self.assertEqual(mapper.map_offset(2), 3)
		self.assertEqual(mapper.map_offset(3), 6)
		self.assertEqual(mapper.map_offset(4), 7)
		self.assertEqual(mapper.map_offset(5), 8)
		self.assertEqual(mapper.map_offset(6), None)

		virt_list = mapper.make_virtual_list()
		self.assertEqual(virt_list, [Range(0,3), Range(3,3)])

		self.assertEqual(mapper.map_range(Range(0,1)), [Range(1,1)])
		self.assertEqual(mapper.map_range(Range(0,2)), [Range(1,2)])
		self.assertEqual(mapper.map_range(Range(0,3)), [Range(1,3)])
		self.assertEqual(mapper.map_range(Range(0,4)), [Range(1,3), Range(6,1)])
		self.assertEqual(mapper.map_range(Range(0,5)), [Range(1,3), Range(6,2)])
		self.assertEqual(mapper.map_range(Range(0,6)), [Range(1,3), Range(6,3)])
		
		self.assertEqual(mapper.map_range(Range(3,1)), [Range(6,1)])
		self.assertEqual(mapper.map_range(Range(3,2)), [Range(6,2)])
		self.assertEqual(mapper.map_range(Range(5,1)), [Range(8,1)])
		self.assertEqual(mapper.map_range(Range(2,2)), [Range(3,1), Range(6,1)])
		self.assertEqual(mapper.map_range(Range(1,2)), [Range(2,2)])

		with self.assertRaises(AssertionError):
			mapper.map_range(Range(0,7))

		with self.assertRaises(AssertionError):
			mapper.map_range(Range(5,2))
		

if __name__ == '__main__':

	unittest.main()
