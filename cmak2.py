#!python

import re
import os
import sys
import argparse
import glob
import datetime
from argparse import RawTextHelpFormatter

VERSION = '2.7.0 (1/2019)'


class HandleFiles(object) :
	def __init__ (self) :
		self.valid_extention = [".c",".cpp",".cxx",".cc"]
		self.cpp_file_list = []
		self.cpp_source = 0
		self.include_path_list = []

	def cpp_file(self, filename):
		''' Check if we have a .c/.cpp file and store it '''	
		if not(os.path.exists(filename)):
			print ('File "%s" does not exists...\n' % (filename,))
			sys.exit(1)
   
		ext = os.path.splitext(filename)[-1]
		invalid_extention = 1
    
		if ext in self.valid_extention :
			invalid_extention = 0
			self.cpp_source = (0 if (ext == '.c') else 1)

		if invalid_extention == 1 :
			print('File %s don\'t have valid c/c++ extension. --> %s' % (filename,ext))
		else:
			print('Adding file : %s'%(filename))
			self.cpp_file_list.append(filename)


	def handle_file_list(self, file_list, dir='') :
		''' Get a file list and ask to check them or go in sub dir '''
		for value in file_list :
			if ((value != '.') and (value != '..')):
				if dir == '' :	mypath = value
				else : 			mypath = '%s/%s' % (dir, value)

				if os.path.isdir(mypath) :
					self.find_dir_files(mypath)
				else:					
					self.cpp_file(mypath)

	def find_dir_files(self, dir):
		''' determine if we have a file, a directory or a pattern and do the appropriate job'''
		print("Analysing file/dir : %s\n"%(dir))

		# handle single file
		if os.path.isfile(dir):
			self.cpp_file(dir)
			return

		# handle directory
		if os.path.isdir(dir) :
			self.include_path_list.append(dir)
			file_list = os.listdir (dir)

			self.handle_file_list(file_list, dir)

		# handle patterns
		if dir.find("*") != -1 :
			file_list = glob.glob(dir)

			self.handle_file_list(file_list)


