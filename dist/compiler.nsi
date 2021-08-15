;--------------------------------
;Vars - This is probably the only thing you might need to change

  !define APPNAME "Bulk Whatsapp Sender" ; Also folder name as well btw
  !define RUNFILE "${APPNAME}.exe"
  !define VERSIONMAJOR 1    ; Only change on major release
  !define VERSIONMINOR 1    ; TODO: Update version every time you compile
  !define ICONFILE "myico.ico" ; Must be inside folder always
  !define COMPANYNAME "Bulk Whatsapp Sender"
  !define COMPANYURL "example.com"
  !define INSTALLSIZE 81000

  SetCompressor /SOLID lzma

;--------------------------------
;Include Modern UI

  !include "MUI2.nsh"

;--------------------------------
;General

  ;Name and file
  Name "${APPNAME}"
  ; Icon "${APPNAME}\${ICONFILE}"
  !define MUI_ICON "${APPNAME}\${ICONFILE}"
  !define MUI_UNICON "${APPNAME}\${ICONFILE}"
  OutFile "${APPNAME}_setup.exe"
  Unicode True

  ;Default installation folder
  InstallDir "$PROGRAMFILES\${APPNAME}"

  ;Get installation folder from registry if available
  ;InstallDirRegKey HKCU "Software\${APPNAME}" ""   ;FIXME: Yo figure out this later dhole..

  ;Request application privileges for Windows Vista
  RequestExecutionLevel admin

  ; Hide "Show details" button
  ShowInstDetails nevershow

;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING

;--------------------------------
;Pages

  !insertmacro MUI_PAGE_WELCOME
  !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES
  !insertmacro MUI_PAGE_FINISH

  !insertmacro MUI_UNPAGE_WELCOME
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES
  !insertmacro MUI_UNPAGE_FINISH

;--------------------------------
;Languages

  !insertmacro MUI_LANGUAGE "English"

;--------------------------------
;Installer Sections

Section "Core" core

  SectionIn RO ;Make it read-only / Required

  DetailPrint "Installing ${APPNAME}.."
  SetDetailsPrint none

  SetOutPath "$INSTDIR"

  ;Full folder add
  file /r "${APPNAME}\*"

  ;Hide specifics for Panchani...
  nsExec::Exec 'attrib /D +h +s "$INSTDIR\*"'
  nsExec::Exec 'attrib /D -h -s "$INSTDIR\logs"'
  nsExec::Exec 'attrib -h -s "$INSTDIR\${RUNFILE}"'

  ;Store installation folder
  ;WriteRegStr HKCU "Software\${APPNAME}" "" $INSTDIR  ; FIXME: Same #2 dhole

  ;Control panel entry
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "InstallLocation" "$\"$INSTDIR$\""
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$\"$INSTDIR\${ICONFILE}$\""
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${COMPANYNAME}"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "HelpLink" "$\"${COMPANYURL}$\""
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLUpdateInfo" "$\"${COMPANYURL}$\""
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLInfoAbout" "$\"${COMPANYURL}$\""
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}"
	WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
	WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMinor" ${VERSIONMINOR}
	# There is no option for modifying or repairing the install
	WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
	WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1
	# Set the INSTALLSIZE constant (!defined at the top of this script) so Add/Remove Programs can accurately report the size
	WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "EstimatedSize" ${INSTALLSIZE}

  ;Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

SectionEnd

Section "Start Menu shortcut" smshort

  createShortCut "$SMPROGRAMS\${APPNAME}.lnk" "$INSTDIR\${RUNFILE}" "" "$INSTDIR\${ICONFILE}"

SectionEnd

Section "Desktop shortcut" deskshort

  createShortCut "$desktop\${APPNAME}.lnk" "$INSTDIR\${RUNFILE}" "" "$INSTDIR\${ICONFILE}"

SectionEnd

;--------------------------------
;Descriptions

  ;Language strings
  LangString DESC_core ${LANG_ENGLISH} "Main program files required to run."
  LangString DESC_smshort ${LANG_ENGLISH} "Create a shortcut in your start menu."
  LangString DESC_deskshort ${LANG_ENGLISH} "Create a shortcut on your desktop."

  ;Assign language strings to sections
    !insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${core} $(DESC_core)
    !insertmacro MUI_DESCRIPTION_TEXT ${smshort} $(DESC_smshort)
    !insertmacro MUI_DESCRIPTION_TEXT ${deskshort} $(DESC_deskshort)
  !insertmacro MUI_FUNCTION_DESCRIPTION_END

;--------------------------------
;Uninstaller Section

Section "Uninstall"

  SetDetailsView hide
  SetDetailsPrint textonly
  DetailPrint "Uninstalling ${APPNAME}.."

  ; Remove start menu & desktop entries (even if they were not created in the first place)
  delete "$SMPROGRAMS\${APPNAME}.lnk"
  delete "$desktop\${APPNAME}.lnk"

  ; Maybe force stop app just in case it's still running
  nsExec::Exec 'taskkill /f /im "${RUNFILE}"'

  ; Remove files (warn: removes everything even logs and stuff)
  delete "$INSTDIR\*.*"
  RmDir /r "$INSTDIR"

  # Always delete uninstaller as the last action (already delete due to wildcard)
  ;Delete "$INSTDIR\Uninstall.exe"

  ;DeleteRegKey /ifempty HKLM "Software\${APPNAME}"  
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"

SectionEnd
