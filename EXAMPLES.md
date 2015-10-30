## Examples

### Windows script for incremental backup

Initial backup should be done manually.

`D:\siddar.py create d:\tmp d:\repository 2014-01-01_test`

`D:\repository\2014-01-01_test.cat` should be copied to `D:\repository\test.cat` also manually. (`test.cat` is a reference for next incremental backup.)
```
set dt=%date:~6,4%-%date:~3,2%-%date:~0,2%
set name=test
set source=D:\tmp
set rep=D:\repository
D:\siddar.py create d:\%source% %rep% %dt%_%name% -r %name%
copy /Y %rep%\%dt%_%name%.cat %rep%\%name%.cat
```