class HandleConfig (object) :
	''' Lets play with Config File '''
	def __init__(self) :
		self.cmak_header_list=[]
		self.cmak_ldflags_list=[]
		self.cmak_cflags_list=[]

		self.loaded = 0

	def checkCfg(self, path) :
		if self.loaded == 0 :
			print('Trying %s'%(path))

		if os.path.exists(path) :
			self.load_cmak_cfg_ex(path)
			self.loaded = 1
			print('Config File Found : %s'%(path))

	def load_cmak_cfg(self):
		
		if (self.cmak_cfg != ''):
			self.checkCfg(self.cmak_cfg)

		self.checkCfg('./cmak2.cfg')
		self.checkCfg(os.path.dirname(__file__) + '/cmak2.cfg')

		if self.cmak_defined('unix') or self.cmak_defined('morphos'):
			self.checkCfg('/etc/cmak2.cfg')
			self.checkCfg('/usr/share/cmak/cmak2.cfg')
			self.checkCfg('usr:share/cmak/cmak2.cfg')
		else:
			if self.cmak_defined('win32'):
				self.checkCfg('c:\\cmak2.cfg')

		if (self.loaded == 0):
			print("cmak2.cfg configuration file can't be found ...\n")
			sys.exit(1)
			
			
	def load_cmak_cfg_ex(self, cmak_filename):
		known_cmds = ['', 'ifdef', 'endif', 'define', 'header', 'cflags_default', 'ldflags_default']

		print ('Reading configuration file %s\n' % (cmak_filename,))
		line = 0
		ifdef_list = []
		ignore_cmd = 0
		fp = open(cmak_filename, 'r')

		if not fp : 
			print ("Error when opeing file %s\n" % (cmak_filename,))
			sys.exit(2)
    
		for l in fp :
			line_str = l
			line = line + 1
			
			l = re.sub(r'\#.*$', '', l)
			l = l.strip ()
			command = l
			arg = l

			command = re.sub(r'^([^\s]*).*$', r'\1', command)
			command = command.rstrip()

			arg = re.sub(r'^[^\s]*', '', arg)
			arg = arg.strip()

			if command not in known_cmds :
				self.cmak_error(cmak_filename, line, line_str, 'Unknown Command')

			if (command == ''):
				continue
				
			if (command == 'ifdef'):
				ignore_cmd = (0 if self.cmak_defined(arg) else 1)
				ifdef_list.append(arg)
				continue
			
			if (command == 'endif'):
				ifdef_count = len(ifdef_list)
				arg = re.search('[^\s].*', arg)
				if arg :
					self.cmak_error(cmak_filename, line, line_str, "endif accept no arguments.")
				if (ifdef_count <= 0):
					self.cmak_error(cmak_filename, line, line_str, 'endif is declared without ifdef.')
				ifdef_list.pop()
				ignore_cmd = 0
				if (len(ifdef_list) > 0):
					ignore_cmd = (1 if self.cmak_defined(ifdef_list[(len(ifdef_list) - 1)]) else 0)
				continue
			else:
				if (ignore_cmd == 1):
					continue
				else:
					if (command == 'define'):
						self.cmak_define(arg)
						continue

					if (command == 'header'):
						table = arg.split(':')
						if ((len(table) > 3) or (len(table) < 2)):
							self.cmak_error(cmak_filename, line, line_str, '"header" command only accept 2 or 3 arguments.')
						arg_header = table[0]
						arg_ldflags = table[1]
						arg_cflags = ''
						if len(table) > 2 :
							arg_cflags = table[2]

						arg_header = arg_header.strip()
						arg_ldflags = arg_ldflags.strip() 
						arg_cflags = arg_cflags.strip() 

						self.cmak_header_list.append(arg_header)
						self.cmak_ldflags_list.append(arg_ldflags)
						self.cmak_cflags_list.append(arg_cflags)
						continue		

					if command == 'cflags_default' :
						table = arg.split(':')
						self.cflags = self.cflags + table[1]
						continue

					if command == 'ldflags_default' :
						table = arg.split(':')
						self.ldflags = self.ldflags + table[1]
						continue

	def cmak_error(self, cmak_filename, line, line_str, explication):
		print ('Error in file %s\n' % (cmak_filename,))
		print ('Line:        %s\n' % (line,))
		print ('Content:     %s\n' % (line_str.strip(),))
		if (explication != ''):
			print ('Reason: %s\n' % (explication,))
		sys.exit(10)

	def cmak_define(self, bla):
		if type(bla) is list :
			self.define.extend(bla)
		else :
			self.define.append(bla)

	# peut etre remplacee par in 
	def cmak_defined(self, const):
		if const in self.define :
			return 1
		return 0

class HandleMain(object) :
	''' Try to find main function and use cpp filename as executable name '''
	def __init__ (self) :
		zz=''

	def auto_detect_main(self):
		if (self.executable != ''):
			return
		print('Search for "main" function...\n')

		map(self.detect_main, self.cpp_file_list)

	def detect_main(self,filename):
		print ('Scanning file "%s"...\n' % (filename,))
		fp = open(filename, 'r')
		content = fp.read()
		fp.close()

		if self.test_main(filename, content) == 1:
			self.executable = os.path.basename(delext(filename))
			print("Executable : %s"%(self.executable))
			return 1
		return 0

	def test_main(self, filename, line_str):
		if re.search('main([ ]*|)\(', line_str):
			print(('FOUND main in %s' % (filename,)))
			return 1
		return 0


