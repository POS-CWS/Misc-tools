This program is for changing file timestamps based on image EXIF data
Copyright (C) 2018-2020 Gregory O'Hagan (GNU v3 licence)
Version 1.1

If any questions arise during use or modifications, feel free to contact the creator at:
	gregoryrohagan@gmail.com

***In addition to the standard python libraries, this requires PyQt5 and Pillow:***
• Both can be installed using pip. Run the commands "pip install pyqt5" and "pip install Pillow"

Usage notes:
• Run the program by running "start.py". No other file manipulation is necessary.
• Databases are created automatically by the program, in the program's folder
	This means that when moving the program, copy the entire folder to keep data
• Running the program from a single location (such as a network drive) is recommended
• Multiple people running the program is okay, provided two copies do not try to edit
	data for the same location at the same time.
• This program was designed and tested using *Python 2*
• The file time can be set to the desired file time to change all filenames to that time
• By default, the tool will only rename images following the standard format
	If renaming all images is desired, check the option to include non-standard images

Other notes:
• This could be reused for many other timing situations by changing 3 methods in start.py:
	get_file_time, git_image_time, and build_new_image_time

Update from Nicole (12 Mar 2020):
Gregory showed me how to run the script with the previous version of Qt. Open a file explorer window and navigate to Z:\vol01\Image_time_fixer. In command prompt, enter "C:\Python2\python.exe start.py", select the site you are interested, select the dates you are interested in. When the tool is running, it will say not responding. If you ever need to undo the changes, you can do so in the tool as well.

