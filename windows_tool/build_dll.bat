@echo off
REM ZeroTrace C++ DLL Build Script
REM Automatically detects and uses available compiler

echo ========================================
echo ZeroTrace C++ Core - Build Script
echo ========================================
echo.

REM Check for MinGW g++
where /q g++
if %ERRORLEVEL% EQU 0 (
    echo [FOUND] MinGW g++ compiler
    echo Compiling with g++...
    g++ -shared -o wiper_core.dll wiper_core.cpp -ladvapi32 -O3 -s -DNDEBUG
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo [SUCCESS] wiper_core.dll created!
        echo File size:
        dir wiper_core.dll | find "wiper_core.dll"
        goto :end
    ) else (
        echo [ERROR] Compilation failed
        goto :error
    )
)

REM Check for MSVC cl.exe
where /q cl
if %ERRORLEVEL% EQU 0 (
    echo [FOUND] MSVC cl.exe compiler
    echo Compiling with cl.exe...
    cl /LD /O2 /DNDEBUG wiper_core.cpp advapi32.lib /Fe:wiper_core.dll
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo [SUCCESS] wiper_core.dll created!
        echo File size:
        dir wiper_core.dll | find "wiper_core.dll"
        goto :end
    ) else (
        echo [ERROR] Compilation failed
        goto :error
    )
)

REM No compiler found
echo [ERROR] No C++ compiler found!
echo.
echo Please install one of the following:
echo   1. MinGW-w64: https://www.mingw-w64.org/
echo   2. Visual Studio Build Tools: https://visualstudio.microsoft.com/downloads/
echo.
echo After installation, run this script again.
goto :error

:error
echo.
echo Build failed. The application will use Python fallback.
pause
exit /b 1

:end
echo.
echo Build complete! The DLL will be automatically detected by ZeroTrace.
pause
exit /b 0
