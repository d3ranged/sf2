import atexit

from core.utils import *
from core.config import *
from core.data_buffer import *


class MetaData:

	def __init__(self):
		self.list = dict()
		self.last_id = 0

	def get_last_id(self):
		# zero mean no one
		return self.last_id

	def add_entry(self):
		self.last_id += 1
		item_id = self.last_id
		self.list[item_id] = dict()
		return item_id
		
	def _get_entry(self, item_id):
		if item_id in self.list:
			return self.list[item_id]

	def set_data(self, item_id, name, value):
		item = self._get_entry(item_id)
		if item is None: raise ValueError('invalid meta_id')
		item[name] = value

	def get_data(self, item_id, name):
		item = self._get_entry(item_id)
		if item is None: raise ValueError('invalid meta_id')
		
		if name not in item: return None
		return item[name]

	def list_index(self):
		for index in self.list.keys():
			yield index


class FileBackup:

	def __init__(self, top_dir):
		self.bak_dir = self.get_backup_dir(top_dir)

	def get_backup_dir(self, top_dir):
		out_path = FileTools.MakePath(SF_BACKUP_DIR, top_dir)
		FileTools.MkDir(out_path)
		return out_path

	def get_bak_name(self, idx):
		return f'{idx}.bin'

	def add_backup(self, idx, data):
		bak_name = self.get_bak_name(idx)
		FileTools.SaveFile2(bak_name, self.bak_dir, data)

	def del_backups(self):
		FileTools.RmDir(self.bak_dir)

	def get_backup_path(self, idx):
		bak_name = self.get_bak_name(idx)
		file_path = FileTools.MakePath(bak_name, self.bak_dir)
		return file_path


class FileManager:

	def __init__(self, core):
		self.riposte = core.riposte
		self.top_dir = core.top_dir
		self.load_id = None
		self.riposte_id = None
		self.cmd_id = None

		self.file_list = MetaData()
		self.cmd_list = MetaData()
		self.bak = FileBackup(self.top_dir)

		atexit.register(self.bak.del_backups)

		if SF_REMOVE_OUTPUT:
			atexit.register(self.remove_output)

	def load_by_path(self, file_path):

		path = FileTools.GetAbsolutePath(file_path)
		file_dir = FileTools.GetDirPath(path)
		file_name = FileTools.GetFileName(path)

		file_data = FileTools.ReadFile(path)
		file_size = len(file_data)
	
		self.load_id = self.file_list.add_entry()

		if SF_BACKUP_INPUT:
			self.bak.add_backup(self.load_id, file_data)

		self.file_list.set_data(self.load_id, 'type', 'input')
		self.file_list.set_data(self.load_id, 'file_dir', file_dir)
		self.file_list.set_data(self.load_id, 'file_name', file_name)
		self.file_list.set_data(self.load_id, 'file_size', file_size)
		self.file_list.set_data(self.load_id, 'full_path', path)

		return self.load_id, path, file_data


	def _read_by_index(self, file_id):
		real_path = self.bak.get_backup_path(file_id)
		file_data = FileTools.ReadFile(real_path)
		return file_data


	def load_by_index(self, file_id):
		
		in_path = self.file_list.get_data(file_id, 'full_path')
		file_data = self._read_by_index(file_id)

		self.load_id = file_id

		return file_id, in_path, file_data


	def new_file(self, data_buffer, opt_comment):

		assert(isinstance(data_buffer, DataBuffer))

		self._update_cmd_id()
		file_id = self.file_list.add_entry()

		file_patch = data_buffer.get_patches()
		file_data = data_buffer.get_data()
		file_size = len(file_data)

		self.bak.add_backup(file_id, file_data)

		# create new dir for every command
		# so we can scan files separately
		self.out_dir = self._get_out_dir()
		self.riposte.vars.set(f'$out', self.out_dir)

		FileTools.MkDir(self.out_dir)

		out_name = f'{file_id}.bin'
		FileTools.SaveFile2(out_name, self.out_dir, file_data)
		full_path = FileTools.MakePath(out_name, self.out_dir)	

		self.file_list.set_data(file_id, 'type', 'output')
		self.file_list.set_data(file_id, 'cmd_id', self.cmd_id)
		self.file_list.set_data(file_id, 'parent_id', self.load_id)
		self.file_list.set_data(file_id, 'patch_list', file_patch)
		self.file_list.set_data(file_id, 'file_dir', self.out_dir)
		self.file_list.set_data(file_id, 'file_name', out_name)
		self.file_list.set_data(self.load_id, 'file_size', file_size)
		self.file_list.set_data(file_id, 'full_path', full_path)
		self.file_list.set_data(file_id, 'comment', opt_comment)

		self.riposte.success(f'{out_name}')

	def _update_cmd_id(self):
		last_id = self.riposte.get_cmd_counter()
		if last_id == self.riposte_id:
			return

		self.cmd_id = self.cmd_list.add_entry()

		cmd_line = self.riposte.get_cmd_line()	
		self.cmd_list.set_data(self.cmd_id, 'cmd_line', cmd_line)
		self.cmd_list.set_data(self.cmd_id, 'loaded_file_id', self.load_id)
		self.riposte_id = last_id

	def _get_out_dir(self, path = None):

		if path is None: path = self.top_dir

		dir_full = FileTools.MakePath(SF_OUT_DIR, path)
		dir_full = FileTools.MakePath(f'{self.cmd_id}', dir_full)

		return FileTools.GetAbsolutePath(dir_full) 

	def _prepare_folders(self, folders):

		temp = []
		folders.reverse()

		for item in folders:

			if item in temp:
				continue
			
			temp.append(item)

		return temp

	def remove_output(self):

		folders = list()

		for file_id in self.file_list.list_index():

			file_type = self.file_list.get_data(file_id, 'type')
			full_path = self.file_list.get_data(file_id, 'full_path')
			file_dir = self.file_list.get_data(file_id, 'file_dir')

			if file_type != 'output': continue

			folders.append(file_dir)
			FileTools.DelFile2(full_path)

		for dir_path in self._prepare_folders(folders):
				FileTools.RmDirEmpty(dir_path)


