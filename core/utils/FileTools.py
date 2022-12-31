import os
import shutil


class FileTools:

	@staticmethod
	def SetHome(path):
		home = os.path.realpath(os.path.dirname(path))
		os.chdir(home)

	@staticmethod
	def GetScriptDir():
		return os.path.realpath(__file__)
	
	@staticmethod
	def ReadFile(path):
		if not FileTools.IsFile(path):
			raise ValueError(F'file not found! {path}')
		with open(path, 'rb') as f:
			return f.read()

	@staticmethod
	def SaveFile(path, data):
		with open(path, 'wb') as f:
			f.write(data)
			
	@staticmethod
	def GetAbsolutePath(path):
		path = path.replace('\'', '')
		path = path.replace('\"', '')
		return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))

	@staticmethod
	def GetDirPath(path):
		return os.path.realpath(os.path.dirname(path))

	@staticmethod
	def GetFileName(path):
		return os.path.basename(path)

	@staticmethod
	def MakePath(file_name, dir_name):
		return f'{dir_name}{os.sep}{file_name}'

	@staticmethod
	def SaveFile2(file_name, dir_name, file_data):
		file_path = FileTools.MakePath(file_name, dir_name)	
		FileTools.SaveFile(file_path, file_data)	

	@staticmethod
	def IsFile(file_path):
		return os.path.isfile(file_path) 

	@staticmethod
	def IsDir(file_path):
		return os.path.isfile(file_path) 

	@staticmethod
	def DelFile(file_name, dir_name):
		file_path = FileTools.MakePath(file_name, dir_name)	
		if not os.path.isfile(file_path): return
		os.unlink(file_path)

	@staticmethod
	def DelFile2(file_path):
		if not os.path.isfile(file_path): return
		os.unlink(file_path)

	@staticmethod
	def MkDir(dir_name):
		if not os.path.isdir(dir_name):
			# make nested path
			os.makedirs(dir_name)

	@staticmethod
	def RmDir(dir_name):
		shutil.rmtree(dir_name)

	@staticmethod
	def RmDirEmpty(dir_name):
		try:
			os.rmdir(dir_name)
			return True
		except OSError:
			return False

	@staticmethod
	def GetSize(path):
		return os.path.getsize(path)
		# can raise OSError 




