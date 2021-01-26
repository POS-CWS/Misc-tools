import re
import sys
import os
import time
from datetime import date, datetime, timedelta
import shutil

from PyQt5 import QtGui, QtCore, uic, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from functools import partial

startingHour = 14
hoursRotation = (3, 3, 3, 3, 12)
timeWindowSeconds = 3600

osWin = False
if "win" in sys.platform:
	import ctypes
	from ctypes import wintypes
	osWin = True

# Used in the copy_file method. This (and copy_file method) is based on code by Michael Burns:
# https://stackoverflow.com/questions/22078621/python-how-to-copy-files-fast
try:
	O_BINARY = os.O_BINARY
except:
	O_BINARY = 0
READ_FLAGS = os.O_RDONLY | O_BINARY
WRITE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | O_BINARY
BUFFER_SIZE = 128 * 1024

# Determine which version of python we are working with, for the copy method.
py2 = True
if sys.version_info > (3, 0):
	py2 = False

app = None

def main():
	global app
	app = QApplication(sys.argv)
	ex = Program()
	sys.exit(app.exec_())


# Copies a file. Works quickly in Python 2.
# Based on code by Michael Burns:
# https://stackoverflow.com/questions/22078621/python-how-to-copy-files-fast
def copyfile(src, dst):
	global py2, osWin
	if py2 and osWin:
		try:
			fin = os.open(src, READ_FLAGS)
			stat = os.fstat(fin)
			fout = os.open(dst, WRITE_FLAGS, stat.st_mode)
			for x in iter(lambda: os.read(fin, BUFFER_SIZE), ""):
				os.write(fout, x)
		finally:
			try:
				os.close(fin)
			except:
				pass
			try:
				os.close(fout)
			except:
				pass
	# This version allows for python 3 compatibility, but is MUCH slower
	else:
		shutil.copy2(src, dst)


# Primary program. Sorts files, provides GUI
class Program(QMainWindow):
	def __init__(self):
		super(Program, self).__init__()

		# Set a few variables for later
		self.working = False

		# set central layout and some default window options
		self.mainWidget = QWidget()
		self.setCentralWidget(self.mainWidget)
		self.setGeometry(400, 250, 800, 200)
		self.setWindowTitle('Image Sampler')

		self.mainLayout = QVBoxLayout()
		self.mainWidget.setLayout(self.mainLayout)

		self.locWidget = QWidget()
		self.locLayout = QGridLayout()
		self.locWidget.setLayout(self.locLayout)
		self.mainLayout.addWidget(self.locWidget)

		# Add text lines and buttons for selecting the folders
		# Also link the functions to keep them in sync, and to verify that the paths exist
		self.inpathBox = QLineEdit("")
		self.locLayout.addWidget(self.inpathBox, 1, 0)
		self.inpathBtn = QPushButton("Select source folder")
		self.inpathBtn.clicked.connect(partial(self.select_path, self.inpathBox))
		self.inpathBox.textChanged.connect(self.verify_paths)
		self.locLayout.addWidget(self.inpathBtn, 0, 0)

		self.outpathBox = QLineEdit("")
		self.locLayout.addWidget(self.outpathBox, 1, 1)
		self.inpathBtn = QPushButton("Select destination folder")
		self.inpathBtn.clicked.connect(partial(self.select_path, self.outpathBox))
		self.outpathBox.textChanged.connect(self.verify_paths)
		self.locLayout.addWidget(self.inpathBtn, 0, 1)

		# Add bar for bottom buttons
		self.controlsWidget = QWidget()
		self.controlsLayout = QHBoxLayout()
		self.controlsWidget.setLayout(self.controlsLayout)
		self.mainLayout.addWidget(self.controlsWidget)

		# Add the button to transfer the files
		# Initially, this is inactive since we need the user to select inpath/outpath first
		self.sampleBtn = QPushButton("Start sample")
		self.sampleBtn.setEnabled(False)
		self.sampleBtn.clicked.connect(self.start_scan)
		self.controlsLayout.addWidget(self.sampleBtn)

		self.show()

	# Method for combining lineEdit and fileSelect methods of getting the path
	def select_path(self, lineEdit):
		folder = QFileDialog.getExistingDirectory(self, "Select Directory")
		if folder:
			lineEdit.setText(str(folder))

	# Checks whether the inpath and outpath exists.
	# Enables and disables the sort button based on this, and places feedback on it
	def verify_paths(self):
		inExists = os.path.exists(str(self.inpathBox.text()))
		outExists = os.path.exists(str(self.outpathBox.text()))
		if not inExists and not outExists:
			self.sampleBtn.setEnabled(False)
			self.sampleBtn.setText("Need inpath and outpath")
		elif not inExists:
			self.sampleBtn.setEnabled(False)
			self.sampleBtn.setText("Need inpath")
		elif not outExists:
			self.sampleBtn.setEnabled(False)
			self.sampleBtn.setText("Need outpath")
		else:
			if not self.working:
				self.sampleBtn.setEnabled(True)
			self.sampleBtn.setText("Start sample")

	def start_scan(self):
		fileList = []
		self.statusBar().showMessage("Starting search...")
		inpath, outpath = str(self.inpathBox.text()), str(self.outpathBox.text())
		self.scan_folder(inpath, fileList)
		if len(fileList) == 0:
			self.statusBar().showMessage("No image files recognized.")
			return

		self.statusBar().showMessage("Sorting files...")
		fileList.sort()

		self.statusBar().showMessage("Calculating subset...")
		fileListFinal = self.get_subset(fileList)

		self.statusBar().showMessage("Copying results...")
		self.copy_results(fileListFinal, outpath)
		self.statusBar().showMessage("Done. " + str(len(fileListFinal)) + " files copied.")

	# recursively searches a folder for images
	def scan_folder(self, path, fileList):
		for filename in os.listdir(path):
			filepath = os.path.join(path, filename)

			# Recurse on all folders
			if os.path.isdir(filepath):
				self.scan_folder(filepath, fileList)
				continue

			fileTime = get_file_time(filepath)
			if fileTime:
				fileList.append((filename, fileTime, filepath))

	def get_subset(self, fileList):
		subset = []
		targetDate = fileList[0][1]
		targetDate = datetime(targetDate.year, targetDate.month, targetDate.day, startingHour) - timedelta(hours=24)
		i = 0
		fileListLength = len(fileList)
		while True:
			for nextIncrement in hoursRotation:
				while fileList[i][1] < targetDate:
					i += 1
					if i >= fileListLength:
						return subset
				if fileList[i][1] < targetDate + timedelta(seconds=timeWindowSeconds):
					subset.append(fileList[i])
				targetDate += timedelta(hours=nextIncrement)


	def copy_results(self, fileList, outpath):
		length = str(len(fileList))
		for i, fileItem in enumerate(fileList):
			self.statusBar().showMessage("Copying results... " + str(i) + "/" + length)
			copyfile(fileItem[2], os.path.join(outpath, fileItem[0]))

# Gets the PI timestamp of the image
# Returns a datetime object, accurate to the seconds place
def get_file_time(filePath):
	m = re.search(r'(\d\d\d\d).(\d\d).(\d\d).(\d\d).(\d\d).(\d\d).*', filePath)
	if not m:
		return None
	return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
				 int(m.group(4)), int(m.group(5)), int(m.group(6)))

# --------------------------------------------------


# Run the program
if __name__ == '__main__':
	main()
