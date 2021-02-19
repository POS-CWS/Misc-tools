from datetime import datetime, timedelta
import sys
import os
import re

from PyQt5 import QtGui, QtCore, uic, QtWidgets
from PyQt5.QtWidgets import *
# from PyQt5.QtCore import *
# from PyQt5.QtGui import *

from functools import partial

# Get this via "pip install Pillow"
from PIL import Image

def main():
	app = QApplication(sys.argv)
	ex = Program()
	sys.exit(app.exec_())


# Popup window to request a date
# Modified from: https://stackoverflow.com/questions/18196799/how-can-i-show-a-pyqt-modal-dialog-and-get-data-out-of-its-controls-once-its-clo
class DateDialog(QDialog):
	def __init__(self, parent=None):
		super(DateDialog, self).__init__(parent)

		layout = QVBoxLayout(self)

		# nice widget for editing the date
		self.date = QDateEdit(self)
		self.date.setCalendarPopup(True)
		self.date.setDate(QtCore.QDate.currentDate())
		layout.addWidget(self.date)

		# OK and Cancel buttons
		buttons = QDialogButtonBox(
			QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
			QtCore.Qt.Horizontal, self)
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)
		layout.addWidget(buttons)

	# get current date and time from the dialog
	def dateTime(self):
		qDate = self.date.dateTime().date()
		return datetime(qDate.year(), qDate.month(), qDate.day())

	# static method to create the dialog and return (date, time, accepted)
	@staticmethod
	def getDate(parent=None):
		dialog = DateDialog(parent)
		result = dialog.exec_()
		date = dialog.dateTime()
		return (date, result == QDialog.Accepted)