class HandleLib(object) :
	''' Try to find lib files to add to cflags and ldflags'''
	def __init__ (self) :
		self.visited_header_list=[]
	
	def auto_detect_lib(self):
		''' check all files '''
		for  value in self.cpp_file_list:
			print("file: "+value)
			self.detect_lib(value, 0, 0)
	
	def search_header(self, filename):
		''' try to find headers '''
		for value in self.include_path_list:
			if os.path.exists(('%s/%s' % (value, filename))):
				return ('%s/%s' % (value, filename))
		if os.path.exists(('/usr/include/%s' % (filename,))):
			return ('/usr/include/%s' % (filename,))
		if 'linux' in self.define:
			if os.path.exists(('/usr/include/linux/%s' % (filename,))):
					return ('/usr/include/linux/%s' % (filename,))
		if os.path.exists(('/usr/local/include/%s' % (filename,))):
			return ('/usr/local/include/%s' % (filename,))
		return filename

	def get_include(self, line_str) :
		''' find include name in line '''
		include = line_str.strip()
		include = re.sub(r'^\s*\#include\s*["<]', '', include)
		include = re.sub(r'[">].*$', '', include)

		return include

	def find_flags(self, include, filename) :
		i = 0
		for value in self.cmak_header_list:
			if include.startswith(value):
				if (len(self.cmak_cflags_list)>= i and (self.cmak_cflags_list[i] != '')):
					self.cflags = self.cflags+ ' %s'%(self.cmak_cflags_list[i],)
					print ('File %s contains %s so CFLAGS.=%s\n' % (filename, include, self.cmak_cflags_list[i]))
					self.cmak_cflags_list[i] = ''
				if (len(self.cmak_ldflags_list)>=i and (self.cmak_ldflags_list[i] != '')):
					self.ldflags = self.ldflags+ ' %s' % (self.cmak_ldflags_list[i],)
					print ('File %s contains %s so LDFLAGS.=%s\n' % (filename, include, self.cmak_ldflags_list[i]))
					self.cmak_ldflags_list[i] = ''

				i = -1
				break

			i = (i + 1)

		return i

	def already_visited_header(self, filename) :
		if filename in self.visited_header_list :
			print ('IGNORE: file %s already scanned\n' % (filename,))
			return True

		self.visited_header_list.append(filename)
		return False

	def detect_lib(self, filename, recursive_lvl=0, ignore_error=0):
		''' auto detect libs and includes to put in flags '''

		if self.verbose:
				print ('   %s' % (recursive_lvl,))
				print ('"%s"\n' % (filename,))

		if self.already_visited_header(filename) :
			return 1

		if (recursive_lvl >= 16):
			return 0

		filename = self.search_header(filename)

		if os.path.exists(filename) :
			fp = open(filename, 'r')
		else :
			print ("Error when opening file %s ...\nAdd path for includes with option -I or --include-dir\n" % (filename,))
			if not(ignore_error):
				# Removed this exit, shall we really exit here ?
				# sys.exit(1)
				pass
			return 1

		for line_str in fp:
			if line_str.find('#include') != -1:
				include = self.get_include(line_str)
				i = self.find_flags(include, filename)

				if (i != -1):
					ignore = 0
					line_str = re.search(r'\#include.*<.*>' , line_str)

					if line_str != None :
						ignore = 1

					self.detect_lib(include, (recursive_lvl + 1), ignore)
			else:
				if (recursive_lvl == 0):
					if HandleMain().test_main(filename, line_str):
						executable = os.path.basename(delext(filename))



class HandleInteractive (object) :
	def __init__ (self) :
		zz = ''

	def interactive_mode(self):
		if (self.interactive != 0):
			self.makefile = self.cmak_prompt('Makefile name', self.makefile)
			self.executable = self.cmak_prompt('Executable name', self.executable)

	def cmak_prompt(self, question, default):
		ret = raw_input(question+'\n')
		print(ret)
		if ret == '' :
			ret = default
		return ret


