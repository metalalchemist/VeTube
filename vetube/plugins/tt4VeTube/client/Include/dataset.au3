; Dataset manager for FakeYou Tacotron 2.
;Author: Mateo Cedillo
; Fixes by @Subz
#include <Array.au3>
#include <File.au3>
#include <sound.au3>
$sFakeYouDatasetManager_Ver = 0.2.1
; #FUNCTION# ====================================================================================================================
; Name ..........: _changeDatasetOrder
; Description ...: changes the order of wavs and transcripts in the dataset
; Syntax ........: _changeDatasetOrder($sPath, $sListFileName, $nNum)
; Parameters ....: $sPath               - The dataset path.
;                  $sListFileName       - The path containing the list of transcripts.
;                  $nNum                - The number from where the order will be changed.
; Return values .: None
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: Yes
; ===============================================================================================================================
Func _changeDatasetOrder($sPath, $sListFileName, $nNum)
	$hFiles = FileFindFirstFile($sPath & "\wavs\*.wav")
	If $hFiles = -1 Then
		MsgBox(16, "Error", "No wavs.")
		Exit
	EndIf
	$aFile = FileReadToArray($sPath & "\" & $sListFileName)
	$iLines = @extended
	If @error Then
		MsgBox(16, "Error", "There was an error reading the filelist. @error: " & @error)
		Exit
	EndIf
	Local $sFileName = "", $iResult = 0
	Local $aTexts[]
	Local $aDivList
	For $i = 0 To $iLines - 1
		$aDivList = StringSplit($aFile[$i], "|")
		$aTexts[$i] = $aDivList[2]
	Next
	$hFileOpen = FileOpen($sPath & "\" & StringTrimRight($sListFileName, 4) & "_converted.txt", 1)
	If $hFileOpen = -1 Then
		MsgBox(16, "Error", "the converted file could not be created.")
		Exit
	EndIf
	Local $nItem = 0
	Local $sFilesList = ""
	While 1
		$sFileName = FileFindNextFile($hFiles)
		If @error Then ExitLoop
		$sFilesList &= $sFileName & "|"
		Sleep(50)
	WEnd
	$sFilesList = StringTrimRight($sFilesList, 1)
	$aFileslist = StringSplit($sFilesList, "|")
	For $IProcess = 1 To $aFileslist[0]
		FileMove($sPath & "\wavs\" & $aFileslist[$IProcess], $sPath & "\wavs\" & $nNum & ".wav", $FC_OVERWRITE)
		FileWriteLine($hFileOpen, "wavs/" & $nNum & ".wav|" & $aTexts[$nItem])
		$nItem = $nItem + 1
		$nNum = $nNum + 1
		Sleep(50)
	Next
	FileClose($hFileOpen)
	MsgBox(0, "Success", "the dataset has been changed.")
EndFunc   ;==>_changeDatasetOrder
; #FUNCTION# ====================================================================================================================
; Name ..........: _AhoTtsDataset2Tacotron
; Description ...: Convert an AhoTts dataset to a dataset compatible for training with Tacotron 2.
; Syntax ........: _AhoTtsDataset2Tacotron($sPath[, $sListFileName = "list.txt"])
; Parameters ....: $sPath               - The dataset folder.
;                  $sListFileName       - [optional] The name of the file that contains the list of transcripts. Default is "list.txt".
; Return values .: None
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: Yes
; ===============================================================================================================================
Func _AhoTtsDataset2Tacotron($sPath, $sListFileName = "list.txt")
	$hFiles = FileFindFirstFile($sPath & "\*.wav")
	If $hFiles = -1 Then
		MsgBox(16, "Error", "No wavs.")
		Exit
	ElseIf Not FileExists($sListFileName) Then
		MsgBox(16, "Error", "List file not found")
		Exit
	EndIf
	$aFile = FileReadToArray($sListFileName)
	$iLines = @extended
	If @error Then
		MsgBox(16, "Error", "There was an error reading the filelist. @error: " & @error)
		Exit
	EndIf
	$hFileOpen = FileOpen($sPath & "\" & StringTrimRight($sListFileName, 4) & "_converted.txt", 1)
	If $hFileOpen = -1 Then
		MsgBox(16, "Error", "the converted file could not be created.")
		Exit
	EndIf
	Local $nNum = 1
	Local $sFilesList = ""
	While 1
		$sFileName = FileFindNextFile($hFiles)
		If @error Then ExitLoop
		$sFilesList &= $sFileName & "|"
		Sleep(50)
	WEnd
	$sFilesList = StringTrimRight($sFilesList, 1)
	$aFileslist = StringSplit($sFilesList, "|")
	If Not FileExists($sPath & "\wavs") Then DirCreate($sPath & "\wavs")
	For $IProcess = 1 To $aFileslist[0]
		FileMove($sPath & "\" & $aFileslist[$IProcess], $sPath & "\wavs\" & $nNum & ".wav", $FC_OVERWRITE)
		FileWriteLine($hFileOpen, "wavs/" & $nNum & ".wav|" & $aFile[$IProcess - 1])
		$nNum = $nNum + 1
		Sleep(50)
	Next
	FileClose($hFileOpen)
	MsgBox(0, "Success", "the dataset has been converted.")
EndFunc   ;==>_AhoTtsDataset2Tacotron
; #FUNCTION# ====================================================================================================================
; Name ..........: _DatasetFixList
; Description ...: Fix certain symbols that are in the transcript so that we can train without problems.
; Syntax ........: _DatasetFixList($sListPath[, $sLang = "en"])
; Parameters ....: $sListPath           - The path of the transcript file.
;                  $sLang               - [optional] The language in which the transcript is written. Default is "en" (english).
; Return values .: None
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: Yes
; ===============================================================================================================================
Func _DatasetFixList($sListPath, $sLang = "en")
	Local $sReplacements = 0
	Switch $sLang
		Case "en"
			Local $aSimbols[][2] = [["ñ", "n"], ["1", "one"], ["2", "two"], ["3", "three"], ["4", "four"], ["5", "five"], ["6", "six"], ["7", "seven"], ["8", "eight"], ["9", "nine"], ["0", "zero"], ["...", ","]]
		Case "es"
			Local $aSimbols[][] = [["ñ", "ni"], ["1", "uno"], ["2", "dos"], ["3", "tres"], ["4", "cuatro"], ["5", "cinco"], ["6", "seis"], ["7", "siete"], ["8", "ocho"], ["9", "nueve"], ["0", "cero"], ["...", ","]]
	EndSwitch
	If Not FileExists($sListPath) Then
		MsgBox(16, "Error", "There is no list specified.")
		Exit
	EndIf
	Local $aFile = FileReadToArray($sListPath)
	If @error Then
		MsgBox(16, "Error", "Cannot load file list.")
		Exit
	EndIf
	$iCount = @extended
	Local $i = 0
	Local $aWavList[]
	Local $aFile2 = $aFile
	Local $aSplit[]
	$hFileOpen = FileOpen(StringTrimRight($sListPath, 4) & "_fixed.txt", 1)
	If $hFileOpen = -1 Then
		MsgBox(16, "Error", "the fixed list could not be created.")
		Exit
	EndIf

	While $i <= UBound($aFile, 1) - 1
		$aWavList[$i] = StringSplit($aFile[$i], "|")[1]
		For $iStart = 0 To UBound($aSimbols, 1) - 1
			If StringInStr(StringSplit($aFile[$i], "|")[2], $aSimbols[$iStart][0]) Then
				$aFile2[$i] = StringReplace(StringSplit($aFile[$i], "|")[2], $aSimbols[$iStart][0], $aSimbols[$iStart][1])
				$sReplacements = $sReplacements + @extended
				;ConsoleWrite("a match was found in line " &$I &" of " &$iCount &". Simbol: " &$aSimbols[$iStart][0] &" = " &$aSimbols[$iStart][1] &"." &@crlf)
			Else
				$aSplit = StringSplit($aFile2[$i], "|")
				If $aSplit[0] = 2 Then
					$aFile2[$i] = $aSplit[2]
				Else
				EndIf
				ContinueLoop
			EndIf
			Sleep(10)
		Next
		FileWriteLine($hFileOpen, $aWavList[$i] & "|" & $aFile2[$i])
		$i = $i + 1
	WEnd
	FileClose($hFileOpen)
	SetError(Null, $sReplacements)
EndFunc   ;==>_DatasetFixList
; #FUNCTION# ====================================================================================================================
; Name ..........: _DatasetWavsDuration
; Description ...: Gets the total duration of the dataset.
; Syntax ........: _DatasetWavsDuration([$sWavsPath = @ScriptDir & "\wavs"])
; Parameters ....: $sWavsPath           - [optional] The audios path (wavs). Default is @ScriptDir & "\wavs".
; Return values .: None
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: No
; ===============================================================================================================================
Func _DatasetWavsDuration($sWavsPath = @ScriptDir & "\wavs")
	If Not FileExists($sWavsPath) Then Return SetError(1, 0, "")
	$hWavs = FileFindFirstFile($sWavsPath & "\*.wav")
	If $hWavs = -1 Then Return SetError(2, 0, "")
	Local $sFileName = "", $iResult = 0, $aSound
	While 1
		$sFileName = FileFindNextFile($hWavs)
		If @error Then ExitLoop
		$iResult = $iResult + __Dataset_GetAudioDuration($sWavsPath & "\" & $sFileName)
		If @error Then
			Return SetError(3, 0, "")
			ExitLoop
		EndIf
		Sleep(10)
	WEnd
	$iSecs = Int($iResult / 1000)
	$iHours = Int($iSecs / 3600)
	$iSecs = Mod($iSecs, 3600)
	$iMins = Int($iSecs / 60)
	$iSecs2 = Round(Mod($iSecs, 60))
	Return $iHours & ":" & $iMins & ":" & $iSecs2
EndFunc   ;==>_DatasetWavsDuration
; #INTERNAL_USE_ONLY# ===========================================================================================================
; Name ..........: __Dataset_GetAudioDuration
; Description ...: Function that helps to obtain the audio duration.
; Syntax ........: __Dataset_GetAudioDuration($sFile[, $iMaxSeconds = 20])
; Parameters ....: $sFile               - The name of the audio file to examine.
;                  $iMaxSeconds         - [optional] an integer value that contains the maximum number of seconds allowed. Default is 20.
; Return values .: None
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: No
; ===============================================================================================================================
Func __Dataset_GetAudioDuration($sFile, $iMaxSeconds = 20)
	$aSound = _SoundOpen($sFile)
	If @error Then Return SetError(1, 0, "")
	$sLenght = _SoundLength($aSound, 2)
	$aLenghtFormat = StringSplit(_SoundLength($aSound, 1), ":")
	If $aLenghtFormat[3] >= $iMaxSeconds Then ConsoleWrite("Warning: the duration of " & $sFile & " It lasts longer than " & $aLenghtFormat[3] & @CRLF)
	Return $sLenght
EndFunc   ;==>__Dataset_GetAudioDuration
; #FUNCTION# ====================================================================================================================
; Name ..........: _Dataset_CreateTranscription
; Description ...: Create a transcript (blank list) either based on a maximum number of items or by detecting the wavs.
; Syntax ........: _Dataset_CreateTranscription($sFileName, $iMaxItems[, $sWavsPath = @ScriptDir & "\wavs"])
; Parameters ....: $sFileName           - The filename of the new filelist to create.
;                  $iMaxItems           - an integer value containing the maximum n[umber of elements to create.
;                  $sWavsPath           - [optional] A string containing the path of the wavs. Default is @ScriptDir & "\wavs".
; Return values .: None
; Author ........: Mateo Cedillo, fixes by Subz
; Modified ......:
; Remarks .......: To create a blank transcript by detecting wavs, simply pass "FW" (from wavs) to the $iMaxItems parameter.
; Related .......:
; Link ..........:
; Example .......: Yes
; ===============================================================================================================================
Func _Dataset_CreateTranscription($sFileName, $iMaxItems, $sWavsPath = @ScriptDir & "\wavs")
	If FileExists($sFileName) Then Return SetError(1, 0, "") ;The transcript file already exists.
	Local $hFile = FileOpen($sFileName, 2)
	If $hFile = -1 Then Return SetError(2, 0, "") ;the transcription file could not be created.
	If $iMaxItems = "FW" Then
		$iMaxItems = 0
		Local $aFileList = _FileListToArrayRec($sWavsPath, "*.wav", 1)
		If @error Then Return SetError(3, 0, "")
		;_ArraySort($aFileList)
		If @error Then Return SetError(4, 0, "")
		FileWrite($hFile, "wavs/" & _ArrayToString($aFileList, "|" & @CRLF & "wavs/", 1, -1, @CRLF) & "|" & @CRLF)
		FileClose($hFile)
	Else
		If Not IsInt($iMaxItems) Then Return SetError(5, 0, "") ;The maximum number of elements is not an integer.
		For $i = 1 To $iMaxItems
			FileWriteLine($hFile, "wavs/" & $i & ".wav|")
		Next
		FileClose($hFile)
	EndIf
	Return True
EndFunc   ;==>_Dataset_CreateTranscription
