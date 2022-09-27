; Voice downloader
; by Mateo C
#include <guiConstantsEx.au3>
#include <InetConstants.au3>
#include "json.au3"
#INCLUDE "miscstring.au3"
#include "net.au3"
#include "progress.au3"
#include "reader.au3"
#include "translator.au3"
Global $iError = 0
Global $sVd_ver = "1.0", $sConfigPath = @ScriptDir & "\Config\config.st"
GLOBAL $sServerPath = iniRead(@ScriptDir &"\config\config.st", "general", "server path", "")
global $sVPacksDir = $sServerPath &"\data"
; #FUNCTION# ====================================================================================================================
; Name ..........: downloadvoices
; Description ...: this is the voice downloader from blind text, adapted for Tt4VeTube
; Syntax ........: downloadvoices()
; Parameters ....: None
; Return values .: None
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: No
; ===============================================================================================================================
Func downloadvoices($sURL = DEFAULT, $sMode = default)
	if $sURL = default then $sURL = "https://github.com/metalalchemist/vetube/blob/main/plugins/tt4VeTube/server/voices.json?raw=true"
	if $sMode = default then $sMode = "local"
	Global $iOldMode = Opt("GUIOnEventMode", 1)
	local $dVoicelist
	local $sVdata
	If Not FileExists($sVPacksDir) Then DirCreate($sVPacksDir)
	if $sMode = "local" then
		if not FileExists($sServerPath &"\voices.json") then return SetError(1, 0, "")
	elseif $sMode = "online" then
		$hVoices = InetGet($sURL, $sServerPath &"\voices.json", $INET_FORCERELOAD, $INET_DOWNLOADBACKGROUND)
		Do
			Sleep(250)
		Until InetGetInfo($hVoices, $INET_DOWNLOADCOMPLETE)
		InetClose($hVoices)
		if @error then return seterror(2, 0, "")
	else
		return SetError(3, 0, "")
	EndIf
	$sVdata = _GetFileData($sServerPath &"\voices.json")
	Global $hGuilist = GUICreate(translate($lng, "Download voices"))
	$idLabellist = GUICtrlCreateLabel(translate($lng, "List of available voices") & ": ", 25, 50, 200, 20)
	Global $idlist = GUICtrlCreateList("", 120, 50, 120, 30)
	GUICtrlSetLimit(-1, 200)
	Global $idBtnTest = GUICtrlCreateButton(translate($lng, "Preview"), 160, 50, 120, 30)
	GUICtrlSetOnEvent(-1, "previewvoice")
	Global $idBtnDownload = GUICtrlCreateButton(translate($lng, "Download"), 160, 110, 120, 30)
	GUICtrlSetOnEvent(-1, "downloadvoice")
	Global $idBtnClose = GUICtrlCreateButton(translate($lng, "Close"), 160, 150, 120, 30)
	GUICtrlSetOnEvent(-1, "closeddialogue")
	if not $sVdata = "" then
		GLOBAL $oVoicesJson = Json_decode($sVdata)
		Global $aLoTengo = Json_ObjGetKeys($oVoicesJson)
		$iVoiceCount = Json_ObjGetCount($oVoicesJson)
		GUICtrlSetData($idlabellist, translate($lng, "List of available voices") & ": " & $iVoiceCount)
		For $iColoca = 0 To uBound($aLoTengo) -1
			GUICtrlSetData($idlist, $aLoTengo[$iColoca])
		Next
		speaking(translate($lng, "Loaded"))
		GUISetOnEvent($GUI_EVENT_CLOSE, "closeddialogue")
		GUISetState(@SW_SHOW)
	Else
		;MsgBox(16, "Error", "An error occurred while getting the list of voices. This is because the server may be down or because of your internet connection.")
		return SetError(4, 0, "")
	EndIf
