## Restore from backup

siddar.py **restore** -h

siddar.py **restore** repository name destination [-i mask ...] [-e mask ...] [-d] [-g]

|    |        |                         |
|:---|:-------|:------------------------|
| -h | --help | Show short description. |
|| `repository` | Backup path: `y:\arch`, `./my_rep` (without slash at the end).<br/>Windows: if path has spaces, use double quotes: `"d:\folder name"`. |
|| name | Backup name: `arch12`, `backup_2013-10-15`. |
|| destination | Destination path (without slash at the end). |
| -i | --include | Space separated set of include restore masks for files / folders. `*` and `?` can be used. (`filename.jpg`, `*.pdf *.doc`, `doc201?.pdf`, `doc*.pdf`). |
| -e | --exclude | Space separated set of exclude restore masks for files / folders. `*` and `?` can be used. (`filename.jpg`, `*.pdf *.doc`, `doc201?.pdf`, `doc*.pdf`). |
| -d | --delete | Remove from `destination` files, not restored from backup.<br/>Default: restored files are created, other files in `destination` are not deleted. |
| -g | --ignore | Ignore all errors. |

Command reports restore progress:

`Files (New/All): x / y, Size (New/All): a.aa Mb / b.bb Mb`

For example: `Files (New/All): 1 / 3, Size (New/All): 1.33 Mb / 2.15 Mb` reports that 1 file is already restored, total 3 files will be restored. 1.33 Mb is already restored. Total 2.15 Mb will be restored.
