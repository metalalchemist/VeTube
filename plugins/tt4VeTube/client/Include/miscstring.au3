; misc string functions
; by Mateo C
; #FUNCTION# ====================================================================================================================
; Name ..........: _String_startsWhit
; Description ...: Checks if the string starts with a specific criteria, similar to the function in Python.
; Syntax ........: _String_startsWhit($sString, $sStart)
; Parameters ....: $sString             - The string to be examined.
;                  $sStart              - A value (string) to check.
; Return values .: True if the string starts with that value; otherwise, return false. If $sString is not a string, return @error.
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: Yes
; ===============================================================================================================================
Func _String_startsWhit($sString, $sStart)
	If Not IsString($sString) Then Return SetError(1, 0, "")
	Return $sStart = StringLeft($sString, 1)
EndFunc   ;==>_String_startsWhit
; #FUNCTION# ====================================================================================================================
; Name ..........: _String_EndsWhit
; Description ...: Checks if the string ends with a specific criteria, similar to the function in Python.
; Syntax ........: _String_EndsWhit($sString, $sEnd)
; Parameters ....: $sString             - The string to be examined.
;                  $sEnd                - A value (string) to check.
; Return values .: True if the string ends with that value; otherwise, return false. If $sString is not a string, return @error
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: Yes
; ===============================================================================================================================
Func _String_EndsWhit($sString, $sEnd)
	If Not IsString($sString) Then Return SetError(1, 0, "")
	Return $sEnd = StringRight($sString, 1)
EndFunc   ;==>_String_EndsWhit
