#include <WinAPICom.au3>
#include-once
Global Const $HTTP_STATUS_OK = 200
; #INTERNAL_USE_ONLY# ===========================================================================================================
; Name ..........: __HttpGet
; Description ...:
; Syntax ........: __HttpGet($sURL[, $sData = ""])
; Parameters ....: $sURL                - a string value.
;                  $sData               - [optional] a string value. Default is "".
; Return values .: None
; Author ........:
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: No
; ===============================================================================================================================
Func __HttpGet($sURL, $sData = "")
	Local $oErrorHandler = ObjEvent("AutoIt.Error", "_ErrFunc")
	Local $oHTTP = ObjCreate("WinHttp.WinHttpRequest.5.1")
	$oHTTP.Open("GET", $sURL & "?" & $sData, False)
	If (@error) Then Return SetError(1, 0, 0)
	$oHTTP.SetRequestHeader("Content-Type", "application/json")
	$oHTTP.Send()
	If (@error) Then Return SetError(2, 0, 0)
	If ($oHTTP.Status <> $HTTP_STATUS_OK) Then Return SetError(3, 0, 0)
	Return SetError(0, 0, $oHTTP.ResponseText)
EndFunc   ;==>__HttpGet

; #INTERNAL_USE_ONLY# ===========================================================================================================
; Name ..........: __HttpPost
; Description ...:
; Syntax ........: __HttpPost($sURL[, $sData = ""])
; Parameters ....: $sURL                - a string value.
;                  $sData               - [optional] a string value. Default is "".
; Return values .: None
; Author ........:
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: No
; ===============================================================================================================================
Func __HttpPost($sURL, $sData = "")
	Local $oErrorHandler = ObjEvent("AutoIt.Error", "_ErrFunc")
	Local $oHTTP = ObjCreate("WinHttp.WinHttpRequest.5.1")
	$oHTTP.Open("POST", $sURL, False)
	If (@error) Then Return SetError(1, 0, 0)
	$oHTTP.SetRequestHeader("Content-Type", "application/json")
	$oHTTP.Send($sData)
	If (@error) Then Return SetError(2, 0, 0)
	If ($oHTTP.Status <> $HTTP_STATUS_OK) Then Return SetError(3, 0, 0)
	Return SetError(0, 0, $oHTTP.ResponseText)
EndFunc   ;==>__HttpPost

; User's COM error function. Will be called if COM error occurs
; #FUNCTION# ====================================================================================================================
; Name ..........: _ErrFunc
; Description ...:
; Syntax ........: _ErrFunc($oError)
; Parameters ....: $oError              - an object.
; Return values .: None
; Author ........:
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: No
; ===============================================================================================================================
Func _ErrFunc($oError)
	; Do anything here.
	ConsoleWrite(@ScriptName & " (" & $oError.scriptline & ") : ==> COM Error intercepted !" & @CRLF & _
			@TAB & "err.number is: " & @TAB & @TAB & "0x" & Hex($oError.number) & @CRLF & _
			@TAB & "err.windescription:" & @TAB & $oError.windescription & @CRLF & _
			@TAB & "err.description is: " & @TAB & $oError.description & @CRLF & _
			@TAB & "err.source is: " & @TAB & @TAB & $oError.source & @CRLF & _
			@TAB & "err.helpfile is: " & @TAB & $oError.helpfile & @CRLF & _
			@TAB & "err.helpcontext is: " & @TAB & $oError.helpcontext & @CRLF & _
			@TAB & "err.lastdllerror is: " & @TAB & $oError.lastdllerror & @CRLF & _
			@TAB & "err.scriptline is: " & @TAB & $oError.scriptline & @CRLF & _
			@TAB & "err.retcode is: " & @TAB & "0x" & Hex($oError.retcode) & @CRLF & @CRLF)
EndFunc   ;==>_ErrFunc
; #INTERNAL_USE_ONLY# ===========================================================================================================
; Name ..........: __GenerateUUID
; Description ...: Generates a random UUID.
; Syntax ........: __GenerateUUID()
; Parameters ....: None
; Return values .: None
; Author ........: Danifirex, Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: No
; ===============================================================================================================================
Func __GenerateUUID()
	Return StringLower(StringReplace(StringReplace(_WinAPI_CreateGUID(), "{", ""), "}", ""))
EndFunc   ;==>__GenerateUUID
