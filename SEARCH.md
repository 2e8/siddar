## Search in backup

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
