# Misc tools

This repository holds a number of small tools:
* [File counter](#file-counter)
* [File list/copier](#file-listcopy)
* [Image sampler](#image-sampler)
* [Metadata copier](#metadata-copier)

## File counter

todo

## File list/copy

todo

## Image sampler

todo

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

#### Technical notes:

This program compares filenames _only_ up to the first period. This means that all of "picture.jpg", "picture.JPG", "picture.old.jpg", and "picture.new.jpg" _will_ match against each other. Also note that it is case sensitive, so "picture.jpg" will not match against "Picture.jpg".

Only files that end in ".jpg" or ".JPG" are considered. All other files are skipped, even if they are actually of jpg format but under a different name. Note that files that end in one of these file endings, but are not actually jpg's, are likely to cause unexpected behaviour.
