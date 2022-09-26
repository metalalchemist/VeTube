#include-once
; This file has some functions for key processing. It stores the state of each key in an ; array, so that it is possible to check the last state of the key and prevent the user from ; holding them down.

Dim $keys[200]
$dll = DLLOpen("user32.dll")
Func key_pressed($hexKey)
Local $aR, $bO
$hexKey = '0x' & $hexKey
$aR = DllCall($dll, "int", "GetAsyncKeyState", "int", $hexKey)
If Not @error And BitAND($aR[0], 0x8000) = 0x8000 Then
$bO = 1
Else
$bO = 0
EndIf
Return $bO
EndFunc
Func check_key($hextemp,$entry)
$hex = "" & $hextemp & ""
$tempkey = key_pressed("" & $hex & "")
If $tempkey = -1 Then return -1
If $tempkey = 1 Then
$intstatus = $keys[$entry]
$status = "" & $intstatus & ""
If $status = "1" Then
Return 0
EndIf
If $status = "2" Then
Return 0
EndIf
If $status = "0" Then
$keys[$entry] = 1
Return 1
EndIf
Else
$keys[$entry] = 0
Return 0
EndIf
EndFunc
Func check_keys()
$capt = check_key("25",0)
If $capt = -1 Then return 0
If $capt = 1 Then
$key="left arrow"
EndIf
$capt = check_key("27",1)
If $capt = 1 Then
$key="right arrow"
EndIf
$capt = check_key("26",2)
If $capt = 1 Then
$key="up arrow"
EndIf
$capt = check_key("28",3)
If $capt = 1 Then
$key="down arrow"
EndIf
$capt = check_key("20",4)
If $capt = 1 Then
$key="spacebar"
EndIf
$capt = check_key("0D",5)
If $capt = 1 Then
$key="enter"
EndIf
$capt = check_key("1B",6)
If $capt = 1 Then
$key="escape"
EndIf
EndFunc
