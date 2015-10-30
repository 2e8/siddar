## About

**siddar** (SImple DeDuplicating ARchiver) - is a shell command that creates incremental backups. Identical files are included in backup only once, regardless of the file name and location.

File size and sha256 checksum are used to check if files are identical or not.

## Features

* **create / find / restore commands:** no extra tool is needed;
* **incremental backups:** identical files are included in backup only once;
* **multi-volume archives:** you can specify maximum volume size;
* **tar / gz / bz2 archive formats:** volumes can be compressed;
* **include / exclude filters:** you can specify which files/folders should be included in backup or restored from backup;
* **cross-platform:** requires Python3 with standard libraries only.

## Documentation

### Create backup

siddar.py **create** -h

siddar.py **create** source repository name [-r reference] [-s size] [-i mask ...] [-e mask ...] [-c tar|gz|bz2] [-q] [-g] [-a]

|    |        |                         |
|:---|:-------|:------------------------|
| -h | --help | Show short description. |
|| source | Source path: `d:\folder`, `/media/sdcard`, `../user_name` (without slash at the end). |
|| repository | Backup path: `y:\arch`, `./my_rep` (without slash at the end).<br/>Windows: if path has spaces, use double quotes: `"d:\folder name"`. |
|| name | Backup name: `arch12`, `backup_2013-10-15`. |
| -r | --reference | Reference backup name for incremental backup `arch11`, `backup_2012-01-01`.<br/>Reference backup `.cat` file should be in `repository`. Reference volumes are not necessary.<br/>If repository is not specified, full backup is created. |
| -s | --size | Maximum volume size for `tar` uncompressed archives (byte).<br/>Maximum volume size is always defined for uncompressed data, even if you are using `gz` or `bz2` compression.<br/>Default: 1.069.547.520 byte. |
| -i | --include | Space separated set of include masks for files / folders. `*` and `?` can be used. (`filename.jpg`, `*.pdf *.doc`, `doc201?.pdf`, `doc*.pdf`).<br/>Default: `*`. |
| -e | --exclude | Space separated set of exclude masks for files / folders. `*` and `?` can be used. (`filename.jpg`, `*.pdf *.doc`, `doc201?.pdf`, `doc*.pdf`). |
| -c | --compression | Compression: `tar`, `gz`, `bz2` <br/>Default: `tar`. |
| -q | --quiet | Turn off all messages except error messages. |
| -g | --ignore | Ignore all errors. |
| -a | --recalculate | Recalculate checksum for all files in `source`.<br/>By default, if new incremental backup is created, checksums are calculated for new / changed (changed size or data-time) files only. This option force checksum calculation for all files. |

Command reports backup progress:

`Files (New/All): x / y, Size (New/All): a.aa Mb / b.bb Mb`

For example: `Files (New/All): 1 / 3, Size (New/All): 1.33 Mb / 2.15 Mb` reports that 1 new file is included in backup, 3 files are already in backup (if it's incremental backup or you have 3 identical files in `source` folder). New file size is 1.33 Mb. Size of all files in `source` folder is 2.15 Mb.

Another example: `Files (New/All): 0 / 818, Size (New/All): 0.00 Mb / 2263.26 Mb` reports that no new file found, 818 files are already in backup (it's definitely incremental backup). Size of all files in `source` folder is 2.15 Mb.

### Search in backup

siddar.py **find** -h

siddar.py **find** repository name [-i mask ...] [-e mask ...]

|    |        |                         |
|:---|:-------|:------------------------|
| -h | --help | Show short description. |
|| repository | Backup path: `y:\arch`, `./my_rep` (without slash at the end).<br/>Windows: if path has spaces, use double quotes: `"d:\folder name"`. |
|| name | Backup name mask for search. (You can search in few backups at the same time.) `*` and `?` can be used. (`arch12`, `arch??`, `backup_*15`) |
| -i | --include | Space separated set of include search masks for files / folders. `*` and `?` can be used. (`filename.jpg`, `*.pdf *.doc`, `doc201?.pdf`, `doc*.pdf`). |
| -e | --exclude | Space separated set of exclude search masks for files / folders. `*` and `?` can be used. (`filename.jpg`, `*.pdf *.doc`, `doc201?.pdf`, `doc*.pdf`). |

Command returns list of files / folders found:

`Name_catalogue.cat:     	relative_path/filename`

### Restore from backup
