from datetime import datetime, timedelta
import sys
import os
import re

from PyQt5 import QtGui, QtCore, uic, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import pyexiv2

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
		self.referenceFileCount = 0
		self.processed = [0, 0, 0]		# [total to process, corrected, skipped]

		# set central layout and some default window options
		self.mainWidget = QWidget()
		self.setCentralWidget(self.mainWidget)
		self.setGeometry(400, 250, 400, 300)
		self.setWindowTitle('Metadata Copier')

		self.mainLayout = QVBoxLayout()
		self.mainWidget.setLayout(self.mainLayout)

		self.pathLayout = QHBoxLayout()
		self.mainLayout.addLayout(self.pathLayout)

		self.pathLayout.addWidget(QLabel('path:'))
		self.pathBox = QLineEdit("")
		self.pathLayout.addWidget(self.pathBox)
		self.pathBtn = QPushButton("Browse")
		self.pathBtn.clicked.connect(self.select_path)
		self.pathBox.textChanged.connect(self.verify_path)
		self.pathLayout.addWidget(self.pathBtn)

		# self.duplicateBox = QCheckBox('Skip files with matching names')
		# self.duplicateBox.setChecked(True)
		# self.duplicateBox.setToolTip('When checked, skip files when more than one matching reference file is found. This is recommended')
		# self.mainLayout.addWidget(self.duplicateBox)

		self.startBtnLayout = QHBoxLayout()
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
		self.show()

	def select_path(self):
		folder = QFileDialog.getExistingDirectory(self, "Select Directory")
		if folder:
			self.pathBox.setText(str(folder))

	def verify_path(self):
		if os.path.exists(str(self.pathBox.text())):
			if not self.isProcessing:
				self.startBtn.setEnabled(True)
			self.startBtn.setText('Start')
		else:
			self.startBtn.setEnabled(False)
			self.startBtn.setText('(invalid path)')

	def update_info_text(self, stillSearching=True, stillProcessing=True):
		# TODO: add info about duplicates
		text = '{0} files found\n\t{1} with metadata\n\t{2} without\n'.format(
			self.totalJPGs, self.referenceFileCount, self.processed[0])
		if not stillSearching:
			text += '{0} reference files found\n{1} files corrected\n{2} files skipped (unable to find info for)\n'.format(
				self.referenceFileCount, self.processed[1], self.processed[2]
			)
		text += ('working...' if stillProcessing else 'done.')
		self.infoLabel.setText(text)

	def process(self):
		self.isProcessing = True
		self.startBtn.setEnabled(False)

		# Reset summary data
		self.totalJPGs = 0
		self.referenceFileCount = 0
		self.processed = [0, 0, 0]

		basePath = str(self.pathBox.text())
		d = {}
		listToAddMeta = []
		self.build_hash(basePath, d, listToAddMeta)
		self.update_info_text()

		self.add_meta(d, listToAddMeta)
		self.update_info_text(False, False)

		self.isProcessing = False

	def build_hash(self, path, d, listToAddMeta):
		folders = []
		for i, filename in enumerate(os.listdir(path)):
			if i % 100 == 1:
				self.update_info_text()
				app.processEvents()
			filepath = os.path.join(path, filename)
			if os.path.isdir(filepath):
				folders.append(filepath)
			elif filepath.endswith('.jpg') or filepath.endswith('.JPG'):
				self.totalJPGs += 1
				if self.add_to_hash(d, filepath, filename):
					self.referenceFileCount += 1
				else:
					listToAddMeta.append((filepath, filename))
					self.processed[0] += 1
		for folder in folders:
			self.build_hash(folder, d, listToAddMeta)

	# Returns True and inserts if valid metadata, else returns False and does not insert
	def add_to_hash(self, d, filepath, filename):
		shortName = filename.split('.')[0]
		with pyexiv2.Image(filepath) as img:
			meta = img.read_exif()
			if len(meta) < 1:
				return False

			self.trim_meta(meta)
			if shortName not in d:
				d[shortName] = meta
			else:
				pass					# TODO don't go fubar
			return True

	def add_meta(self, d, listToAddMeta):
		for i, file in enumerate(listToAddMeta):
			if i % 100 == 1:
				self.update_info_text(False)
				app.processEvents()
			filepath, filename = file
			shortName = filename.split('.')[0]
			if shortName in d:
				with pyexiv2.Image(filepath) as img2:
					img2.modify_exif(d[shortName])
				self.processed[1] += 1
			else:
				self.processed[2] += 1

	def trim_meta(self, meta):
		toPop = ['Exif.Thumbnail.Compression',
				 'Exif.Thumbnail.XResolution',
				 'Exif.Thumbnail.YResolution',
				 'Exif.Thumbnail.ResolutionUnit',
				 'Exif.Thumbnail.JPEGInterchangeFormat',
				 'Exif.Thumbnail.JPEGInterchangeFormatLength']
		for item in toPop:
			if item in meta:
				meta.pop(item)

if __name__ == "__main__":
	main()
