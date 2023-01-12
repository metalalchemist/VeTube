#include "audio.au3"
#include-once
Global $count
Global $progress_ver = "1.2.1"
; #FUNCTION# ====================================================================================================================
; Name ..........: CreateBeepProgress
; Description ...: create a progress bar but using the default AU3 beep func
; Syntax ........: CreateBeepProgress($numero)
; Parameters ....: $numero              - A floating point number value.
; Return values .: None
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: No
; ===============================================================================================================================
Func CreateBeepProgress($numero)
	If $numero < 0 or $numero > 100 Then
		;msgbox(0, "Error", "Wrong value")
	EndIf
	Local $iFreqStart = 110
	Local $iFreqEnd = 2.00
	$count = 0
	$count = $numero * 16.0
	$progress = $iFreqStart * 1.5
	Beep($count, 60)
EndFunc   ;==>CreateBeepProgress
; #FUNCTION# ====================================================================================================================
; Name ..........: CreateAudioProgress
; Description ...: create a progress bar with an audio file containing a sound with a small tone
; Syntax ........: CreateAudioProgress($numero)
; Parameters ....: $numero              - A floating point number value.
; Return values .: None
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: No
; ===============================================================================================================================
Func CreateAudioProgress($numero)
	If $numero <= 0 or $numero >= 100 Then
		;msgbox(0, "Error", "Wrong value")
	EndIf
	Local $iFreqStart = 0.01
	Local $iFreqEnd = 2.00
	$count = 0
	$tin = $device.opensound(@ScriptDir & "\sounds/progress.ogg", 0)
	$count = $numero * 0.04
	If $count = 0 Then
		$tin.pitchshift = 0.125
		$tin.play()
	Else
		$progress = $iFreqStart * 0.1
		$tin.pitchshift = $count
		$tin.play()
	EndIf
EndFunc   ;==>CreateAudioProgress
; #FUNCTION# ====================================================================================================================
; Name ..........: progresReverse
; Description ...: revert a progress bar
; Syntax ........: progresReverse()
; Parameters ....: None
; Return values .: None
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: Yes
; ===============================================================================================================================
Func progresReverse()
	Local $iFreqStart = 110
	Local $iFreqEnd = 2.00
	$tin = $device.opensound("sounds/progress.ogg", 0)
	For $iFreq = $iFreqEnd To $iFreqStart Step -0.02
		$tin.pitchshift = $iFreq
		$tin.play()
		$count = $count - 1
		Sleep(50)
	Next
	MsgBox(0, "_WinAPI_Beep Example", "Results: " & $count)
EndFunc   ;==>progresReverse
