from datetime import datetime, timedelta
import sys
import os
import re
import shutil

from PyQt5 import QtGui, QtCore, uic, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


app = None


def main():
	global app
	app = QApplication(sys.argv)
	ex = Program()
	sys.exit(app.exec_())


# https://stackoverflow.com/questions/5671354/how-to-programmatically-make-a-horizontal-line-in-qt
class QHLine(QFrame):
	def __init__(self):
		super(QHLine, self).__init__()
		self.setFrameShape(QFrame.HLine)
		self.setFrameShadow(QFrame.Sunken)


class Program(QMainWindow):
	def __init__(self):
		super(Program, self).__init__()

		# globals for processing
		self.isProcessing = False
		self.totalJPGs = 0
		self.totalToCopy = 0
		self.totalUnknown = 0
		self.numCopied = 0
		self.numSkipped = 0

		self.mmFolders = []
		self.otherFolders = []

		# set central layout and some default window options
		self.mainWidget = QWidget()
		self.setCentralWidget(self.mainWidget)
		self.setGeometry(400, 250, 400, 300)
		self.setWindowTitle('Marine Mammal Image Copier')

		self.mainLayout = QVBoxLayout()
		self.mainWidget.setLayout(self.mainLayout)

		self.pathLayout = QHBoxLayout()
		self.mainLayout.addLayout(self.pathLayout)

		self.pathLayout.addWidget(QLabel('Source:'))
		self.pathBox = QLineEdit("")
		self.pathLayout.addWidget(self.pathBox)
		self.pathBtn = QPushButton("Browse")
		self.pathBtn.clicked.connect(self.select_path)
		self.pathBox.textChanged.connect(self.verify_path)
		self.pathLayout.addWidget(self.pathBtn)

		self.outpathLayout = QHBoxLayout()
		self.mainLayout.addLayout(self.outpathLayout)

		self.outpathLayout.addWidget(QLabel('Destination:'))
		self.outpathBox = QLineEdit("")
		self.outpathLayout.addWidget(self.outpathBox)
		self.outpathBtn = QPushButton("Browse")
		self.outpathBtn.clicked.connect(self.select_outpath)
		self.outpathBox.textChanged.connect(self.verify_path)
		self.outpathLayout.addWidget(self.outpathBtn)

		self.enableCopyBox = QCheckBox("Copy images found")
		self.enableCopyBox.setToolTip("Check to copy all marine mammal images found to the output folder")
		self.enableCopyBox.setChecked(True)
		self.enableListBox = QCheckBox("Create image list")
		self.enableListBox.setToolTip("Check to create a list of all marine mammal images in the output folder\n"
									  "This list can later be copied using the file_list_copy tool")

		self.checkboxLayout = QVBoxLayout()
		self.checkboxLayout.addWidget(self.enableCopyBox)
		self.checkboxLayout.addWidget(self.enableListBox)

		self.startBtnLayout = QHBoxLayout()
		self.startBtnLayout.addLayout(self.checkboxLayout)
		self.startBtnLayout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Fixed))
		self.startBtn = QPushButton("Start")
		self.startBtn.clicked.connect(self.process)
		self.startBtn.setEnabled(False)
		self.startBtnLayout.addWidget(self.startBtn)
		self.mainLayout.addLayout(self.startBtnLayout)

		self.mainLayout.addWidget(QHLine())
		self.infoLabel = QLabel('')
		self.mainLayout.addWidget(self.infoLabel)

		self.mainLayout.addItem(QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Expanding))

		self.load_lists()
		self.show()

	def select_path(self):
		folder = QFileDialog.getExistingDirectory(self, "Select Directory")
		if folder:
			self.pathBox.setText(str(folder))

	def select_outpath(self):
		folder = QFileDialog.getExistingDirectory(self, "Select Destination")
		if folder:
			self.outpathBox.setText(str(folder))

	def verify_path(self):
		if os.path.exists(str(self.pathBox.text())):
			if not self.isProcessing:
				self.startBtn.setEnabled(True)
			self.startBtn.setText('Start')
		else:
			self.startBtn.setEnabled(False)
			self.startBtn.setText('(invalid source path)')

	def update_info_text(self, stillProcessing=True):
		text = '{0} images found\n\t{1} marine mammals\n\t{2} other\n\t{3} unknown\n'.format(
			self.totalJPGs, self.totalToCopy, self.totalJPGs - self.totalToCopy - self.totalUnknown, self.totalUnknown)
		if self.enableCopyBox.isChecked():
			text += '{0} images copied\n{1} images skipped (already in destination folder)\n'.format(
				self.numCopied, self.numSkipped
			)
		text += ('working...' if stillProcessing else 'done.')
		self.infoLabel.setText(text)

	def load_lists(self):
		self.mmFolders = []
		self.otherFolders = []

		with open('marine mammal folders.txt', 'r') as infile:
			for line in infile.readlines():
				if not line.startswith("#"):
					self.mmFolders.append(line.strip())

		with open('other folders.txt', 'r') as infile:
			for line in infile.readlines():
				if not line.startswith("#"):
					self.otherFolders.append(line.strip())

	def process(self):
		self.isProcessing = True
		self.set_gui_locked(True)

		outpath = str(self.outpathBox.text())
		if not os.path.exists(outpath):
			if len(outpath) > 0:
				try:
					os.makedirs(outpath)
				except:
					self.isProcessing = False
					self.startBtn.setEnabled(True)
					self.infoLabel.setText("Error: could not create destination path")
					return

		# Reset summary data
		self.totalJPGs = 0
		self.totalToCopy = 0
		self.totalUnknown = 0
		self.numCopied = 0
		self.numSkipped = 0

		basePath = str(self.pathBox.text())
		listToCopy = []
		self.search(basePath, listToCopy)

		if self.enableListBox.isChecked():
			self.create_output_list(listToCopy, outpath)

		if self.enableCopyBox.isChecked():
			self.copy_from_list(listToCopy, outpath)

		# cleanup
		self.update_info_text(False)

		self.isProcessing = False
		self.set_gui_locked(False)

	# Disables or enables most interactible GUI elements
	def set_gui_locked(self, locked):
		enabled = not locked
		self.startBtn.setEnabled(enabled)
		self.enableListBox.setEnabled(enabled)
		self.enableCopyBox.setEnabled(enabled)

		self.pathBox.setEnabled(enabled)
		self.outpathBox.setEnabled(enabled)

	def search(self, path, toCopy):
		mmFolder, otherFolder = self.determine_folder_type(path)
		for i, filename in enumerate(os.listdir(path)):
			if i % 10 == 0:
				self.update_gui()

			filepath = os.path.join(path, filename)
			# Recurse
			if "." not in filename and os.path.isdir(filepath):
				self.search(filepath, toCopy)
				continue

			# Is picture? consider if we're in a special folder right now
			if filepath.endswith(".jpg"):
				self.totalJPGs += 1
				if mmFolder:
					self.totalToCopy += 1
					toCopy.append(filepath)
				elif not otherFolder:
					self.totalUnknown += 1

	def determine_folder_type(self, path):
		folder = os.path.split(path)[1]
		mmFolder, otherFolder = False, False
		if folder in self.mmFolders:
			mmFolder = True
		elif folder in self.otherFolders or re.search(r"\d", folder):
			otherFolder = True
		else:
			print("unknown folder: {}".format(folder))
		return mmFolder, otherFolder

	def copy_from_list(self, toCopy, dst):
		for file in toCopy:

			newPath = os.path.join(dst, os.path.split(file)[1])

			if os.path.exists(newPath):
				self.numSkipped += 1
				continue

			shutil.copy2(file, newPath)
			self.numCopied += 1
			self.update_gui()

	def update_gui(self):
		global app
		self.update_info_text()
		app.processEvents()

	@staticmethod
	def create_output_list(fileList, outpath):
		with open(os.path.join(outpath, 'filelist.txt'), 'w+') as outfile:
			for filename in fileList:
				outfile.write(os.path.split(filename)[1] + '\n')
		with open(os.path.join(outpath, 'filelist_full_paths.txt'), 'w+') as outfile:
			for filename in fileList:
				outfile.write(filename + '\n')


if __name__ == "__main__":
	main()
