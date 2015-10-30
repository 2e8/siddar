## Examples

### Windows script for incremental backup

Initial backup should be done manually.

`D:\siddar.py create d:\tmp d:\repository 2014-01-01_%name%`

`%rep%\%dt%_%name%.cat` should be copied to `%rep%\%name%.cat` also manually. (`%name%.cat` is a reference for next incremental backup.)
```
set dt=%date:~6,4%-%date:~3,2%-%date:~0,2%
set name=test
set source=D:\tmp
set rep=D:\repository
D:\siddar.py create d:\%source% %rep% %dt%_%name% -r %name%
copy /Y %rep%\%dt%_%name%.cat %rep%\%name%.cat
```