class Program(QMainWindow):
	dataFolder = "dates_db"
	logFolder = "logs"

	def __init__(self):
		super(Program, self).__init__()

		# Ensure we always have a data folder. Other methods assume this.
		if not os.path.exists(self.dataFolder):
			os.mkdir(self.dataFolder)

		self.location = ""
		self.marginSecs = 1		# seconds
		self.locations = []
		self.timeCorrections = []

		# set central layout and some default window options
		self.mainWidget = QWidget()
		self.setCentralWidget(self.mainWidget)
		self.setGeometry(400, 250, 1000, 600)
		self.setWindowTitle('Image renamer')		# Note: this gets changed later

		self.mainLayout = QVBoxLayout()
		self.mainWidget.setLayout(self.mainLayout)

		# Create "File" menu
		self.statusBar()
		self.mainMenu = self.menuBar()
		self.fileMenu = self.mainMenu.addMenu('&File')

		# File menu option for editing image times
		self.editTimesAction = QAction("&Edit times", self)
		self.editTimesAction.setStatusTip('Add or modify camera and pi time configuration')
		self.editTimesAction.triggered.connect(self.show_edit_time_screen)
		self.fileMenu.addAction(self.editTimesAction)
		# Add spacer in file menu
		self.fileMenu.addSeparator()

		# File menu option for adding new locations
		self.addLocationAction = QAction("&Add new location", self)
		self.addLocationAction.setStatusTip('Adds a new camera location, with independent time adjustments')
		self.addLocationAction.triggered.connect(self.add_location_action)
		self.fileMenu.addAction(self.addLocationAction)

		# File menu option for deleting the current location
		self.delLocationAction = QAction("&Delete current location", self)
		self.delLocationAction.setStatusTip('Archive the current location, making it unavailable to use')
		self.delLocationAction.triggered.connect(self.delete_location_action)
		self.fileMenu.addAction(self.delLocationAction)
		self.fileMenu.addSeparator()

		# File menu option for undoing a previous location
		self.undoRenameAction = QAction("&Undo rename", self)
		self.undoRenameAction.setStatusTip('Undo any rename applied to the target folder')
		self.undoRenameAction.triggered.connect(self.undo_rename_action)
		self.fileMenu.addAction(self.undoRenameAction)

		self.show_main_screen()

		# Load stored data
		self.load_metadata()

		self.update_display()
		self.show()

	# Sets up the main window to display the location select and time summaries
	def show_main_screen(self):
		# remove everything from main layout, making room for new stuff
		for i in reversed(range(self.mainLayout.count())):
			self.mainLayout.itemAt(i).widget().setParent(None)

		# Enable file menu:
		self.addLocationAction.setEnabled(True)
		self.editTimesAction.setEnabled(True)
		self.delLocationAction.setEnabled(True)
		self.undoRenameAction.setEnabled(True)

		self.contentsWidget = QWidget()
		self.contentsLayout = QGridLayout()
		self.contentsWidget.setLayout(self.contentsLayout)
		self.mainLayout.addWidget(self.contentsWidget)

		# Add labels to the top of the columns
		self.locAreaLbl = QLabel("Location")
		self.locAreaLbl.setAlignment(QtCore.Qt.AlignLeft)
		self.contentsLayout.addWidget(self.locAreaLbl, 0, 0)

		self.timeAreaLbl = QLabel("Date" + " " * 25 + "Camera time" + " " * 10 + "pi Time")
		self.timeAreaLbl.setAlignment(QtCore.Qt.AlignLeft)
		self.contentsLayout.addWidget(self.timeAreaLbl, 0, 1)

		# Create scroll area for locations
		self.locScrollArea = QScrollArea()
		self.locScrollArea.setWidgetResizable(True)
		self.locScrollArea.setMinimumWidth(200)

		self.locScrollWidget = QWidget()
		self.locScrollLayout = QVBoxLayout()

		self.locScrollWidget.setLayout(self.locScrollLayout)
		self.locScrollArea.setWidget(self.locScrollWidget)
		self.contentsLayout.addWidget(self.locScrollArea, 1, 0)

		# Create scroll area for timing information
		self.timeScrollArea = QScrollArea()
		self.timeScrollArea.setWidgetResizable(True)
		self.timeScrollArea.setMinimumWidth(200)

		self.timeScrollWidget = QWidget()
		self.timeScrollLayout = QVBoxLayout()

		self.timeScrollWidget.setLayout(self.timeScrollLayout)
		self.timeScrollArea.setWidget(self.timeScrollWidget)
		self.contentsLayout.addWidget(self.timeScrollArea, 1, 1)

		# Add an option to look through all files
		self.includeNonStandardCheckbox = QCheckBox('Include images in non-standard format ("capture_date_time.jpg")')
		self.contentsLayout.addWidget(self.includeNonStandardCheckbox)

		# Add the current location name again, as well as the "select images" button
		self.endLayout = QHBoxLayout()
		self.contentsLayout.addLayout(self.endLayout, 3, 1)

		spacer = QSpacerItem(100, 40, QSizePolicy.Expanding, QSizePolicy.Minimum)
		self.endLayout.addItem(spacer)

		self.locationLbl = QLabel("")
		self.endLayout.addWidget(self.locationLbl)

		self.renameBtn = QPushButton("Select Images")
		self.renameBtn.clicked.connect(self.rename_select_folder)
		self.endLayout.addWidget(self.renameBtn)

		self.update_location_list()
		self.update_timing_list()

	# Handles changing the active location
	# Attach buttons with this: b.clicked.connect(partial(self.loc_button_event, name))
	def loc_button_event(self, loc):
		self.location = loc
		self.update_display()

	# Updates the two lists (location and time adjustments) of the main display
	# Also sets current location labels
	def update_display(self):
		self.locationLbl.setText(self.location)
		self.setWindowTitle(self.location)

		self.update_location_list()
		self.update_timing_list()

	# Updates the list of buttons in the main screen corresponding to each location
	# Should only need to be called when rebuilding the main screen or adding/removing locations
	def update_location_list(self):
		# Ensure all previous items in area were deleted
		for i in reversed(range(self.locScrollLayout.count())):
			self.locScrollLayout.itemAt(i).widget().setParent(None)

		for f in os.listdir(self.dataFolder):
			# Ignore archived locations
			if f.endswith(" - archived.csv"):
				continue
			if f.endswith(".csv"):
				name = f[:-4]
				b = QPushButton(name)
				b.setStyleSheet("QPushButton { text-align: left; }")

				# TODO: add marking the currently selected location button here

				b.clicked.connect(partial(self.loc_button_event, name))
				self.locScrollLayout.addWidget(b)

		# spacer = QSpacerItem(100, 40, QSizePolicy.Expanding, QSizePolicy.Expanding)
		# self.locScrollLayout.addItem(spacer)

	# Updates both self.timeCorrections in memory and the display
	# Uses location from memory
	def update_timing_list(self):
		# Ensure all previous items in area were deleted
		for i in reversed(range(self.timeScrollLayout.count())):
			self.timeScrollLayout.itemAt(i).widget().setParent(None)

		self.timeCorrections = []

		path = os.path.join(self.dataFolder, self.location + ".csv")
		# Ensure file for the location exists
		if not os.path.exists(path):
			return

		with open(path) as inFile:
			for line in inFile:
				m = re.match(r"^(\d\d\d\d)-(\d+)-(\d+),(-?\d+),(-?\d+)", line)
				# ignore lines that don't match expected format (room for comments, error handling)
				if not m:
					continue

				# Add time point to list
				time = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
				self.timeCorrections.append((time, int(m.group(4)), int(m.group(5))))

				# Create string for display
				# Start with date
				text = self.build_date_string(time.year, time.month, time.day)

				# Ensure spacing is consistent.
				# Note: condition should never fail, but is there for error handling
				if len(text) < 25:
					text += " " * (25 - len(text))

				# camera time
				text += self.build_time_diff_string(int(m.group(4)))

				# Ensure spacing is consistent
				if len(text) < 50:
					text += " " * (50 - len(text))

				# pi time
				text += self.build_time_diff_string(int(m.group(5)))

				# Add text to screen
				lbl = QLabel(text)
				self.timeScrollLayout.addWidget(lbl)

		# spacer = QSpacerItem(100, 40, QSizePolicy.Expanding, QSizePolicy.Expanding)
		# self.timeScrollLayout.addItem(spacer)

	# Reads settings from the last time the program was open.
	# Currently only sets the default location
	def load_metadata(self):
		try:
			with open(os.path.join(self.dataFolder, "meta.txt"), "r") as inFile:
				for line in inFile:
					line = line.rstrip()

					if line.startswith("Location: "):
						self.location = line[10:]
					if line.startswith("Margin (Seconds): "):
						self.marginSecs = int(line[18:])
					# Add any additional metadata here
		except IOError:
			print("Can't read metadata.")
			self.location = "(location)"

	# Prompt the user for new location data
	def add_location_action(self):
		name, ok = QInputDialog.getText(self, "New location", "Enter new location name:")
		if ok and name:
			# Prompt the user to start adding date adjustments.
			# Note: new location isn't technically saved until the confirm on this screen
			self.location = str(name)
			self.timeCorrections = []
			self.show_edit_time_screen()

	# Archive a location, making it inaccessible by the program
	# Note: power users can manually rename the file to make it accessible again if needed
	def delete_location_action(self):
		reply = QMessageBox.question(self, 'Continue?', 'warning: this will delete this location',
									 QMessageBox.Yes, QMessageBox.No)
		# Rename the file to an archived file in the user requests deletion.
		if reply == QMessageBox.Yes:
			os.rename(os.path.join(self.dataFolder, self.location + ".csv"),
					  os.path.join(self.dataFolder, self.location + " - archived.csv"))
			self.location = ""
			self.update_display()
		# Do nothing if the user cancels

	def undo_rename_action(self):
		folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
		self.undo_rename(folder, True)

	# Removes everything from the main layout, and replaces it with the contest for editing times
	def show_edit_time_screen(self):
		# remove everything from main layout, making room for new stuff
		for i in reversed(range(self.mainLayout.count())):
			self.mainLayout.itemAt(i).widget().setParent(None)

		# disable file menu:
		self.addLocationAction.setEnabled(False)
		self.editTimesAction.setEnabled(False)
		self.delLocationAction.setEnabled(False)
		self.undoRenameAction.setEnabled(False)

		self.contentsWidget = QWidget()
		self.contentsLayout = QVBoxLayout()
		self.contentsWidget.setLayout(self.contentsLayout)
		self.mainLayout.addWidget(self.contentsWidget)

		# Display the location
		# TODO: center and make this font bigger
		self.locationLbl = QLabel(self.location)
		self.contentsLayout.addWidget(self.locationLbl)

		# Titles for the area below. This way the titles stay if the area is scrolled down
		self.timeAreaLbl = QLabel("Date" + " " * 25 + "Camera time" + " " * 5 + "Pi time")
		self.timeAreaLbl.setAlignment(QtCore.Qt.AlignLeft)
		self.contentsLayout.addWidget(self.timeAreaLbl)

		# Create and fill scroll area for times
		self.timeScrollArea = QScrollArea()
		self.timeScrollArea.setWidgetResizable(True)
		self.timeScrollArea.setMinimumWidth(200)

		self.timeScrollWidget = QWidget()
		self.timeScrollLayout = QVBoxLayout()

		self.timeScrollWidget.setLayout(self.timeScrollLayout)
		self.timeScrollArea.setWidget(self.timeScrollWidget)
		self.contentsLayout.addWidget(self.timeScrollArea)

		self.update_edit_times_list()

		# TODO: stuff for adding new time line

		# options along bottom (delete location, cancel, done)
		# extra step to make widget for easy deletion
		bottomWidget = QWidget()
		self.contentsLayout.addWidget(bottomWidget)
		bottomLayout = QHBoxLayout()
		bottomWidget.setLayout(bottomLayout)

		# Edit time widget. This will be empty when not actively editing a time line
		self.editTimeWidget = QWidget()
		bottomLayout.addWidget(self.editTimeWidget)
		self.editTimeLayout = QHBoxLayout()
		self.editTimeWidget.setLayout(self.editTimeLayout)

		# Ensures that the control buttons are on the right side
		# Note: this doesn't interfere with deletes because we'll delete the whole widget
		spacer = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Fixed)
		bottomLayout.addItem(spacer)

		# Control buttons at bottom right
		cancelBtn = QPushButton("Cancel")
		cancelBtn.clicked.connect(self.cancel_edit_times)
		bottomLayout.addWidget(cancelBtn)

		confirmBtn = QPushButton("Save all changes")
		confirmBtn.clicked.connect(self.confirm_edit_times)
		bottomLayout.addWidget(confirmBtn)

		# testEdit = QTextEdit("default text")
		# # testEdit.setFocusPolicy(QtCore.Qt.StrongFocus)
		# bottomLayout.addWidget(testEdit)
		# testEdit.selectionChanged.connect(self.focus_event)

	# def focus_event(self):
	# 	print("focus changed")

	# updates the edit time corrections display with what is in memory (self.timeCorrections)
	# Note: must be called when the display is set to the edit screen
	def update_edit_times_list(self):

		# remove everything from main layout, making room for new stuff
		for i in reversed(range(self.timeScrollLayout.count())):
			self.timeScrollLayout.itemAt(i).widget().setParent(None)

		for tc in self.timeCorrections:
			# Create a widget for each line for easy deletion
			lineW = QWidget()
			lineL = QHBoxLayout()
			lineW.setLayout(lineL)
			self.timeScrollLayout.addWidget(lineW)

			text = self.build_date_string(tc[0].year, tc[0].month, tc[0].day)

			# Ensure spacing is consistent.
			# Note: condition should never fail, but is there for error handling
			if len(text) < 25:
				text += " " * (25 - len(text))

			# camera time
			text += self.build_time_diff_string(tc[1])

			# Ensure spacing is consistent
			if len(text) < 40:
				text += " " * (40 - len(text))

			# pi time
			text += self.build_time_diff_string(tc[2])

			dateLbl = QLabel(text)
			lineL.addWidget(dateLbl)

			editBtn = QPushButton("Edit")
			editBtn.clicked.connect(partial(self.edit_date_line, tc))
			lineL.addWidget(editBtn)

			delBtn = QPushButton("Delete")
			delBtn.clicked.connect(partial(self.delete_date_line, tc))
			lineL.addWidget(delBtn)

		# Add new time option at bottom
		newBtn = QPushButton("New")
		newBtn.clicked.connect(self.new_date_line)
		self.timeScrollLayout.addWidget(newBtn)

	# Requests a date from the user, then prompts them for the pi and camera time adjustments
	def new_date_line(self, tc):
		date, ok = DateDialog.getDate()
		if ok:
			self.edit_date_line((date, 0, 0))

	# Display a time in the edit area
	# tc: timeCorrection: (dateTime, int, int)
	def edit_date_line(self, tc):
		# remove previous stuff from bottom line if applicable, without saving
		for i in reversed(range(self.editTimeLayout.count())):
			self.editTimeLayout.itemAt(i).widget().setParent(None)

		# Add the date as a label. This part isn't editable
		timeLbl = QLabel(self.build_date_string(tc[0].year, tc[0].month, tc[0].day))
		self.editTimeLayout.addWidget(timeLbl)

		# Add an editable text box for each time
		camBox = QLineEdit(self.build_time_diff_string(tc[1]))
		self.editTimeLayout.addWidget(camBox)

		piBox = QLineEdit(self.build_time_diff_string(tc[2]))
		self.editTimeLayout.addWidget(piBox)

		# Add confirm and cancel buttons
		cancelBtn = QPushButton("Cancel")
		cancelBtn.clicked.connect(self.edit_date_line_cancel)
		self.editTimeLayout.addWidget(cancelBtn)
		acceptBtn = QPushButton("Confirm")
		acceptBtn.clicked.connect(partial(self.edit_date_line_accept, tc[0], camBox, piBox))
		self.editTimeLayout.addWidget(acceptBtn)

		# Enforce a valid entry into the time boxes: grey out the confirm button otherwise
		camBox.textChanged.connect(partial(self.edit_date_line_validate, camBox, piBox, acceptBtn))
		piBox.textChanged.connect(partial(self.edit_date_line_validate, camBox, piBox, acceptBtn))

	# Save and clear the modified line
	# Inputs:
	# t: dateTime object. Specifically, requires t.year, t.month, and t.day to be correct
	# camBox,piBox: QLineEdit for each time, with form either like -7 or 2:30
	# Note: this saves the change locally, but doesn't commit changes to database
	def edit_date_line_accept(self, t, camBox, piBox):
		# Get the time changes from the
		camChange = self.parse_minutes_from_string(camBox.text())
		piChange = self.parse_minutes_from_string(piBox.text())
		# The tuple to be added
		item = (t, camChange, piChange)
		for i, tc in enumerate(self.timeCorrections):
			# Update if the time already exists
			if tc[0] == t:
				self.timeCorrections[i] = item
				item = None
				break
			# Insert in order if that time doesn't exist yet
			elif tc[0] > t:
				self.timeCorrections.insert(i, item)
				item = None
				break
		# If the item hasn't been added yet, insert it at the end:
		if item:
			self.timeCorrections.append(item)
		# Remove icons as a visual aid
		for i in reversed(range(self.editTimeLayout.count())):
			self.editTimeLayout.itemAt(i).widget().setParent(None)
		self.update_edit_times_list()

	# Reads text as either hours or a ':' separated hours and minutes
	# Returns the number of minutes (integer)
	# Returns None if string cannot be parsed
	@staticmethod
	def parse_minutes_from_string(text):
		minutes = 0
		m = re.match("^ *(-?\d+) *$", text)
		if m:
			minutes = int(m.group(1)) * 60
		else:
			m = re.match("^ *(-?\d+):(\d\d) *$", text)
			if m:
				minutes = int(m.group(1)) * 60
				# use same sign on minutes as hours
				if m.group(1)[0] == '-':
					minutes -= int(m.group(2))
				else:
					minutes += int(m.group(2))
			# If we can't read things, print error and return none
			else:
				print("Parse error: can't read camBox time")
				return None
		return minutes

	# Removes everything from the edit date line space. Primarily asthetic - no real function
	def edit_date_line_cancel(self):
		# remove previous stuff from bottom line if applicable, without saving
		for i in reversed(range(self.editTimeLayout.count())):
			self.editTimeLayout.itemAt(i).widget().setParent(None)

	# Checks through the text of both text boxes (txt1, txt2) for either acceptable format:
	# -?\d+ or -?\d+:\d\d
	# If valid, enable button. Otherwise, disable it
	def edit_date_line_validate(self, txt1, txt2, acptBtn):
		if not (re.match("^ *-?\d+ *$", txt1.text()) or re.match("^ *-?\d+:\d\d *$", txt1.text())):
			acptBtn.setEnabled(False)
			return
		if not (re.match("^ *-?\d+ *$", txt2.text()) or re.match("^ *-?\d+:\d\d *$", txt2.text())):
			acptBtn.setEnabled(False)
			return
		acptBtn.setEnabled(True)

	# Removes the time correction from the list in memory
	# Note: This isn't a permanent delete until the file is written (confirm_edit_times)
	# Input: timeCorrection item: ((int, int int), int, int)
	# Returns True if the item was removed, or false if it wasn't in the list
	def delete_date_line(self, timeCorrection):
		try:
			self.timeCorrections.remove(timeCorrection)
			self.update_edit_times_list()
			return True
		except ValueError:
			return False

	# Separate method for easier editing
	def cancel_edit_times(self):
		self.show_main_screen()

	# Save the changes, and return to the main screen
	def confirm_edit_times(self):
		with open(os.path.join(self.dataFolder, self.location + ".csv"), "w+") as saveFile:
			for tc in self.timeCorrections:
				line = self.build_date_string(tc[0].year, tc[0].month, tc[0].day)
				line += "," + str(tc[1]) + "," + str(tc[2]) + "\n"
				saveFile.write(line)
		self.show_main_screen()

	# Updates the meta file when the program is closed
	def closeEvent(self, event):
		# Write the active location. This allows it to resume at the same default
		with open(os.path.join(self.dataFolder, "meta.txt"), "w+") as f:
			f.write("Location: " + self.location + "\n")
			f.write("Margin (Seconds): " + str(self.marginSecs) + "\n")

	# Input: year, month, and day as ints
	# Output: string of form yyyy-mm-dd
	@staticmethod
	def build_date_string(year, month, day):
		res = str(year) + "-"
		if month < 10:
			res += "0"
		res += str(month) + "-"
		if day < 10:
			res += "0"
		res += str(day)
		return res

	# Takes a number in minutes, and converts it to a string of form:
	# -?\d+:\d\d		ex: -125 => -2:05
	@staticmethod
	def build_time_diff_string(deltaMinutes):
		text = ""
		hours = deltaMinutes // 60
		minutes = deltaMinutes % 60
		# account for integer division on negative numbers
		if hours < 0:
			if minutes != 0:
				hours += 1
				minutes = 60 - minutes
			# Add the negative here, so we can use simple abs values later
			text += "-"
		text += str(abs(hours)) + ":"
		if minutes < 10:
			text += "0"
		text += str(abs(minutes)) + " "

		return text

	def rename_select_folder(self):
		folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
		if folder:
			self.rename(folder, True, self.includeNonStandardCheckbox.isChecked())

	# Renames all files in a folder that have times different by greater than the margin
	def rename(self, folder, recurse, searchNonStandard, logFile=None):
		recurseFolders = []
		numErrors = 0
		numRenamed = 0
		for i, filename in enumerate(os.listdir(folder)):
			filePath = os.path.join(folder, filename)
			# If the file is a directory, skip. Recurse on these later if needed
			if os.path.isdir(filePath):
				if recurse:
					recurseFolders.append(filePath)
				continue
			# Note on error handling - included in methods, method will return None
			ft = self.get_file_time(filePath)
			it = self.get_image_time(filePath)

			# If we're searching non-standard files, don't worry if we don't have a filetime
			if searchNonStandard and ft is None:
				ft = datetime.now()
			if ft is None or it is None:
				numErrors += 1
				continue

			# print(ft, it)
			if abs(ft - it) > timedelta(0, self.marginSecs):
				newName = self.build_new_image_name(it, filename)
				# print(newName)
				os.rename(filePath, os.path.join(folder, newName))
				numRenamed += 1

		print("Completed " + str(len(os.listdir(folder))) + " files, with " + str(numRenamed) + " renamed.")
		if numErrors > 0:
			print(str(numErrors) + " errors.")

		for f in recurseFolders:
			self.rename(f, recurse, searchNonStandard, logFile=logFile)

	# Gets the CAMERA timestamp of the image
	# Returns a datetime object, accurate to the seconds place
	def get_image_time(self, filePath):
		# get raw time
		timeStr = ""
		try:
			timeStr = Image.open(filePath)._getexif()[36867]
		except:
			return None
		t = datetime(int(timeStr[0:4]), int(timeStr[5:7]), int(timeStr[8:10]),
				int(timeStr[11:13]), int(timeStr[14:16]), int(timeStr[17:19]))

		# Find correct time correction
		delta = 0
		for tc in self.timeCorrections:
			if tc[0] < t:
				delta = tc[1]
			else:
				break
		# convert time correction to minutes, and modify appropriately
		# Subtraction since the stored time is a time zone, and we are converting to utc.
		# Ex: 8am PST (-8:00) is 4pm UTC
		t = t - timedelta(0, delta * 60)
		# print(t)
		return t

	# Gets the PI timestamp of the image
	# Returns a datetime object, accurate to the seconds place
	# Returns none if the filename cannot be parsed
	def get_file_time(self, filePath):
		m = re.search(r'(\d\d\d\d)-(\d\d)-(\d\d)_(\d\d)-(\d\d)-(\d\d).*', filePath)
		if not m:
			return None
		t = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
					 int(m.group(4)), int(m.group(5)), int(m.group(6)))

		# Find correct time correction
		delta = 0
		for tc in self.timeCorrections:
			if tc[0] < t:
				delta = tc[2]
			else:
				break
		# convert time correction to minutes, and modify appropriately
		# Subtraction since the stored time is a time zone, and we are converting to utc.
		# Ex: 8am PDT (-8:00) is 4pm UTC
		t = t - timedelta(0, delta * 60)

		return t

	# Input: datetime imageTime: zulu time of the image
	# oldname: the old filename, including a 4 character extension (expected: ".jpg")
	# Return: a name matching the new time, including the old name in brackets on the end
	# Note: operates exclusively  on the file name, NOT the file path
	def build_new_image_name(self, imageTime, oldName):
		# Construct string with constant length
		res = "capture_" + str(imageTime.year) + "-"
		if imageTime.month < 10:
			res += "0"
		res += str(imageTime.month) + "-"
		if imageTime.day < 10:
			res += "0"
		res += str(imageTime.day) + "_"
		if imageTime.hour < 10:
			res += "0"
		res += str(imageTime.hour) + "-"
		if imageTime.minute < 10:
			res += "0"
		res += str(imageTime.minute) + "-"
		if imageTime.second < 10:
			res += "0"
		res += str(imageTime.second)
		# Strip extension, place old name in brackets, and add .jpg back in
		res += "(" + (oldName[:-4] if oldName.endswith('.jpg') else oldName) + ").jpg"
		return res

	# Reverses a pass of the renamer program through a folder.
	def undo_rename(self, folder, recurse):
		recurseFolders = []
		numErrors = 0
		numRenamed = 0
		for filename in os.listdir(folder):
			filePath = os.path.join(folder, filename)
			# If the file is a directory, skip. Recurse on these later if needed
			if os.path.isdir(filePath):
				if recurse:
					recurseFolders.append(filePath)
				continue

			# check if the file matches the pattern of a renamed file.
			m = re.search("capture_.{10}_.{8}\((.+)\)", filename)
			# If this file wasn't previously renamed, ignore it
			if not m:
				continue

			# Check if the new file path already has a file. We don't want to overwrite anything
			newFilePath = os.path.join(folder, m.group(1) + ".jpg")
			if os.path.exists(newFilePath):
				numErrors += 1
				continue

			# Increment counter and rename
			numRenamed += 1
			os.rename(filePath, newFilePath)

		print(str(numRenamed) + " of " + str(len(os.listdir(folder))) + " images renamed.")
		# For visual clarity, only print out errors if there was an error
		if numErrors > 0:
			print("Could not rename " + str(numRenamed) + "files")

		# Note: if recurse is false, then recurseFolders will be empty
		for f in recurseFolders:
			self.undo_rename(f, recurse)


def demo():
	# t1 = time.gmtime(1000000000)
	# print(t1)
	#
	# t2 = time.struct_time((2018, 6, 1, 22, 3, 36, 0, 0, 0))
	# print (t2)
	#
	# t3 = time.strptime("capture_2016-12-14 12 21 31", "capture_%Y-%m-%d %H %M %S")
	# print(t3)

	t1 = datetime(2017, 6, 1, 22, 3, 36)
	print(t1)
	print(t1.year, t1.month, t1.day, t1.hour, t1.minute, t1.second, t1.microsecond, t1.tzinfo)

	td1 = timedelta(2, 30)
	print(td1)
	print(t1 + td1)

	t2 = datetime(2017, 5, 1, 22, 1, 1)
	print(t2 - t1)
	print(t1 - t2)
	td2 = t2 - t1
	print(td2.days, td2.seconds, td2.microseconds)
	print(td_to_seconds(t2 - t1), td_to_seconds(t1 - t2))


def td_to_seconds(td):
	return td.seconds + td.days * 86400


if __name__ == "__main__":
	main()
