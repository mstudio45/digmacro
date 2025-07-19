@echo off
cd src
echo Converting all .py files to LF

for /r %%f in (*.py) do (
    echo %%f | findstr /i "__pycache__" >nul
    if errorlevel 1 (
        if exist "%%f" (
            echo Converting: %%f
            dos2unix "%%f"
        )
    )
)

cd ..
cd scripts

for /r %%f in (*.sh) do (
    if exist "%%f" (
        echo Converting: %%f
        dos2unix "%%f"
    )
)

echo Done!