class HandleMakefile(object) :
	def __init__ (self) :
		self.cc = 'gcc:g++'

	def getCC(self) :
		mysplit = self.cc.split(':')

		if self.cpp_source:	ret = mysplit[1]
		else:	ret = mysplit[0]

		return ret

	def create_makefile(self):
		global VERSION
 
		if self.executable == '' :
			self.executable = 'main'

		self.cc=self.getCC()
		i = datetime.datetime.now()

		if self.debug :
			if self.cpp_source :
				self.cflags = "-g -Wall "+self.cflags 
				self.ldflags = "-Wl, --traditional-format " + self.ldflags
				debug_string = "objdump --source --line-numbers --demangle --syms --reloc --disassemble-all "
			else :
				debug_string = "objdump --syms --reloc --disassemble-all "

		if self.optimize :
			self.cflags = "-O2 "+self.cflags

		if self.full_optimize :
			self.cflags = "-O3 "+self.cflags
			# remove unused functions
			# self.ldflags = " -Wl, --gc-sections "+self.ldflags
        
		print ('Creating file "%s"...\n' % (self.makefile,))
		fp = open(self.makefile, 'w')
		fp.write('#--------------------------------------------------------------\n')
		fp.write(('# Makefile generated with cmak2.py version %s.\n' % (VERSION,)))
		fp.write(('# Date: %s/%s/%s%s' % (i.day, i.month, i.year, (' %s:%s:%s\n' % (i.hour, i.minute, i.second)))))
		fp.write('# Dirty port from Original cmak perl script by SixK\n')
		fp.write('#--------------------------------------------------------------\n\n')
		fp.write('PREFIX  = /usr/local\n')
		fp.write(('CFLAGS  = %s\n' % (self.cflags,)))
		fp.write(('LDFLAGS = %s\n\n' % (self.ldflags,)))
		fp.write(('CC = %s\n' % (self.cc,)))
		fp.write('RM = rm -f\n')
		fp.write('INSTALL_PROG = install -m 755 -s\n\n')
		fp.write(('EXE = %s\n' % (self.executable,)))
		exe_base = os.path.basename(self.executable)
		if (exe_base != self.executable):
			fp.write(('EXE_BASE = %s\n\n' % (exe_base,)))
		else:
			fp.write('\n')

		if self.debug :	
			fp.write('DEBUG = $(EXE).dump\n')
        
		if self.egypt :
			fp.write('EGYPT = $(EXE).svg\n')

		fp.write('OBJS =')    
		for value in self.cpp_file_list:
			fp.write(' ')
			if (self.objdir != ''):
				fp.write('%s/' % (self.objdir,))
			print("File found : %s"%(value))

			if (value[0:1] == '/'):
				value = value[1: 1+len(value)]
			fp.write('%s.o' % (delext(value),))
    
		fp.write('\n\nALL : $(EXE)\n\n')
    
		for value in self.cpp_file_list:
			# value = value.replace(default_path, '')
			if (value[0:1] == '/'):
				value = value[1: 1+ len(value)]
			obj = ('%s.o' % (delext(value),))
			if (self.objdir != ''):
				obj = ('%s/%s' % (self.objdir, obj))
			fp.write('%s : %s\n' % (obj, value))
			fp.write('\t$(CC) -c %s $(CFLAGS) -o %s\n\n' % (value, obj))
        
		fp.write('$(EXE) : $(OBJS)\n')
		fp.write('\t$(CC) $(OBJS) -o $(EXE) $(LDFLAGS)\n\n')
		fp.write('\tstrip $(EXE)\n\n')
		if 'unix' in self.define :
			fp.write('install : $(EXE)\n')
			fp.write('\t$(INSTALL_PROG) $(EXE) $(PREFIX)/bin\n\n')
		fp.write('uninstall :\n')
		if (self.executable != exe_base):
			fp.write('\t$(RM) $(PREFIX)/bin/$(EXE_BASE)\n\n')
		else:
			fp.write('\t$(RM) $(PREFIX)/bin/$(EXE)\n\n')
		fp.write('clean :\n')
		fp.write('\t$(RM) $(OBJS) $(EXE) $(DEBUG) $(EGYPT)')

		if self.debug :
			fp.write('\n\ndebug :\n')
			fp.write('\t%s $(EXE) > $(DEBUG)'%(debug_string))

		if self.egypt == True :
			fp.write('\n\negypt :\n')
			fp.write('\tegypt *.expand | dot -Tsvg -o $(EGYPT)')

		fp.close()
        
        