class FileInterface:

	def __init__(self, file_manager):
		self.fm = file_manager
		self.cmd = self.fm.cmd_list
		self.file = self.fm.file_list

	def get_last_cmd_id(self):
		# can return 0, that means empty list
		return self.cmd.get_last_id()

	def get_last_file_id(self):
		# can return 0, that means empty list
		return self.file.get_last_id()

	def is_valid_cmd_id(self, cmd_id):
		return cmd_id > 0 and cmd_id <=	self.get_last_cmd_id()

	def is_valid_file_id(self, file_id):
		return file_id > 0 and file_id <= self.get_last_file_id()

	def get_file_info(self, file_id : int, name : str):
		return self.file.get_data(file_id, name)

	def set_file_info(self, file_id : int, name : str, value):
		return self.file.set_data(file_id, name, value)

	def get_file_list(self, cmd_id : int):

		out_list = []

		for file_id in self.file.list_index():

			file_cmd_id = self.file.get_data(file_id, 'cmd_id')
			if file_cmd_id is None: continue

			if cmd_id == file_cmd_id:
				out_list.append(file_id)

		return out_list

	def get_cmd_list(self):
		return list(self.cmd.list_index())

	def new_file(self, data, comment : str = ''):
		self.fm.new_file(data, comment) 

	def read_file(self, file_id : int):
		return self.fm._read_by_index(file_id)

	def get_cmd_info(self, cmd_id : int, name : str):
		return self.cmd.get_data(cmd_id, name)

	def is_file_exist(self, file_id):
		full_path = self.get_file_info(file_id, 'full_path')
		return FileTools.IsFile(full_path)

	def get_cmd_work_range(self, cmd_id):
		# return Range or None

		file_list = self.get_file_list(cmd_id)
		if not file_list: return None

		full_list = []

		for file_id in file_list:
			patch_list = self.get_file_info(file_id, 'patch_list')
			full_list += patch_list

		full_list = RangeTools.unique_sorted_list(full_list)

		if not full_list:
			return None
		else:
			return RangeTools.maximize(full_list[0], full_list[-1])

