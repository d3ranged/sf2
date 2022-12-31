

class FlagParser:

	'''
		"command arg1 arg2 -1 666 12 -2 3 -aaa"
								=>
		('arg1', 'arg2', '-1', '666', '12', '-2', '3', '-aaaa')
								=>
		[aaaa(()), 2(('3',)), 1(('666', '12'))]
	'''

	def _get_flag_idx(self, inp):
		return [idx for idx, i in enumerate(inp) if i.startswith('-')]

	def _get_flag_data(self, inp):
		for idx in reversed(self._get_flag_idx(inp)):
			yield inp[idx:]
			inp = inp[:idx]

	def _parse_flags(self, inp):
		flag_lst = self._get_flag_data(inp)
		for item in flag_lst:
			cmd = item[0].replace('-','')
			args = item[1:]
			yield cmd, args

	def remove_flags(self, inp):
		idx = list(self._get_flag_idx(inp))
		if not idx: return inp
		return inp[:idx[0]]

	def parse(self, inp):
		return dict(self._parse_flags(inp))


def get_format_arg_count(mask):

	for i in range(150):

		try:
			out_str = mask.format(*list(range(i)))
			return i
		except IndexError:
			pass

