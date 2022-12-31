import re


class VarManager:

	def __init__(self):
		self.data = dict()

	def get_data(self):
		return self.data

	def names(self):
		return self.data.keys()

	def set(self, name : str, value : str):
		self.data[name] = str(value)

	def get(self, name : str):
		if name in self.data:
			return self.data[name]
		else:
			raise ValueError(f'Unknown variable - {name}')

	def delete(self, name):
		if name in self.data:
			del self.data[name]
			return True

	def del_by_prefix(self, prefix : str):
		for name in list(self.names()):
			if name.startswith(prefix):
				self.delete(name)



class VarManager2(VarManager):

	def __init__(self):
		self.data = dict()
		self.pattern = re.compile(r'(%|\$)[A-Za-z0-9_]+')

	def validate(self, arg_name):
		match = self.pattern.fullmatch(arg_name)
		if match is None:
			raise ValueError(f'Invalid variable name - {arg_name}')

	def is_var(self, arg_name):
		return arg_name[0] in ['$', '%']

	def replace_list(self, args_list):
		new_args = [] + args_list
		
		for idx, arg in enumerate(new_args):

			if self.is_var(arg):

				self.validate(arg)

				value = self.get(arg)
				new_args[idx] = value

		return new_args

	def set(self, name : str, value : str):
		self.validate(name)
		self.data[name] = str(value)

	def set_type_1(self, name : str, value : str):
		self.set(f'%{name}', value)

	def set_type_2(self, name : str, value : str):
		self.set(f'${name}', value)