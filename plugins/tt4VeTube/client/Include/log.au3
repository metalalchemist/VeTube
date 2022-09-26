#include-once
#include <fileConstants.au3>
Global $ifSave = IniRead(@ScriptDir &"\config\config.st", "General settings", "Save Logs", "")
Select
	Case $ifSave = ""
		IniWrite(@ScriptDir &"\config\config.st", "General settings", "Save Logs", "No")
		$ifSave = "no"
	Case $ifSave = "no"
		sleep(10)
	Case else
		Local $logfile = FileOpen("logs\" & @YEAR & @MON & @MDAY & ".log", $FC_OVERWRITE + $FC_CREATEPATH)
EndSelect
; #FUNCTION# ====================================================================================================================
; Name ..........: writeinlog
; Description ...: write a text or information to the log
; Syntax ........: writeinlog($text)
; Parameters ....: $text                - A dll struct value.
; Return values .: None
; Author ........: Mateo Cedillo
; Modified ......: 
; Remarks .......: 
; Related .......: 
; Link ..........: 
; Example .......: No
; ===============================================================================================================================
Func writeinlog($text)
	If $ifSave = "yes" Then
		FileWrite($logfile, @YEAR & "-" & @MON & "-" & @MDAY & " " & @HOUR & ":" & @MIN & ": " & $text & @CRLF)
	EndIf
EndFunc   ;==>writeinlog
; #FUNCTION# ====================================================================================================================
; Name ..........: ___DeBug
; Description ...: write an error to the log
; Syntax ........: ___DeBug($iError, $sAction)
; Parameters ....: $iError              - A integer value.
;                  $sAction             - A string value.
; Return values .: None
; Author ........: Mateo Cedillo
; Modified ......: 
; Remarks .......: 
; Related .......: 
; Link ..........: 
; Example .......: No
; ===============================================================================================================================
Func ___DeBug($iError, $sAction)
	Switch $iError
		Case -1
			FileWrite($logfile, @CRLF & "-" & $sAction & @CRLF)
		Case 0
			FileWrite($logfile, @CRLF & "+" & $sAction & " - OK" & @CRLF)
		Case Else
			FileWrite($logfile, @CRLF & "!" & $sAction & " - FAILED" & @CRLF)
			Exit
	EndSwitch
EndFunc   ;==>___DeBug
