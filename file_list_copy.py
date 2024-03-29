import re
import sys
import os
import time
from datetime import date, timedelta
import shutil

from PyQt5 import QtGui, QtCore, uic, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from functools import partial


app = None


def main():
	global app
	app = QApplication(sys.argv)
	ex = Program()
	sys.exit(app.exec_())


# Primary program. Sorts files, provides GUI
class Program(QMainWindow):
	def __init__(self):
		super(Program, self).__init__()

		# Set a few variables used for settings and counting progress
		self.working = False
		self.filesCopied = 0
		self.filesSkipped = 0
		self.correctForZulu = 1
		self.mode = 'list'			# one of 'copy', 'list', 'test subset'

		# set central layout and some default window options
		self.mainWidget = QWidget()
		self.setCentralWidget(self.mainWidget)
		self.setGeometry(250, 400, 600, 200)
		self.setWindowTitle('File list tool - {} mode'.format(self.mode))

		self.mainLayout = QVBoxLayout()
		self.mainWidget.setLayout(self.mainLayout)

		# Add mode toggle button
		self.toggleModeLayout = QHBoxLayout()
		self.toggleModeBtn = QPushButton("Toggle Mode")
		self.toggleModeBtn.clicked.connect(self.toggle_mode)
		self.toggleModeLayout.addWidget(self.toggleModeBtn)
		self.toggleModeLayout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
		self.mainLayout.addLayout(self.toggleModeLayout)

		# Add text lines and buttons for selecting the folders
		# Also link the functions to keep them in sync, and to verify that the paths exist
		self.inpathBox = QLineEdit("")
		self.inpathBtn = QPushButton("Browse")
		self.inpathBtn.clicked.connect(partial(self.select_path, self.inpathBox))
		self.inpathBox.textChanged.connect(self.verify_paths)

		inpathLayout = QHBoxLayout()
		inpathLayout.addWidget(QLabel("File source path       "))
		inpathLayout.addWidget(self.inpathBox)
		inpathLayout.addWidget(self.inpathBtn)
		self.mainLayout.addLayout(inpathLayout)

		self.filepathBox = QLineEdit("")
		self.filepathBtn = QPushButton("Browse")
		self.filepathBtn.clicked.connect(partial(self.select_path, self.filepathBox))
		self.filepathBox.textChanged.connect(self.verify_paths)

		filepathLayout = QHBoxLayout()
		filepathLayout.addWidget(QLabel("File list path             "))
		filepathLayout.addWidget(self.filepathBox)
		filepathLayout.addWidget(self.filepathBtn)
		self.mainLayout.addLayout(filepathLayout)

		self.outpathBox = QLineEdit("")
		self.outpathBtn = QPushButton("Browse")
		self.outpathBtn.clicked.connect(partial(self.select_path, self.outpathBox))
		self.outpathBox.textChanged.connect(self.verify_paths)

		outpathLayout = QHBoxLayout()
		outpathLayout.addWidget(QLabel("File destination path"))
		outpathLayout.addWidget(self.outpathBox)
		outpathLayout.addWidget(self.outpathBtn)
		self.mainLayout.addLayout(outpathLayout)

		self.outpathBtn.setEnabled(False)
		self.outpathBox.setEnabled(False)

		# Add bar for bottom buttons
		self.controlsWidget = QWidget()
		self.controlsLayout = QHBoxLayout()
		self.controlsWidget.setLayout(self.controlsLayout)
		self.mainLayout.addWidget(self.controlsWidget)

		# Add the button to transfer the files
		self.startBtn = QPushButton("Start copy")
		self.startBtn.setEnabled(False)		# Need inpath/outpath before button is enabled
		self.startBtn.clicked.connect(self.start_operation)
		self.controlsLayout.addWidget(self.startBtn)

		self.show()

	# Switches between list and copy modes
	def toggle_mode(self):
		if self.mode == 'list':
			self.mode = 'copy'
		elif self.mode == 'copy':
			self.mode = 'test subset'
		else:
			self.mode = 'list'
		self.setWindowTitle(format('File list tool - %s mode' % self.mode))
		self.verify_paths()

		if self.mode == 'list':
			self.outpathBtn.setEnabled(False)
			self.outpathBox.setEnabled(False)
			self.filepathBox.setEnabled(True)
			self.filepathBtn.setEnabled(True)
		elif self.mode == 'copy':
			self.outpathBtn.setEnabled(True)
			self.outpathBox.setEnabled(True)
			self.filepathBox.setEnabled(True)
			self.filepathBtn.setEnabled(True)
		else:
			self.outpathBtn.setEnabled(True)
			self.outpathBox.setEnabled(True)
			self.filepathBox.setEnabled(False)
			self.filepathBtn.setEnabled(False)

	# Method for combining lineEdit and fileSelect methods of getting the path
	def select_path(self, lineEdit):
		folder = QFileDialog.getExistingDirectory(self, "Select Directory")
		if folder:
			lineEdit.setText(str(folder))

	# Checks whether the required folders exist.
	# Enables and disables the sort button based on this, and places feedback on it
	def verify_paths(self):
		inExists = os.path.isdir(str(self.inpathBox.text()))
		fileExists = os.path.isdir(str(self.filepathBox.text()))
		outExists = os.path.isdir(str(self.outpathBox.text()))
		if self.mode == 'list':
			if not inExists:
				self.startBtn.setEnabled(False)
				self.startBtn.setText("Requires a valid input folder")
			elif not fileExists:
				self.startBtn.setEnabled(False)
				self.startBtn.setText("Requires a valid folder for output list")
			else:
				self.startBtn.setEnabled(True)
				self.startBtn.setText("Create list")
		elif self.mode == 'copy':
			if not inExists:
				self.startBtn.setEnabled(False)
				self.startBtn.setText("Requires a valid input folder")
			elif not fileExists:
				self.startBtn.setEnabled(False)
				self.startBtn.setText("Requires a valid list of files")
			elif not outExists:
				self.startBtn.setEnabled(False)
				self.startBtn.setText("Requires an output folder")
			else:
				self.startBtn.setEnabled(True)
				self.startBtn.setText("Copy files in list")
		elif self.mode == 'test subset':
			if not inExists:
				self.startBtn.setEnabled(False)
				self.startBtn.setText("Requires a valid input folder")
			elif not outExists:
				self.startBtn.setEnabled(False)
				self.startBtn.setText("Requires a destination folder")
			else:
				self.startBtn.setEnabled(True)
				self.startBtn.setText("Test if destination is a subset of source")
		else:
			self.startBtn.setEnabled(False)
			self.startBtn.setText("Program mode not recognized")

	def start_operation(self):
		if self.mode == 'list':
			self.start_build_file_list()
		elif self.mode == 'copy':
			self.start_copy_from_list()
		elif self.mode == 'test subset':
			self.start_verify_folders()
		else:
			# should never get here
			print("Mode error. Please restart this tool")

	# ---------------------------------------------------------------------------

	def start_build_file_list(self):
		global app
		src = str(self.inpathBox.text())
		dst = str(self.filepathBox.text())
		if not os.path.isdir(src) or not os.path.isdir(dst):
			print("Warning: source or list path not a folder. Cancelling list operation")
			return

		self.statusBar().showMessage("Building lists...")
		app.processEvents()
		filecount = self.build_file_list(src, dst)
		self.statusBar().showMessage("Finished creating lists of %d files" % filecount)

	def build_file_list(self, srcPath, listPath):
		fileCount = 0
		if not os.path.exists(listPath):
			os.makedirs(listPath)
		listName = os.path.join(listPath, "filelist.txt")
		with open(listName, 'w+') as fileList:
			for filename in os.listdir(srcPath):
				filepath = os.path.join(srcPath, filename)
				if os.path.isdir(filepath):
					fileCount += self.build_file_list(filepath, os.path.join(listPath, filename))
				else:
					shortFilename = self.parse_filename(filename)
					fileList.write(shortFilename)
					fileList.write('\n')
					fileCount += 1

		# Remove empty list files (i.e. a folder is either empty or only contains subfolders)
		if os.stat(listName).st_size == 0:
			os.remove(listName)
		return fileCount

	# ---------------------------------------------------------------------------

	def start_copy_from_list(self):
		src = str(self.inpathBox.text())
		list = str(self.filepathBox.text())
		dst = str(self.outpathBox.text())
		if not os.path.isdir(src) or not os.path.isdir(list) or not os.path.isdir(dst):
			print("Warning: source, list, or destination path not a folder. Cancelling build operation")
			return

		self.copy_from_list(src, list, dst)

	def copy_from_list(self, srcPath, listPath, dst):
		global app
		table = {}
		self.statusBar().showMessage('Searching input files...')
		app.processEvents()
		self.create_hash(table, srcPath)
		self.statusBar().showMessage('Created hashmap. Working on copy...')
		app.processEvents()
		skipped, copied, missing = self.iterate_through_list(listPath, table, dst)
		self.statusBar().showMessage('done build operation. %d copied, %d skipped, %d missing' % (copied, skipped, missing))

	def create_hash(self, table, path):
		for filename in os.listdir(path):
			filepath = os.path.join(path, filename)
			shortFilename = self.parse_filename(filename)
			if os.path.isdir(filepath):
				self.create_hash(table, filepath)
			else:
				if shortFilename not in table:
					table[shortFilename] = (filepath, )
				# Handle multiple files with the same filename
				else:
					li = list(table[shortFilename])
					li.append(filepath)
					table[shortFilename] = tuple(li)

	def iterate_through_list(self, listPath, table, dst):
		skipped, copied, missing = 0, 0, 0
		for filename in os.listdir(listPath):
			filepath = os.path.join(listPath, filename)
			if filename.startswith("filelist.txt"):
				if not os.path.exists(dst):
					os.makedirs(dst)
				s, c, m = self.build_folder(filepath, dst, table)
				skipped += s
				copied += c
				missing += m
			elif os.path.isdir(filepath):
				s, c, m = self.iterate_through_list(filepath, table, os.path.join(dst, filename))
				skipped += s
				copied += c
				missing += m
		return skipped, copied, missing

	def build_folder(self, fileList, dst, table):
		skipped = 0		# files already present
		copied = 0		# files copied
		missing = 0		# files that could not be found to copy
		with open(fileList, 'r') as infile:
			for filename in infile.readlines():
				filename = filename.strip()
				if os.path.exists(os.path.join(dst, filename)):
					skipped += 1
				elif filename in table:
					if len(table[filename]) == 1:
						self.move_file(table[filename][0], os.path.join(dst, filename))
					else:
						# TODO: check the paths to decide which one to use
						# TODO: for now, just pick the first one
						self.move_file(table[filename][0], os.path.join(dst, filename))
					copied += 1
				else:
					missing += 1
		return skipped, copied, missing

	# TODO: add option to move
	def move_file(self, src, dst):
		global app
		shutil.copy2(src, dst)
		app.processEvents()