class HandleArgs(object) :
	def __init__(self) :
		self.default_path = ''
		self.makefile = 'Makefile'
		self.vdetect_lib = 0
		self.verbose = 0
		self.interactive = 0
		self.executable = ''
		self.ldflags = ''
		self.cflags = ''
		self.objdir = ''
		self.cmak_cfg = ''
		self.include_path_list = []
		self.egypt = False
		self.file_dir_name = ''
		self.debug = 0
        
	def handleMenuArgs(self):
		global VERSION

		parser = argparse.ArgumentParser(description="cmak version %s, Automatic Makefile Generator\n"
													"	Author: Achraf cherti <achrafcherti@gmail.com>\n"
													"	Ported to PHP by SixK (Dirty Port with bugs)\n"
													"	Ported to Python by SixK (Still Dirty but with less bugs)"%(VERSION), formatter_class=RawTextHelpFormatter)
		parser.add_argument("-v", "--verbose",  action="store_true", help="More informations")
		parser.add_argument("--version",  action="version", version="Version : "+VERSION, help="Print software version")
		parser.add_argument("-dl", "--detect-lib",  action="store_true", help="Autodetect libraries \n"
																				"based on headers found in source code. \n"
																				"Edit cmak2.cfg file to \n"
																				"customise this detection")
		parser.add_argument("--cfg", help="Select manualy Path for cmak2.cfg")
		parser.add_argument("-od", "--obj-dir", help="Directory for .o files")
		parser.add_argument("-I", "--include-dir", nargs="*", help="Can be defined several times. \n"
																	"Tell where to find .h files")
																	
		parser.add_argument("-L", "--lib-dir", nargs="*", help="Can be defined several times. \n"
																"Tell where to find .a libraries")
		parser.add_argument("-LD", "--ldflags", nargs="*", help="Add to LDFLAGS an option (can be defined several times)")
		parser.add_argument("-C", "--cflags", nargs="*", help="Add to CFLAGS an option (can be defined several times)")
		parser.add_argument("-e", "--executable", help="Executable name after link")
		parser.add_argument("-m", "--makefile", help="Makefile name (default 'Makefile')")
		parser.add_argument("-i", "--interactive", action="store_true", help="Interactive Mode (Prompt Values)")
		parser.add_argument("-o", "--optimize", action="store_true", help="Add gcc Optimisation -O2")
		parser.add_argument("-fo", "--full-optimize", action="store_true", help="Add gcc Optimisations -O3, strip, ...")
		parser.add_argument("-d", "--debug", action="store_true", help="Add debug parameters to Makefile")
		parser.add_argument("-eg", "--egypt", action="store_true", help="Parameter to use egypt, a call graph perl script\nDownload here : http://www.gson.org/egypt/ ")
		parser.add_argument("filename", type=str, nargs='+')
		args = parser.parse_args()

		# get filename or directory	
		if len(args.filename) :
			self.file_dir_name = args.filename[0]

		# interactive
		self.interactive = args.interactive

		# auto detect libs
		self.vdetect_lib = args.detect_lib

		# verbose
		self.verbose = args.verbose

		# debug
		self.debug = args.debug

		# optimize
		self.optimize = args.optimize

		#full optimize
		self.full_optimize = args.full_optimize

		# cfg file
		if args.cfg != None :
			self.cmak_cfg = args.cfg

		# objdir
		if args.obj_dir != None :
			self.objdir = args.obj_dir

		# include path
		if args.include_dir != None :
			self.include_path_list.append(args.include_dir)

		# cflags
		if args.cflags != None :
			self.cflags = self.cflags + " ".join(args.cflags)

		#ldflags
		if args.ldflags != None :
			self.ldflags = self.ldflags + " ".join(args.ldflags)

		# executable
		if args.executable != None :
			self.executable = args.executable
	
		# makefile	
		if args.makefile != None :
			self.makefile = args.makefile

		# egypt
		if args.egypt == True :
			self.egypt = True
			self.cflags = self.cflags + " -fdump-rtl-expand "


class MetaClass(HandleArgs, HandleConfig, HandleLib, HandleMain, HandleInteractive, HandleMakefile, HandleFiles) :
	''' MetaClass, a class to call all other classes and share variables and functions '''
	def __init__(self) :
		# Todo : Auto detect system
		# self.define = ['gcc', 'morphos']
		self.define = ['gcc', 'unix']

		HandleArgs.__init__(self)
		HandleFiles.__init__(self)

		HandleInteractive.__init__(self)
		HandleMakefile.__init__(self)

		self.handleMenuArgs()
		self.find_dir_files(self.file_dir_name)
		if self.vdetect_lib == True :
			HandleConfig.__init__(self)
			HandleLib.__init__(self)

			self.load_cmak_cfg()
			self.auto_detect_lib()
		else :
			HandleMain.__init__(self)
			self.auto_detect_main()

		self.interactive_mode()	
		self.create_makefile()


def delext(filename):
	return os.path.splitext(filename)[0]

# singleton or something like that
go=MetaClass()
