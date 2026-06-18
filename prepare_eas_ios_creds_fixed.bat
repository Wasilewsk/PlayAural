@echo off
REM prepare_eas_ios_creds_fixed.bat
REM Safer version: avoids parenthesized IF blocks that can cause ": was unexpected at this time." errors.
SETLOCAL

REM --- Defaults ---
SET "SRC_CRED_DIR=C:\Users\natan\Downloads\VIETNAM AIRLINES JSC 2\VIETNAM AIRLINES JSC 2"
SET "PROJECT_DIR=C:\Users\natan\PlayAural\mobile_client"

REM --- Get arguments or prompt ---
IF NOT "%~1"=="" SET "P12_NAME=%~1"
IF NOT "%~2"=="" SET "MOBILEPROV_NAME=%~2"

IF DEFINED P12_NAME GOTO checkprov
SET /P P12_NAME=Enter .p12 filename (e.g. cert.p12): 

:checkprov
IF DEFINED MOBILEPROV_NAME GOTO copyfiles
SET /P MOBILEPROV_NAME=Enter .mobileprovision filename (e.g. profile.mobileprovision): 

:copyfiles
SET "SRC_P12=%SRC_CRED_DIR%\%P12_NAME%"
SET "SRC_PROV=%SRC_CRED_DIR%\%MOBILEPROV_NAME%"

IF NOT EXIST "%SRC_P12%" (
  ECHO ERROR: %SRC_P12% not found.
  PAUSE
  EXIT /B 1
)
IF NOT EXIST "%SRC_PROV%" (
  ECHO ERROR: %SRC_PROV% not found.
  PAUSE
  EXIT /B 1
)

ECHO Creating creds folder in project...
MKDIR "%PROJECT_DIR%\ios-creds" 2>NUL

ECHO Copying files...
COPY /Y "%SRC_P12%" "%PROJECT_DIR%\ios-creds\" >NUL
COPY /Y "%SRC_PROV%" "%PROJECT_DIR%\ios-creds\" >NUL

ECHO.
ECHO Checking for npm...
WHERE npm >NUL 2>&1
IF ERRORLEVEL 1 (
  ECHO npm not found. Install Node.js (https://nodejs.org/) and re-run this script.
  PAUSE
  EXIT /B 1
)

ECHO Installing eas-cli (may require admin)...
npm install -g eas-cli
IF ERRORLEVEL 1 (
  ECHO Failed to install eas-cli. Try running this script from an elevated prompt.
  PAUSE
  EXIT /B 1
)

ECHO.
ECHO Changing to project folder: "%PROJECT_DIR%"
CD /D "%PROJECT_DIR%"

ECHO.
ECHO Now logging into Expo/EAS. Enter your Expo credentials in the next prompt.
eas login
IF ERRORLEVEL 1 (
  ECHO eas login failed. Exiting.
  PAUSE
  EXIT /B 1
)

ECHO.
ECHO Credentials files copied to: "%PROJECT_DIR%\ios-creds"
ECHO When the credentials manager opens, choose the options to upload your own Distribution Certificate (.p12) and Provisioning Profile, and provide the files from that folder.
PAUSE

REM Launch interactive credentials manager
eas credentials --platform ios

ECHO.
ECHO After uploading credentials, run your build, e.g.:
ECHO   eas build --platform ios --profile production
PAUSE
ENDLOCAL
EXIT /B 0
