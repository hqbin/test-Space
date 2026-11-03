@echo off
setlocal enabledelayedexpansion

set "ROOT_DIR=D:\code\test-Space"
set "PROJECT_DIR=%ROOT_DIR%\test-space"
set "DIST_DIR=%ROOT_DIR%\dist"
set "BUNDLE_DIR=%PROJECT_DIR%\src-tauri\target\release\bundle"

title TestSpace Build Tool

cd /d "%PROJECT_DIR%"

for /f "delims=" %%v in ('powershell -NoProfile -Command "(Get-Content package.json -Raw | ConvertFrom-Json).version"') do set "CURRENT_VERSION=%%v"

echo.
echo  +-----------------------------------------------+
echo  ^|           TestSpace  Build Tool               ^|
echo  +-----------------------------------------------+
echo.
echo   Current version: v%CURRENT_VERSION%
echo.
echo   Select build type:
echo.
echo     [1] Patch   - bump patch  (x.x.+1)
echo     [2] Minor   - bump minor  (x.+1.0)
echo     [3] Major   - bump major  (+1.0.0)
echo     [4] No bump - build current version as-is
echo     [0] Exit
echo.
set /p "CHOICE=  Enter choice (0-4): "
echo.

if "%CHOICE%"=="0" (
    echo  Bye.
    timeout /t 2 >nul
    exit /b 0
)
if "%CHOICE%"=="1" set "BUILD_LABEL=Patch"  & goto :do_build
if "%CHOICE%"=="2" set "BUILD_LABEL=Minor"  & goto :do_build
if "%CHOICE%"=="3" set "BUILD_LABEL=Major"  & goto :do_build
if "%CHOICE%"=="4" set "BUILD_LABEL=No bump" & goto :do_build

echo  Invalid choice. Please re-run.
pause
exit /b 1

:do_build
echo  [%BUILD_LABEL%] Cleaning old bundle files...
if exist "%BUNDLE_DIR%\nsis" rd /s /q "%BUNDLE_DIR%\nsis"
if exist "%BUNDLE_DIR%\msi"  rd /s /q "%BUNDLE_DIR%\msi"
echo.
echo  [%BUILD_LABEL%] Building... this may take a few minutes.
echo  -----------------------------------------------
echo.

if "%CHOICE%"=="1" call npm run release:patch
if "%CHOICE%"=="2" call npm run release:minor
if "%CHOICE%"=="3" call npm run release:major
if "%CHOICE%"=="4" call npm run tauri build

if errorlevel 1 (
    echo.
    echo  -----------------------------------------------
    echo  [FAILED] Build error. Check the log above.
    echo  -----------------------------------------------
    pause
    exit /b 1
)

echo.
echo  -----------------------------------------------
echo  [OK] Build succeeded. Copying to dist...
echo  -----------------------------------------------
echo.

if exist "%DIST_DIR%" rd /s /q "%DIST_DIR%"
mkdir "%DIST_DIR%"

set "COPIED=0"

if exist "%BUNDLE_DIR%\nsis" (
    for %%f in ("%BUNDLE_DIR%\nsis\*.exe") do (
        echo    [NSIS] %%~nxf
        copy /y "%%f" "%DIST_DIR%\" >nul
        set /a COPIED+=1
    )
)

if exist "%BUNDLE_DIR%\msi" (
    for %%f in ("%BUNDLE_DIR%\msi\*.msi") do (
        echo    [MSI ] %%~nxf
        copy /y "%%f" "%DIST_DIR%\" >nul
        set /a COPIED+=1
    )
)

echo.
if !COPIED! EQU 0 (
    echo  [WARN] No installer files found. Check build output.
) else (
    echo  Copied !COPIED! file(s) to:
    echo  %DIST_DIR%
    echo.
    echo  Output files:
    for %%f in ("%DIST_DIR%\*.exe" "%DIST_DIR%\*.msi") do echo    - %%~nxf
)

echo.
echo  Press any key to exit...
pause >nul
exit /b 0
