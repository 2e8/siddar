## About

**siddar** (SImple DeDuplicating ARchiver) - is a shell command that creates incremental backups. Identical files are included in backup only once, regardless of the file name and location.

File size and sha256 checksum are used to check if files are identical or not.

The tool is crossplatform and requires Python3 with standard libraries only. 

## Features

* **create / find / restore commands:** no extra tool is needed;
* **incremental backups:** identical files are included in backup only once;
* **multi-volume archives:** you can specify maximum volume size;
* **tar / gz / bz2 archive formats:** volumes can be compressed;
* **include / exclude filters:** you can specify which files/folders should be included in backup or restored from backup.
