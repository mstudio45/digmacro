@echo off
cd ..
echo Deleting all __pycache__ folders recursively from %cd% ...
for /d /r %%d in (__pycache__) do (
    if exist "%%d" (
        echo Deleting: %%d
        rmdir /s /q "%%d"
    )
)
echo Done!