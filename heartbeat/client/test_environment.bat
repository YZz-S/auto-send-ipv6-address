@echo off
echo Testing environment...
echo.

echo Checking Python...
python --version
if errorlevel 1 (
    echo Python not found!
    goto end
)

echo.
echo Checking pip...
pip --version
if errorlevel 1 (
    echo pip not found!
    goto end
)

echo.
echo Checking requests module...
python -c "import requests; print('requests version:', requests.__version__)"
if errorlevel 1 (
    echo requests module not found!
    echo Installing requests...
    pip install requests
)

echo.
echo Environment test completed!

:end
pause 