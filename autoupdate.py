mewnbase_de=r'C:\Users\HP\Desktop\mewnbase_de'
mewnbase_un=r"C:\Users\HP\Desktop\mewnbase_un" 
mewnbase_out=r"C:\Users\HP\Desktop\mewnbase_out"
original_path = r"D:\steam\steamapps\common\MewnBase"
desktop_jar=r'game\desktop-1.0.jar'
exe_name = "MewnBase.exe"
with_console=True
checks_delay = 5


import os, sys
import zipfile
import shutil
import time
import io

import importlib.util
if (spec := importlib.util.find_spec("readchar")) is not None:
	print(f"readchar already in sys.modules")
else:
	print(f"readchar isn't in sys.modules")
	import pip
	if hasattr(pip, 'main'):
		pip.main(['install', "readchar"])
	else:
		pip._internal.main(['install', "readchar"])

from readchar import readkey, key
from threading import Thread

_exe_path=original_path+os.path.sep+exe_name
_desktop_jar_full_path=original_path+os.path.sep+desktop_jar
_lastmodify={}
_changed = []
_stop = False
_lastprint = "input"
_line = ""
_isstartgame = False
_textinput = lambda changes_count: f"There is(are) {changes_count} modified file(s). Launch Mewnbase(yes) or close autoupdater(exit)? (yes/exit):" if not _isstartgame else "Mewnbase is starting..."

def zipdir(path, ziph):
	count=0
	for root, dirs, files in os.walk(path):
		for file in files:
			count+=1
	proceed=0
	for root, dirs, files in os.walk(path):
		for file in files:
			proceed+=1
			file_path = os.path.join(root, file)
			archive_name = os.path.relpath(file_path, path)
			ziph.write(file_path, archive_name)
			if proceed % 500 == 0:
				print(proceed, count, end='\r')
for root, dirs, files in os.walk(mewnbase_de):
	for file in files:
		if file[-5:] == '.java':
			file_path = os.path.join(root, file)
			_lastmodify[file_path] = os.path.getmtime(file_path)


class InputThread(Thread):
	def run(self):
		global _lastprint, _stop, _line, _isstartgame
		def compile_game():
			global _isstartgame, _changed, _lastprint
			os.popen('taskkill /F /IM mewnbase.exe')
			time.sleep(0.6)
			if len(_changed) > 0:
				os.system(fr'javac -cp {mewnbase_un} {" ".join(_changed)} -d {mewnbase_out} --release 8')#--source 8 --target 8')
				_lastprint="compile"
				shutil.copytree(mewnbase_out, mewnbase_un, ignore_dangling_symlinks=False, dirs_exist_ok=True)
				zip_buffer=io.BytesIO()
				zout = zipfile.ZipFile (zip_buffer, 'w')
				zipdir(mewnbase_un, zout)
				zout.close()
				_changed=[]
				with open(_desktop_jar_full_path, 'wb') as f:
					f.write(zip_buffer.getvalue())
				_lastprint="compile"
			if with_console:
				curdir = os.getcwd()
				os.chdir(original_path)
				os.system(fr'java -jar {desktop_jar}')
				os.chdir(curdir)
			else:
				os.startfile(_exe_path)
			_isstartgame = False

		print(_textinput(len(_changed)), _line)
		while True:
			try:
				symbol = readkey()
			except KeyboardInterrupt:
				_stop = True
				exit()
			if not _isstartgame:
				if _lastprint=="input":
					delete_last_line()
				if symbol==key.ENTER:
					print(_textinput(len(_changed)), _line)
					_lastprint="input"
					if _line.lower()=="yes":
						_isstartgame = True
						print(_textinput(len(_changed)))
						compile_game()
					elif _line.lower()=="exit":
						_stop = True
						exit()
					_line=""
					print(_textinput(len(_changed)), _line)
					_lastprint="input"
				elif symbol==key.BACKSPACE:
					_line=_line[:-1]
					print(_textinput(len(_changed)), _line)
					_lastprint="input"
				else:
					_line+=symbol
					print(_textinput(len(_changed)), _line)
					_lastprint="input"
			

class ChangesThread(Thread):
	def run(self):
		def _print(text):
			global _lastprint
			if _lastprint=="input":
				delete_last_line()
				print(text)
				print(_textinput(len(_changed)), _line)
			else:
				print(text)
				_lastprint = "programm"
		
		global _changed, _lastmodify, mewnbase_de, checks_delay
		while True:
			time.sleep(checks_delay)
			if _stop:
				exit()
			for root, dirs, files in os.walk(mewnbase_de):
				for file in files:
					if file[-5:] == '.java':
						file_path = os.path.join(root, file)
						check=os.path.getmtime(file_path)
						if file_path not in _lastmodify:
							_lastmodify[file_path] = 0
						if _lastmodify[file_path] != check:
							_lastmodify[file_path] = check
							if file_path not in _changed:
								_changed.append(file_path)
							_print(f"modified file: {file_path}")

def delete_last_line():
    sys.stdout.write('\x1b[1A')
    sys.stdout.write('\x1b[2K')

inputThread = InputThread()
changesThread = ChangesThread()
inputThread.start()
changesThread.start()