# --------------------------------------------------

	def start_verify_folders(self):
		src = str(self.inpathBox.text())
		dst = str(self.outpathBox.text())
		if not os.path.isdir(src) or not os.path.isdir(dst):
			print("Warning: source or destination path not a folder. Cancelling verify operation")
			return

		self.verify_folders(src, dst)

	def verify_folders(self, src, dst):
		global app
		table = {}
		self.statusBar().showMessage('indexing source files...')
		app.processEvents()

		self.create_hash(table, src)
		self.statusBar().showMessage('Created hashmap. Working on verify...')
		app.processEvents()

		present, missing = self.verify_folder(table, dst, 0, 0)
		if missing == 0:
			self.statusBar().showMessage("Safe: all {} files in destination found in source".format(present))
		else:
			self.statusBar().showMessage("NOT SAFE: {} files found, {} files missing".format(present, missing))

	def verify_folder(self, table, toCheck, present, missing):
		for filename in os.listdir(toCheck):
			filepath = os.path.join(toCheck, filename)
			if os.path.isdir(filepath):
				present, missing = self.verify_folder(table, filepath, present, missing)
				continue

			shortFilename = self.parse_filename(filename)
			if shortFilename in table:
				present += 1
			else:
				missing += 1

			if present + missing % 100 == 0:
				self.statusBar().showMessage('Working... %d found, %d missing' % (present, missing))
				app.processEvents()

		return present, missing

# --------------------------------------------------

	# Extracts a filename out of brackets.
	# example: somePicture(originalName).jpg -> originalName.jpg
	def parse_filename(self, filename):
		m = re.search(r"\((.{5}.*)\)\.", filename)
		if not m:
			return filename
		return self.parse_filename(m.group(1) + '.jpg')

# --------------------------------------------------


# Run the program
if __name__ == '__main__':
	main()
