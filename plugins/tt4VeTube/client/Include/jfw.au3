#include-once
$o_speech = ObjCreate("jfwapi")
;If @error Then return SetError(1, 0, "")
; #FUNCTION# ====================================================================================================================
; Name ..........: JFWSpeak
; Description ...: Speak the selected text, sending this text to the JAWS screen reader
; Syntax ........: JFWSpeak($text)
; Parameters ....: $text                - A dll struct value.
; Return values .: None
; Author ........: angel
; Modified ......: 
; Remarks .......: 
; Related .......: 
; Link ..........: 
; Example .......: No
; ===============================================================================================================================
Func JFWSpeak($text)
	if IsObj($o_speech) then
		$o_speech.saystring($text, -1)
		Return 1 ;
	Else
	return 0
EndIf
EndFunc   ;==>JFWSpeak
