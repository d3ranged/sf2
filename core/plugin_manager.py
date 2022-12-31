from core.utils import *
from core.plugin_aux import *
from core.preload_cmd import *
from plugins import *


class PluginManager:

	def __init__(self, core):
		self.core = core
		self.build_plugin_list()
		self.active_modules = {}

		self.load_modules()
		self.load_commands()

	def debug(self, *arg):
		if not SF_DEBUG_PM: return
		self.core.repl.debug(*arg)

	def class_list(self, mytype):
		for k in globals():
			item = globals()[k]
			if hasattr(item, '__bases__'):
				if mytype in item.__bases__:
					yield item


	def build_plugin_list(self):
		self.modules = list(self.class_list(MODULES_BASE))
		self.commands = list(self.class_list(COMMANDS_BASE))


	def get_item_by_name(self, plug_list, name):
		if name in plug_list:
			return plug_list[name]

	def get_template_by_name(self, plug_list, name):
		for item in plug_list:
			if item.name == name:
				return item

	def get_module_by_name(self, name):
		return self.get_item_by_name(self.active_modules, name)

	def attach_mods(self, instance):
		for mod in instance.req_mods:
			mod_inst = self.get_module_by_name(mod)
			if not mod_inst:
				self.debug(f'no mod - {mod}')
				return False
			setattr(instance, mod, mod_inst)
		return True

	def attach_attr(self, instance):
		for attr in instance.req_attr:
			if not hasattr(self.core, attr):
				self.debug(f'no attr - core.{attr}')
				return False
			# if not getattr(self.core, attr):
			# 	self.debug(f'cant get attr - core.{attr}')
			# 	return False
			if getattr(self.core, attr) is None:
				self.debug(f'none attr - core.{attr}')
				return False
			# link some core information
			setattr(instance, attr, getattr(self.core, attr))
		return True

		
	def attach_methods(self, instance):
		pass


	def load_commands(self):

		for item in self.commands:

			instance = item()

			self.debug('try to load cmd: ', instance.name)

			# skip if required not existed module 
			if not self.attach_mods(instance): continue
			# skip if it requires not loaded file data
			if not self.attach_attr(instance): continue
			# add some new api
			self.attach_methods(instance)

			# add command to our cli
			manual = instance.__doc__ if instance.__doc__ else None

			self.core.riposte.add_command(instance.name, instance.desc, instance.execute, manual)
			self.debug('cmd loaded: ', instance.name)


	def load_modules(self):
		self.active_modules = {}

		for item in self.modules:
			instance = item()
			self.debug('try to load mod: ', instance.name)

			# skip mod if required module does not exist
			if not self.attach_mods(instance): continue
			# skip mod if it requires not loaded file data
			if not self.attach_attr(instance): continue

			if not instance.can_run(): continue
			if not instance.is_my_type(): continue

			# register as active module
			name = instance.name
			value = instance.load()
			self.active_modules[name] = value
			self.debug('mod loaded: ', name)
		
