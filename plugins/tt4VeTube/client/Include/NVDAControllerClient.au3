#include-once
#cs
Hello.
this include file is  contains some functions to control the NVDA screen reader
by using the nvdaControllerClient Library
These include file  was designed by nacer baaziz
You can contact me in the following accounts.
For any question or inquiry
my Facebook account
https://www.facebook.com/baaziznacer1
my skype name is :
simple-blind
my gmail is :
baaziznacer.140@gmail.com
#ce
#### global variables ###
Global $_h_NVDAHandle = -1
### end ###


#cs
Available functions
_nvdaControllerClient_Load()
_nvdaControllerClient_free()
_nvdaControllerClient_SpeakText()
_nvdaControllerClient_brailleMessage()
_nvdaControllerClient_cancelSpeech()
_nvdaControllerClient_testIfRunning()
#ce



#### functions ####
; #FUNCTION# ====================================================================================================================
; Name...........: _nvdaControllerClient_Load
; Description ...: Starts up nvdaControllerClient functions
; Syntax.........: _nvdaControllerClient_Load($s_FileName = @scriptDir & "\nvdaControllerClient32.dll")
; Parameters ....:  -	$s_FileName	-	The relative path to nvdaControllerClient32.dll.
; Return values .: Success      - Returns the dllOpen handle or 1 if the dll is opened before
;                  Failure      - Returns False and sets @ERROR
;									@error will be set to-
;										- -1 	-	File could not be found.
;										- 1 	-	dll File could not be load.
; Author ........: nacer baaziz
; Modified.......
; Remarks .......:
; Related .......:
; Link ..........;
; Example .......;
; ===============================================================================================================================
Func _nvdaControllerClient_Load($s_FileName = @ScriptDir & "\nvdaControllerClient32.dll")
	If $_h_NVDAHandle <> -1 Then Return 1
	If FileExists($s_FileName) Then
		$_h_NVDAHandle = DllOpen($s_FileName)
		If $_h_NVDAHandle = -1 Then Return SetError(1)
		Return $_h_NVDAHandle
	Else
		SetError(-1)
		Return False
	EndIf
EndFunc   ;==>_nvdaControllerClient_Load


; #FUNCTION# ====================================================================================================================
; Name...........: _nvdaControllerClient_Free
; Description ...: UnLoad the nvdaControllerClient dll
; Syntax.........: _nvdaControllerClient_free($DllHandle = $_h_NVDAHandle)
; Parameters ....:  -	$DllHandle	-	 the dllOpen handel returned by _nvdaControllerClient_Load.
; Return values .: Success      - Returns -1 if the dll is Closed.
;                  Failure      - Returns False and sets @ERROR
;									@error will be set to-
;										- 0 	-	0 if the _nvdaControllerClient_Load is not used.
; Author ........: nacer baaziz
; Modified.......
; Remarks .......:
; Related .......:
; Link ..........;
; Example .......;
; ===============================================================================================================================
Func _nvdaControllerClient_free($DllHandle = $_h_NVDAHandle)
	If $DllHandle <> -1 Then
		SetError(0)
		Return False
	EndIf
	DllClose($DllHandle)
	$_h_NVDAHandle = -1
	Return $_h_NVDAHandle
EndFunc   ;==>_nvdaControllerClient_free


; #FUNCTION# ====================================================================================================================
; Name...........: _nvdaControllerClient_SpeakText
; Description ...: speak a custom text using the NVDA screen Reader
; Syntax.........: _nvdaControllerClient_SpeakText($s_text, $DllHandle = $_h_NVDAHandle)
; Parameters ....:  -		$s_text the text-
; -	$DllHandle	-	 the dllOpen handel returned by _nvdaControllerClient_Load.
; Return values .: Success      - Returns 1 .
;                  Failure      - Returns False and sets @ERROR
;									@error will be set to-
;										-  	-	0 if the _nvdaControllerClient_Load is not used.
;										-  	-	dllCall result if there is any problem when try to call the dll file.
; Author ........: nacer baaziz
; Modified.......
; Remarks .......:
; Related .......:
; Link ..........;
; Example .......;
; ===============================================================================================================================

