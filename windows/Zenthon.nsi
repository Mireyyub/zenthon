!include "MUI2.nsh"
!define APP_NAME "Zenthon AI Platform"
!define APP_EXE "Zenthon.exe"

Name "${APP_NAME}"
OutFile "dist\Zenthon-Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\Zenthon"
RequestExecutionLevel user

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"
  File /r "dist\Zenthon\*.*"
  CreateDirectory "$SMPROGRAMS\Zenthon AI Platform"
  CreateShortCut "$SMPROGRAMS\Zenthon AI Platform\Zenthon AI Platform.lnk" "$INSTDIR\${APP_EXE}"
  CreateShortCut "$DESKTOP\Zenthon AI Platform.lnk" "$INSTDIR\${APP_EXE}"
  CreateShortCut "$SMSTARTUP\Zenthon AI Platform.lnk" "$INSTDIR\${APP_EXE}"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$SMSTARTUP\Zenthon AI Platform.lnk"
  Delete "$DESKTOP\Zenthon AI Platform.lnk"
  Delete "$SMPROGRAMS\Zenthon AI Platform\Zenthon AI Platform.lnk"
  RMDir "$SMPROGRAMS\Zenthon AI Platform"
  RMDir /r "$INSTDIR"
SectionEnd
