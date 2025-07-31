@echo off
setlocal enabledelayedexpansion

:: burpDrop.bat
:: Author: Gashaw Kidanu
:: Version: 1.0
:: Description: Automates pushing Burp CA cert to Android emulator on Windows

set "LOGDIR=logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set "LOGFILE=%LOGDIR%\install-%DATE:/=-%_%TIME::=-%.log"

echo [INFO] Logging to %LOGFILE%

:: ============ Dependency Check ============ ::
where adb >nul 2>&1 || (
    echo [ERROR] adb not found. Please install Android Platform Tools and add them to PATH.
    exit /b 1
)
where openssl >nul 2>&1 || (
    echo [ERROR] openssl not found. Please install OpenSSL and add it to PATH.
    exit /b 1
)

:: ============ Get Cert File ============ ::
set /p CERT="Enter full path to cert.der: "
if not exist "%CERT%" (
    echo [ERROR] File not found: %CERT%
    exit /b 1
)

:: ============ Convert to PEM and Hash ============ ::
set "TEMPDIR=%TEMP%\burpcert_%RANDOM%"
mkdir "%TEMPDIR%"
set "PEMFILE=%TEMPDIR%\burp.pem"

openssl x509 -inform der -in "%CERT%" -out "%PEMFILE%" || (
    echo [ERROR] Failed to convert certificate.
    exit /b 1
)

for /f %%A in ('openssl x509 -subject_hash_old -in "%PEMFILE%"') do (
    set "CERTNAME=%%A.0"
)

ren "%PEMFILE%" "!CERTNAME!"

:: ============ ADB Steps ============ ::
echo [INFO] Checking ADB connection...
adb get-state | findstr /i "device" >nul || (
    echo [ERROR] No device detected. Please ensure emulator is running.
    exit /b 1
)

adb root
adb remount

:: ============ Backup Old Cert ============ ::
adb shell "if [ -f /system/etc/security/cacerts/!CERTNAME! ]; then cp /system/etc/security/cacerts/!CERTNAME! /system/etc/security/cacerts/!CERTNAME!.backup.%DATE:/=-%_%TIME::=-%; fi"

:: ============ Push New Cert ============ ::
adb push "%TEMPDIR%\!CERTNAME!" /system/etc/security/cacerts/
adb shell chmod 644 /system/etc/security/cacerts/!CERTNAME!
adb reboot

echo [INFO] Installation complete! Pushed as !CERTNAME!
rd /s /q "%TEMPDIR%"
echo [INFO] Please wait for the emulator to reboot.