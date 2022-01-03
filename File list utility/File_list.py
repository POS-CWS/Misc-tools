# Generates a list of all files in folder
# Ignores itself and it's related utilities and files without a file extension
# Author: Gregory O'Hagan

# A simple script for listing all of the files in the current directory
import os
import re

def main():
	# Get the folder path and build a file name
	fullPath = os.path.realpath(__file__)
	path = '\\'.join(fullPath.split('\\')[0:-1])
	outfilename = "000fileList__" + fullPath.split("\\")[-2] + ".txt"
	fout = open(path + "\\" + outfilename,'w')
	
	# Start off the output file
	fout.write("List of all files in:\n")
	fout.write(path + "\n\n")
	
	counter = 0
	# Loop through all files in the directory
	for filename in os.listdir(path):
		# Ignore this program and the output file
		if filename == outfilename or filename == "File_list.py":
			continue
		if filename == "compile_File_list.py" or filename == "File_list.pyc":
			continue
		# Ignore folders (or anything without a file extension)
		if not re.match("^.*\..*$", filename):
			continue
		# Print the filename both to the console and the file
		print filename
		fout.write(filename + "\n")
		counter += 1
	
	fout.write("\nlisted " + str(counter) + " files\n")
	print("done")


if __name__ == "__main__":
	main()