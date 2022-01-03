# Misc tools

This repository holds a number of small tools:
* [Copy Marine Mammal images](#copy-marine-mammal-images)
* [File counter](#file-counter)
* [File list/copier](#file-listcopy)
* [File list utility](#file-list-utility)
* [Image date fixer](#image-date-fixer)
* [Image sampler](#image-sampler)
* [Metadata copier](#metadata-copier)

Each tool is a single python file, though each requires PyQt5 installed (see the welcome page) and may require additional packages (listed below under the tool itself). To start a tool, run its file using Python 3. For any tool that copies files, a version of Python >= 3.8 is highly recommended as it will boost file copy performance (which accounts for the vast majority of the running time of most of these tools) on most machines by several times.

## Copy Marine Mammal images

#### Usage

#### Understanding the output

#### Troubleshooting

## File counter

This tool counts the number of files in the folder and each subfolder.

#### Usage

If a target folder with a large number of files is chosen, it may take some time to complete. Once finished, the subfolder counts will be both printed to the console and saved in a text file called "file counts.txt" (which is not overwritten - consecutive runs will output a numbered variation on this, such as "file counts (2).txt").

#### Understanding the output

Each line has the full path of a folder, then the number of files in that folder (including files in subfolders, but not including the subfolders themselves). Subfolders are "tabbed over" from their parent, imitating the original folder structure. 

When reading the results in a text editor, it can be helpful to make sure that "word wrap" is disabled.

#### Troubleshooting

If the program fails to start, ensure that your python install has PyQt5 installed. If you have multiple versions of Python installed (such as an additional Python 2 install), ensure that you are starting the program with the correct version of Python.

If the "start" button instead reads "invalid path," try finding the target folder using the "Browse" button instead of typing it. Be careful of how different operating systems treat forward slashes "/" and back slashes "\\".

## File list/copy

This tool is intended to save and recreate a specific file structure from an unorganized copy of that data. For our purposes, this is primarily for saving the structure of a "processed" folder of image data and allowing it to be re-created from the "raw" folder of that data (or vice versa).

#### Usage

This tool has 3 modes: "list," "copy," and "test subset"

In list mode, select the folder you wish to later be able to recreate as the "File source path," and select a new, empty folder where you wish to put this list as the "File list path." When you press the "Create list" button, it will begin to generate this list.

In copy mode, select the source folder for the (unsorted) files as the "File source path," a list folder created by the tool as the "File list path," and where you wish to copy the files to as the "File destination path." When you press the "Copy files in list" button, it will begin to recreate the originally copied file/folder structure, attempting to find and copy each file from the source folder to the destination one.

Test subset mode is for checking whether all of the files in one folder are duplicated in another folder. Select the folder that you will be keeping as the "File source path," and select the folder that you expect to be able to recreate from this source as the "File destination path." When you press the "Test if destination is a subset of source" button, it will check that every file in the destination path is also contained in the source path.

Be careful the correct folder is chosen for the "File list path" and "File destination path." _Make sure that these do not overlap in any way_.

The "File list folders" have a folder structure identical to the source (except for any empty folders in the source), and each folder has a single file in it if there were any non-folder files in it in the original. You can copy these subfolders out as use them as their own "file list folders," but be careful when doing this. Any unexpected files in these lists may cause unexpected behaviour, or even crashes.

#### Understanding the output

In list mode: the tool will tell you how many files it has counted when creating the list. If this number seems wildly off what you were expecting, make sure your source path is correct.

In copy mode: the tool will give you three numbers when it completes a copy.
* "copied": the number of files successfully copied over to the new folder. If this number seems wildly off what you were expecting, make sure the list path is correct.
* "skipped": the number of files that already existed in the destination, and thus haven't been copied over. This number should typically be 0, unless the destination has already been partially recreated.
* "missing": the number of files that were in the file list, but could not be found in the source folder (and weren't already in the destination). On a successful run, this number should be exactly zero. Any other number means that that many files are missing in the recreated folder.

#### Troubleshooting

If the program fails to start, ensure that your python install has PyQt5 installed. If you have multiple versions of Python installed (such as an additional Python 2 install), ensure that you are starting the program with the correct version of Python.

#### Technical notes

As the tool ignores file paths and works strictly with file names, different files with identical names are likely to be mis-copied.

Empty folders will _not_ be recreated in the final copy

This tool will handle any images that have had their filenames changed with the image date fixer tool; any images renamed using this tool will be recorded in the lists as the original name and will be copied with this tool using their original name, regardless of how the filename appears in the folders when the list is created or where the original file is retreived from when rebuilding a folder. Note that the clause to handle this searches for filenames with brackets in them. Non-image filenames (or those that don't follow the convention that tool uses) that contain brackets at the end of the filename are likely to have unexpected results from this tool.

## File List Utility

A simple utility for listing all files in a single folder.

#### Usage

Place File_list.pyc into the target folder and simply double click it. It will place an output text prefixed "000fileList__", which will be at the top of the folder if files are sorted alphabetically.

Note that this tool ignores subfolders, ignores itself and its related files (such as compile_File_list.py), and ignores any files without a file extension (such as most folders).

#### Understanding the output

The output file lists every file in the current folder, as well as a count on the number of files listed.

#### Technical notes

Source code is present in File_list.py. If you modify this code, you can
compile it by running compile_file_list.py, which will generate a new
.pyc file for convenience.

## Image date fixer

This tool changes file timestamps based on image EXIF data. It can be used to add, offset, or correct timestamps on image files, typically in preparation for using the AIS linker tool.

#### Usage

Open up the tool, select the correct location from the bar on the left, then select the images to have their timestamps corrected using the button on the bottom right. This tool is recursive, so it will look through all subfolders.

To undo renaming the files in a folder, select the "undo rename" option from the file menu, then choose the folder.

Since this tool stores data about each location, running it from a central location (such as a network drive) is recommended. Multiple people using this tool simultaneously will not cause any issues, provided they do not try to edit the tool's data for a single location at the same time.

#### Understanding the output

Images will be renamed based on the image timestamp if that timestamp differs from the filename's current timestamp (or if the filename doesn't include a timestamp it recognizes). The original timestamp is placed in brackets at the end of the filename, enabling this process to be undone if needed. Non-image files (anything that can't be opened with the image library) are ignored.

#### Troubleshooting

## Image sampler

This tool extracts a few images spaced throughout the day from potentially a large set (can be run on multiple months at the same time). 

#### Usage

The "source" folder will be recursively searched (searched through all subfolders) for files matching our naming convention for pictures. Once it creates a list of all of these images, it will copy a subset of those images to the "destination" folder. See the Technical Notes section below for more details on how images are selected.

This tool can be run on multiple months simultaneously, and ignores duplicate images found. Note that it may stop responding when started on massive folder sets; don't worry, this is normal. Give the tool time to think, and only close it if it hasn't been responding for a long time.

#### Troubleshooting

If the program fails to start, ensure that your python install has PyQt5 installed. If you have multiple versions of Python installed (such as an additional Python 2 install), ensure that you are starting the program with the correct version of Python.

If the "start" button instead indicates that one or both of the paths are still needed, try finding the target folder using the "Browse" button instead of typing it. Be careful of how different operating systems treat forward slashes "/" and back slashes "\\".

#### Technical notes

Several variables are set at the top of the file that can tweak the tool's behaviour:
* "startingHour" represents the time of day the tool will attempt to start at, on the earliest day that it can find images for. Note that this is _not_ guarranteed to be the time of the first picture
* hoursRotation: represents the time of each image the tool will search for. Assuming a full set of images, the tool will take the first image at startingHour, the second at startingHour + hoursRotation[0], the third at startingHour + hoursRotation[0] + hoursRotation[1],...
	* To change the times of the images beyond the first, change this array. Adding more terms increases the number of images per "cycle", reducing the terms decreases this number.
	* Note to get images at the same time each day, the sum of hoursRotation should be equal to 24. In general having the same behaviour each day is desirable, but there are some cases where you might not want this (such as a weekly rotation, which would instead sum to 24*7).

## Metadata copier

Additional dependencies: 
* pyexiv2: for reading and copying exif information on images. This Python package can be installed using Pip: "pip install pyexiv2"

Metadata is "extra data" tagged on to each file that contains information about that file. In our typical case, we're thinking about image file metadata, sometimes called EXIF data, which contains information such as the photographer, camera type, or of particular interest to us, the date and time it was taken. One of our auto-detection tools copies images _without_ copying this metadata. This tool allows you to restore the original metadata to these copied images.

#### Usage

Start this program using Python 3. Enter the folder path that contains both the original images and the images that you think might be missing metadata. Try to narrow in on as small of a folder that still contains all of the required information, but this tool can handle large folders and will safely ignore any images that already have metadata attached.

#### Understanding the output

The number of "reference files found" is the number of images with metadata located by the tool while searching. If you select a folder with just images without metadata, this will be 0 (or a very low number), indicating that you need to pick a higher level folder with the original images.

The number of files corrected is the number of images that initially didn't have metadata, but that the program found a duplicate image for that did contain the metadata and was able to copy it over successfully.

The number of files skipped is the number of images that did not, and still do not, have metadata. If this is a significant number, check that the folder you've selected contains the original images as well. Also check whether the duplicate images have the same name as the originals. If this is zero, then all images in the target folder now have metadata attached to them.

#### Troubleshooting

If the program fails to start, ensure that your python install has both pyexiv2 and PyQt5 installed. If you have multiple versions of Python installed (such as an additional Python 2 install), ensure that you are starting the program with the correct version of Python.

If the "start" button instead reads "invalid path," try finding the target folder using the "Browse" button instead of typing it. Be careful of how different operating systems treat forward slashes "/" and back slashes "\\".

This tool should stay responsive while working, but if it locks up, let it work for a few minutes. Only after a few minutes, if it hasn't updated the information displayed and is still not responding, is it likely that something has gone wrong. In this case, try running the tool on a smaller folder.

#### Technical notes

This program compares filenames _only_ up to the first period. This means that all of "picture.jpg", "picture.JPG", "picture.old.jpg", and "picture.new.jpg" _will_ match against each other. Also note that it is case sensitive, so "picture.jpg" will not match against "Picture.jpg".

Only files that end in ".jpg" or ".JPG" are considered. All other files are skipped, even if they are actually of jpg format but under a different name. Note that files that end in one of these file endings, but are not actually jpg's, are likely to cause unexpected behaviour.
