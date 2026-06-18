@echo off
REM prepare_eas_ios_creds.bat
REM Copies .p12 and .mobileprovision into mobile_client\ios-creds, installs eas-cli, logs in, and opens eas credentials manager.
SETLOCAL

REM --- Configure defaults (change if needed) ---
SET "SRC_CRED_DIR=C:\Users\natan\Downloads\VIETNAM AIRLINES JSC 2\VIETNAM AIRLINES JSC 2"
SET "PROJECT_DIR=C:\Users\natan\PlayAural\mobile_client"

REM --- Accept optional args: p12 filename and mobileprovision filename ---
IF "%~1"=="" (
  SET /P P12_NAME=Enter .p12 filename (e.g. cert.p12): 
) ELSE SET "P12_NAME=%~1"

IF "%~2"=="" (
  SET /P MOBILEPROV_NAME=Enter .mobileprovision filename (e.g. profile.mobileprovision): 
) ELSE SET "MOBILEPROV_NAME=%~2"

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

ECHO Installing eas-cli (might require admin privileges)...
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