Func _nvdaControllerClient_SpeakText($s_text, $DllHandle = $_h_NVDAHandle)
	If $DllHandle = -1 Then
		SetError(0)
		Return False
	EndIf
	Local $aDLLSpeak = DllCall($DllHandle, "long", "nvdaController_speakText", "wstr", String($s_text))
	If @error Then Return $aDLLSpeak
	Return 1
EndFunc   ;==>_nvdaControllerClient_SpeakText


; #FUNCTION# ====================================================================================================================
; Name...........: _nvdaControllerClient_brailleMessage
; Description ...: View any custom text in the Braille line
; Syntax.........: _nvdaControllerClient_brailleMessage($s_text, $DllHandle = $_h_NVDAHandle)
; Parameters ....:  -		$s_text the text-
; -	$DllHandle	-	 the dllOpen handel returned by _nvdaControllerClient_Load.
; Return values .: Success      - Returns 1 .
;                  Failure      - Returns False and sets @ERROR
;									@error will be set to-
;										-  	-	0 if the _nvdaControllerClient_Load is not used.
;										-  	-	dllCall result if there is any problem when try to call the dll file.
; Author ........: nacer baaziz
; Modified.......
; Remarks .......:
; Related .......:
; Link ..........;
; Example .......;
; ===============================================================================================================================

Func _nvdaControllerClient_brailleMessage($s_text, $DllHandle = $_h_NVDAHandle)
	If $DllHandle = -1 Then
		SetError(0)
		Return False
	EndIf
	Local $aDLLMSg = DllCall($DllHandle, "long", "nvdaController_brailleMessage", "wstr", String($s_text))
	If @error Then Return $aDLLMSg
	Return 1
EndFunc   ;==>_nvdaControllerClient_brailleMessage

; #FUNCTION# ====================================================================================================================
; Name...........: _nvdaControllerClient_cancelSpeech
; Description ...: Stop NVDA from talking
; Syntax.........: _nvdaControllerClient_cancelSpeech($DllHandle = $_h_NVDAHandle)
; Parameters ....:  -	$DllHandle	-	 the dllOpen handel returned by _nvdaControllerClient_Load.
; Return values .: Success      - Returns 1 .
;                  Failure      - Returns False and sets @ERROR
;									@error will be set to-
;										-  	-	0 if the _nvdaControllerClient_Load is not used.
;										-  	-	dllCall result if there is any problem when try to call the dll file.
; Author ........: nacer baaziz
; Modified.......
; Remarks .......:
; Related .......:
; Link ..........;
; Example .......;
; ===============================================================================================================================

Func _nvdaControllerClient_cancelSpeech($DllHandle = $_h_NVDAHandle)
	If $DllHandle = -1 Then
		SetError(0)
		Return False
	EndIf
	Local $aDLLCancel = DllCall($DllHandle, "long", "nvdaController_cancelSpeech") ;, "wstr", "")
	If @error Then Return $aDLLCancel
	Return 1
EndFunc   ;==>_nvdaControllerClient_cancelSpeech

; #FUNCTION# ====================================================================================================================
; Name...........: _nvdaControllerClient_testIfRunning
; Description ...: test if the NVDA is running
; Syntax.........: _nvdaControllerClient_testIfRunning($DllHandle = $_h_NVDAHandle)
; Parameters ....:  -	$DllHandle	-	 the dllOpen handel returned by _nvdaControllerClient_Load.
; Return values .: Success      - Returns true if the NVDA is Running, else return false.
;                  Failure      - Returns False and sets @ERROR
;									@error will be set to-
;										-  	-	0 if the _nvdaControllerClient_Load is not used.
;										-  	-	-1 if there is any problem when try to call the dll file.
; Author ........: nacer baaziz
; Modified.......
; Remarks .......:
; Related .......:
; Link ..........;
; Example .......;
; ===============================================================================================================================


Func _nvdaControllerClient_testIfRunning($DllHandle = $_h_NVDAHandle)
	If $DllHandle = -1 Then
		SetError(0)
		Return False
	EndIf
	Local $aDLLIsRun = DllCall($DllHandle, "long", "nvdaController_testIfRunning")
	If Not (IsArray($aDLLIsRun)) Then Return SetError(-1)
	If $aDLLIsRun[0] <> 0 Then Return False
	Return True
EndFunc   ;==>_nvdaControllerClient_testIfRunning
### end ####
