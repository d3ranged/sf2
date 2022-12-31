def remove_quotes(in_str):
	out_str = in_str.strip()

	if not in_str: return ''

	if out_str[0] in ['\'', '"']:
		if out_str[0] != out_str[-1]:
			raise ValueError('Unterminated quoted string')
		else:
			out_str = out_str[1:-1]
	return out_str


def format_bytes(size):
	"""Return the given bytes as a human friendly KB, MB, GB, or TB string."""
	B = float(size)
	KB = float(1024)
	MB = float(KB ** 2) # 1,048,576
	GB = float(KB ** 3) # 1,073,741,824
	TB = float(KB ** 4) # 1,099,511,627,776

	if B < KB:
		return '{0} {1}'.format(B,'Bytes' if 0 == B > 1 else 'Byte')
	elif KB <= B < MB:
		return '{0:.2f} KB'.format(B / KB)
	elif MB <= B < GB:
		return '{0:.2f} MB'.format(B / MB)
	elif GB <= B < TB:
		return '{0:.2f} GB'.format(B / GB)
	elif TB <= B:
		return '{0:.2f} TB'.format(B / TB)


def format_float(data):
	return "{:4.2f}".format(data)


def get_format_arg_count(mask):

	for i in range(150):

		try:
			out_str = mask.format(*list(range(i)))
			return i
		except IndexError:
			pass

