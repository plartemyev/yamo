YAMO (Yet Another Multimedia Organizer)
======

This is a simple utility written in python to organize file structure of music collections.
It could be handy for those who still prefers to have their music collections as local files.
Sometimes one could encounter dark and encumbered directories with lots of the same MP3's
or ungodly amounts of remixes littered over dozens of subdirectories.
![app_screenshot]

LICENSE
-------
This is free software, distributed under the GPL v.3. If you want to discuss
a release under another license, please open an issue on Github

NOTES
-----
As usual with this kind of software :
This software is provided "AS-IS", without any guarantees. It should not do
any harm to your system, but if it does, the author, github, etc... cannot
be held responsible. Use at your own risk. You have been warned.

Icons were taken from [KDE/breeze-icons](https://github.com/KDE/breeze-icons)

USAGE
-----
Select the source and target directories, layout style `Plain` or `By albums`.
Try to begin in `Dry run` mode, look at suggested actions and if you happy with them - proceed
in `Copy` or `Move` modes.  
Albums are always prefixed with their year.  
By default YAMO will prefix music files with their indexes in "By albums" layout
and by album index and track index in "Plain" layout - like **0101 Song name.mp3**.  
`No indexes in names` is here if you don't want it to happen.

Some hardware players sort music only by FAT indexes. So there are utilities to get those fs level data in
desired order. That's why file name indexes are important, especially in situation with a single directory with
lots of MP3's  
I prefer `fatsort`:
```Shell
sudo fatsort -can /dev/sde1
```

`media_recollect.py` module could be used separately from command line:
```Shell
media_recollect.py --help
usage: media_recollect.py [-h] [--source_dir SOURCE_DIR]
                          [--target_dir TARGET_DIR] [--op_mode OP_MODE]
                          [--dir_structure DIR_STRUCTURE] [--no_indexes]
                          [--debug]

Organize mp3 collections

optional arguments:
  -h, --help            show this help message and exit
  --source_dir SOURCE_DIR
                        Specify source directory to process. Current directory
                        used if omitted.
  --target_dir TARGET_DIR
                        Specify where to move the files. "source_dir" used if
                        omitted.
  --op_mode OP_MODE     Mode of operation (no-op/copy/move). "no-op" if
                        omitted.
  --dir_structure DIR_STRUCTURE
                        Arrange the files by performer or by performer and
                        albums (plain/albums). Plain if omitted.
  --no_indexes          Do not prefix media files with any indexes. Indexes on
                        if omitted.
  --debug
```

REQUIREMENTS
-------------
App requires **python3**, **PyQt5** and **mutagen**.

TODO
----
* [ ] Implement alternate track identification methods for files without tags. I'm thinking about audio fingerprints.
* [ ] Add handling of other popular music file formats besides MP3.
* [ ] Add cleanup functionality for "Move" operating mode
(leftover empty directories, OS-specific litter, cover art, etc)
* [ ] Localization
* [ ] Package for Android.

CONTRIBUTING
------------
Here's how you can help : 
* You can clone the git repository and start hacking with the code. Pull requests are most welcome.



[app_screenshot]: screenshot.png "Usage illustration"
