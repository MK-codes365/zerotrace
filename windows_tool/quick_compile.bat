@echo off
echo Building wiper_core.dll with Visual Studio...

call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"
cl /LD /O2 /DNDEBUG wiper_core.cpp advapi32.lib /Fe:wiper_core.dll

if exist wiper_core.dll (
    echo [SUCCESS] DLL updated with 100%% callback fix!
    dir wiper_core.dll
) else (
    echo [FAILED] Could not compile
)

pause
