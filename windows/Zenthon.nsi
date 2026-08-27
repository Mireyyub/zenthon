!include "MUI2.nsh"
!include "MUI2.nsh"

!define APP_NAME "Zenthon AI Platform"
!define APP_EXE "Zenthon.exe"
!define PROJECT_DIR "${__FILEDIR__}\.."

Name "${APP_NAME}"
OutFile "${PROJECT_DIR}\dist\Zenthon-Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\Zenthon"
InstallDirRegKey HKCU "Software\Zenthon" "InstallDir"
RequestExecutionLevel user

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetShellVarContext current
  SetOutPath "$INSTDIR"
  File /r "${PROJECT_DIR}\dist\Zenthon\*.*"
  CreateDirectory "$LOCALAPPDATA\Zenthon"
  CreateDirectory "$SMPROGRAMS\Zenthon AI Platform"
  CreateShortCut "$SMPROGRAMS\Zenthon AI Platform\Zenthon AI Platform.lnk" "$INSTDIR\${APP_EXE}"
  CreateShortCut "$DESKTOP\Zenthon AI Platform.lnk" "$INSTDIR\${APP_EXE}"
  WriteRegStr HKCU "Software\Zenthon" "InstallDir" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Zenthon" "DisplayName" "${APP_NAME}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Zenthon" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Zenthon" "DisplayVersion" "1.0.0"
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Zenthon" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Zenthon" "NoRepair" 1
  WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section /o "Start Zenthon with Windows" SEC_AUTOSTART
  SetShellVarContext current
  CreateShortCut "$SMSTARTUP\Zenthon AI Platform.lnk" "$INSTDIR\${APP_EXE}"
SectionEnd

Section "Uninstall"
  SetShellVarContext current
  Delete "$SMSTARTUP\Zenthon AI Platform.lnk"
  Delete "$DESKTOP\Zenthon AI Platform.lnk"
  Delete "$SMPROGRAMS\Zenthon AI Platform\Zenthon AI Platform.lnk"
  RMDir "$SMPROGRAMS\Zenthon AI Platform"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Zenthon"
  DeleteRegKey HKCU "Software\Zenthon"
  RMDir /r "$INSTDIR"
SectionEnd
