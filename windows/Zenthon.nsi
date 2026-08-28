; Leon / Zenthon Windows installer (Phase 11)
; Input:  dist\Zenthon\*  (from scripts\build_windows.ps1)
; Output: dist\Zenthon-Setup.exe
; User-level install; startup shortcut is OPTIONAL (not forced).

!include "MUI2.nsh"

!define APP_NAME "Leon"
!define APP_FULL "Leon AI Platform"
!define APP_EXE "Zenthon.exe"
!define PROJECT_DIR "${__FILEDIR__}\.."

Name "${APP_FULL}"
OutFile "${PROJECT_DIR}\dist\Zenthon-Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\Leon"
RequestExecutionLevel user

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Section "Leon core (required)" SecCore
  SectionIn RO
  SetOutPath "$INSTDIR"
  File /r "${PROJECT_DIR}\dist\Zenthon\*.*"
  CreateDirectory "$SMPROGRAMS\Leon"
  CreateShortCut "$SMPROGRAMS\Leon\Leon.lnk" "$INSTDIR\${APP_EXE}"
  CreateShortCut "$DESKTOP\Leon.lnk" "$INSTDIR\${APP_EXE}"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  ; Write simple version stamp
  FileOpen $0 "$INSTDIR\VERSION.txt" w
  FileWrite $0 "Leon 0.8.0 Phase 11 packaging$\r$\n"
  FileWrite $0 "Entry: leon_desktop.py / Zenthon.exe$\r$\n"
  FileWrite $0 "API default: http://127.0.0.1:8000$\r$\n"
  FileClose $0
SectionEnd

Section /o "Start with Windows (optional)" SecStartup
  CreateShortCut "$SMSTARTUP\Leon.lnk" "$INSTDIR\${APP_EXE}"
SectionEnd

Section "Uninstall"
  Delete "$SMSTARTUP\Leon.lnk"
  Delete "$DESKTOP\Leon.lnk"
  Delete "$SMPROGRAMS\Leon\Leon.lnk"
  RMDir "$SMPROGRAMS\Leon"
  RMDir /r "$INSTDIR"
SectionEnd

LangString DESC_SecCore ${LANG_ENGLISH} "Leon desktop shell + cognitive core (PyInstaller)."
LangString DESC_SecStartup ${LANG_ENGLISH} "Launch Leon when Windows starts (optional)."

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecCore} $(DESC_SecCore)
  !insertmacro MUI_DESCRIPTION_TEXT ${SecStartup} $(DESC_SecStartup)
!insertmacro MUI_FUNCTION_DESCRIPTION_END
