import re
import sys
import os
import time
from datetime import date, timedelta
import shutil

from PyQt5 import QtGui, QtCore, uic, QtWidgets
from PyQt5.QtWidgets import *

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

		# Set a few variables for later
		self.working = False
		self.totalFileCount = 0
		self.fileCounts = []

		# set central layout and some default window options
		self.mainWidget = QWidget()
		self.setCentralWidget(self.mainWidget)
		self.setGeometry(400, 250, 400, 200)
		self.setWindowTitle('File counter')

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
		self.inpathBtn = QPushButton("Select target folder")
		self.inpathBtn.clicked.connect(partial(self.select_path, self.inpathBox))
		self.inpathBox.textChanged.connect(self.verify_paths)
		self.locLayout.addWidget(self.inpathBtn, 0, 0)

		# Add bar for bottom buttons
		self.controlsWidget = QWidget()
		self.controlsLayout = QHBoxLayout()
		self.controlsWidget.setLayout(self.controlsLayout)
		self.mainLayout.addWidget(self.controlsWidget)

		# Add the button to transfer the files
		# Initially, this is inactive since we need the user to select inpath/outpath first
		self.sortBtn = QPushButton("  Start Count  ")
		self.sortBtn.setEnabled(False)
		self.sortBtn.clicked.connect(self.start_count)
		self.controlsLayout.addSpacerItem(build_horizontal_spacer())
		self.controlsLayout.addWidget(self.sortBtn)
		self.controlsLayout.addSpacerItem(build_horizontal_spacer())

		self.show()

	# Method for combining lineEdit and fileSelect methods of getting the path
	def select_path(self, lineEdit):
		folder = QFileDialog.getExistingDirectory(self, "Select Directory")
		if folder:
			lineEdit.setText(str(folder))

	# Checks whether the inpath and outpath exists.
	# Enables and disables the sort button based on this, and places feedback on it
	def verify_paths(self):
		if not os.path.exists(str(self.inpathBox.text())):
			self.sortBtn.setEnabled(False)
			self.sortBtn.setText("  Invalid inpath  ")
		else:
			if not self.working:
				self.sortBtn.setEnabled(True)
			self.sortBtn.setText("  Start count  ")

	def start_count(self):
		self.working = True
		self.sortBtn.setEnabled(False)
		self.statusBar().showMessage("Starting count...")

		self.totalFileCount = 0

		targetPath = str(self.inpathBox.text())
		res = self.count_folder(targetPath)
		self.print_result(res)

		self.statusBar().showMessage("Finished. " + str(self.totalFileCount) + " files.")
		self.working = False
		self.verify_paths()

	def count_folder(self, inpath):
		self.statusBar().showMessage("Count: " + str(self.totalFileCount))
		app.processEvents()
		count = 0
		subfolders = []
		fileList = os.listdir(inpath)
		for filename in fileList:
			if os.path.isdir(os.path.join(inpath, filename)):
				subCount, contents = self.count_folder(os.path.join(inpath, filename))
				count += subCount
				subfolders.append(contents)
			else:
				count += 1
				self.totalFileCount += 1
				if count % 1000 == 0:
					self.statusBar().showMessage("Count: " + str(self.totalFileCount))
					app.processEvents()

		return count, (inpath, count, subfolders)

	def print_result(self, result):
		outFileName = 'file counts.txt'
		i = 0
		while os.path.exists(outFileName):
			i += 1
			outFileName = 'file counts (' + str(i) + ').txt'

		with open(outFileName, 'w+') as outfile:
			self.print_recurse(result[1], outfile)

	def print_recurse(self, res, outfile, depth=0):
		for i in range(depth):
			print('\t', end='')
			outfile.write('\t')

		print(res[0], res[1], sep='\t\t')
		outfile.write(res[0] + '\t\t' + str(res[1]) + '\n')
		if len(res) > 2:
			for sub in res[2]:
				self.print_recurse(sub, outfile, depth+1)


# ----------------------------------------


def build_horizontal_spacer():
	return QSpacerItem(20, 40, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)


# --------------------------------------------------


# Run the program
if __name__ == '__main__':
	main()