EndFunc   ;==>downloadvoices
; #FUNCTION# ====================================================================================================================
; Name ..........: previewvoice
; Description ...: download and play a preview of the voice that has been selected
; Syntax ........: previewvoice()
; Parameters ....: None
; Return values .: None
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: No
; ===============================================================================================================================
Func previewvoice()
	$voicestr = GUICtrlRead($idlist)
	$sampleURL = "https://github.com/metalalchemist/vetube/blob/main/plugins/tt4VeTube/server/data/samples/" & $voicestr & ".mp3?raw=true"
	$sampledata = InetGet($sampleURL, @TempDir & "\" & $voicestr & ".mp3", 1, 1)
	Do
		Sleep(250)
	Until InetGetInfo($sampledata, $INET_DOWNLOADCOMPLETE)
	Local $iBytesSize = InetGetInfo($sampledata, $INET_DOWNLOADREAD)
	InetClose($sampledata)
	Switch $iBytesSize
		Case 0
			$error = 1
			MsgBox(16, translate($lng, "Error"), translate($lng, "Unable to connect to the server. The server went down or you don't have an internet connection."))
		Case 1 To 2
			$error = 1
			MsgBox(16, "Error", "The data received on the server is too small.")
		Case Else
			$error = 0
	EndSwitch
	If $error = 0 Then
		$sPathToSample = @TempDir & "\" & $voicestr & ".mp3"
		SoundPlay($sPathToSample, 1)
		sleep(500)
		FileDelete(@TempDir & "\" & $voicestr & ".mp3")
	EndIf
EndFunc   ;==>previewvoice
; #FUNCTION# ====================================================================================================================
; Name ..........: downloadvoice
; Description ...: The function that starts the download of the selected voice
; Syntax ........: downloadvoice()
; Parameters ....: None
; Return values .: None
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: No
; ===============================================================================================================================
Func downloadvoice()
	$searchstr = GUICtrlRead($idlist)
	$sVoiceToDownload = json_get($oVoicesJson, '["' &$searchstr &'"]')
	GUIDelete($hGuilist)
	ProgressOn(translate($lng, "Downloading..."), "Please wait...", "0%", 100, 100, 16)
	WinActivate(translate($lng, "Downloading..."))
	$iPlaces = 2
	local $sD = "https://drive.google.com/uc?id="
	local $sUuid
	local $urltodwn
	IF _String_startsWhit($sVoiceToDownload, "1") then
		$sUuid = __GenerateUUID
		$urltodwn = $sD & $sVoiceToDownload &"&amp;confirm=t&amp;uuid=" &$sUuid
	Else
		$urltodwn = $sVoiceToDownload
	EndIf
	$download1 = InetGet($urltodwn, $sVPacksDir & "\" &$searchstr & ".pt", 1, 1)
	$Size = InetGetSize($urltodwn)
	While Not InetGetInfo($download1, 2)
		Sleep(50)
		$Size2 = InetGetInfo($download1, 0)
		$Percent = Int($Size2 / $Size * 100)
		$iSize = $Size - $Size2
		;CreateAudioProgress($Percent)
		;speaking($Percent & "%")
		ProgressSet($Percent, _GetDisplaySize($iSize, $iPlaces = 2) & " " & translate($lng, "remaining") & $Percent & " " & translate($lng, "percent completed"))
	WEnd
	Sleep(1000)
	ProgressOff()
	$descargado = MsgBox(4, translate($lng, "Information"), translate($lng, "The voice has been downloaded successfully! Do you want to set it as default? You can change voices in options."))
	If $descargado = 6 Then
		IniWrite(@ScriptDir &"\config\config.st", "voice settings", "voice", $searchstr)
	Else
		If IniRead(@ScriptDir &"\config\config.st", "voice settings", "Voice", "") = "" Then MsgBox(16, translate($lng, "Error"), translate($lng, "Hmm... There is no voice set as the default. It seems that this is the first voice you download, therefore I recommend setting it or downloading another voice."))
	EndIf
EndFunc   ;==>downloadvoice
; #FUNCTION# ====================================================================================================================
; Name ..........: closeddialogue
; Description ...: Close the voice downloader window
; Syntax ........: closeddialogue()
; Parameters ....: None
; Return values .: None
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: No
; ===============================================================================================================================
Func closeddialogue()
	GUIDelete($hGuilist)
	Opt("GUIOnEventMode", $iOldMode)
EndFunc   ;==>closeddialogue
; #FUNCTION# ====================================================================================================================
; Name ..........: _GetDisplaySize
; Description ...: get information relevant to downloads
; Syntax ........: _GetDisplaySize($iTotalDownloaded, Const $iPlaces)
; Parameters ....: $iTotalDownloaded    - A integer value.
;                  Const $iPlaces       - An unknown value.
; Return values .: None
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: No
; ===============================================================================================================================
Func _GetDisplaySize($iTotalDownloaded, Const $iPlaces)
	Local Static $aSize[4] = ["Bytes", "KB", "MB", "GB"]
	For $i = 0 To 3
		$iTotalDownloaded /= 1024
		If (Int($iTotalDownloaded) = 0) Then Return Round($iTotalDownloaded * 1024, $iPlaces) & " " & $aSize[$i]
	Next
EndFunc   ;==>_GetDisplaySize
