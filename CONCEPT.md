## General concept

### Glossary

* `source` - source path
* `destination` - destination path (for restore)
* `repository` - backup path
* `name` - backup name (without extension and path, stored in `repository`)
* `catalog` - backup catalog = `name.cat`
* `volume` - backup volume = `name.volume_number.tar[.gz|.bz2]`
* `volume_number` - volume number
* `reference` - reference backup name (without extension and path, stored in `repository`) for incremental backup

### Concept

* Backup is created for one folder only - `source`. Please use few commands or use `include` if you need more.
* Backup is created in `repository` folder. `reference` for incremental backup should also be in `repository` folder.
* Backup consists of few `volume`-files and `catalog`-file.
* `Volumes` contain files, renamed as `[sha256].[size]`, without hierarchy.
* `Catalog` contains information about folder structure of `source` folder with some meta-data and links to files, stored in volumes. (See catalog file structure below)

So, the backup format allows you to retrieve files manually, without using the program. You need: plain text editor, tar, gz, bz2 archive programs and any program to "glue" file pieces.

### Multi-volume backup

* All files are added to the current volume;
* if next file does not fit entirely in the current volume, beginning of the file is included in current volume (till current volume reaches max. size) and rest of file is included in the next volume;
* if rest of the file does not fit entirely in the next volume, beginning of the rest is included and rest of rest goes to the next volume;
* and so on...

So, different pieces of file can be stored in several sequential volumes. Files may be larger then volumes.

### Catalog format:
```
DIR_LIST
FILE
[relative path]
[date-time]
[size]
[sha256]
FILE_END
...
DIR
[relative path]
[date-time]
DIR_END
...
DIR_LIST_END
HASH_LIST
HASH[tab][sha256.size][tab][archive]
...
HASH_LIST_END
```
