;Fakeyou UDF. UDF to support Fakeyou.com api.
;Original idea by Mateo Cedillo, and that written the first UDF version trying adapt a code from Python, but the result It was not nice.
;Modified and rewritten by @Danifirex, that adapted and added the functions in a more appropriate way. Thanks!.
#include <Array.au3>
#include "Json.au3"

Global $Au3FakeyouVer = "0.4.1"
Global Const $HTTP_STATUS_OK = 200

; #FUNCTION# ====================================================================================================================
; Name ..........: _FakeYouWaitForAudioComplete
; Description ...: It waits until the audio has been generated, that is, until the request has been completed, before being able to access the final audio file result.
; Syntax ........: _FakeYouWaitForAudioComplete($sInferenceJobToken)
; Parameters ....: $sInferenceJobToken  - The job token to be processed with.
; Return values .: returns true if the job completed, or returns @error to 1, if the operation failed. 2, if multiple attempts have been made but the process has timed out.
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: Yes
; ===============================================================================================================================
Func _FakeYouWaitForAudioComplete($sInferenceJobToken)
	While 1
		Switch _FakeYouGetQueueStatus($sInferenceJobToken)
			Case "attempt_failed"
				; Keep waiting
			Case "complete_failure"
				SetError(1, 0, "")
				ExitLoop
			Case "complete_success"
				return true
				ExitLoop
			Case "dead"
				SetError(2, 0, "")
		EndSwitch
		Sleep(1000)
	WEnd
EndFunc   ;==>_FakeYouWaitForAudioComplete

; #FUNCTION# ====================================================================================================================
; Name ..........: _FakeYouGetAudioStatus
; Description ...: Obtains the JSON code where all the audio status information of the current job can be obtained.
; Syntax ........: _FakeYouGetAudioStatus($sInferenceJobToken)
; Parameters ....: $sInferenceJobToken  - the job token.
; Return values .: The JSON code
; Author ........: Danifirex, Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: No
; ===============================================================================================================================
Func _FakeYouGetAudioStatus($sInferenceJobToken)
	Return __HttpGet("https://api.fakeyou.com/tts/job/" & $sInferenceJobToken)
EndFunc   ;==>_FakeYouGetAudioStatus
Func _FakeYou_getDirectAudio($sText, $sModelToken)
Local $sJobToken = _FakeYouGenerateAudio($sText, $sModelToken)
$bStatus = _FakeYouWaitForAudioComplete($sJobToken)
	if @error then
		Switch @error
			case 1
				MsgBox(16, "Error", "This job has failed")
			case 2
				MsgBox(16, "Error", "We have retried to process this job, but it has timed out. Please try again later.")
		EndSwitch
	EndIf
	if $bStatus then
		Local $sFinalURL = _FakeYouGetAudioURL($sJobToken)
		return $sFinalURL
	Else
		MsgBox(16, "Error", "An error occurred in this job.")
	EndIf
EndFunc
; #FUNCTION# ====================================================================================================================
; Name ..........: _FakeYouGetQueueStatus
; Description ...: Gets the current status of the requested audio, ie: pending, started, complete, etc.
; Syntax ........: _FakeYouGetQueueStatus($sInferenceJobToken)
; Parameters ....: $sInferenceJobToken  - The job token.
; Return values .: The queue status.
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: No
; ===============================================================================================================================
Func _FakeYouGetQueueStatus($sInferenceJobToken)
	$sData = _FakeYouGetAudioStatus($sInferenceJobToken)
	$oDecodeJson = Json_decode($sData)
	Return json_get($oDecodeJson, '["state"]["status"]')
EndFunc   ;==>_FakeYouGetQueueStatus

; #FUNCTION# ====================================================================================================================
; Name ..........: _FakeYouGenerateAudio
; Description ...: Generate an audio with the inference text and the token of the desired voice model
; Syntax ........: _FakeYouGenerateAudio($sText, $sTTSModelToken[, $sUUID = Default])
; Parameters ....: $sText               - The text to be generated.
;                  $sTTSModelToken      - The voice model token (TTS).
;                  $sUUID               - [optional] If you want to set a specific UUID. Default is Default, This will generate a random UUID.
; Return values .: None
; Author ........: Danifirex, Mateo Cedillo
; Modified ......:
; Remarks .......: To know the tokens of the models, you can do it from: _FakeYouGetVoicesList()
; Related .......:
; Link ..........:
; Example .......: Yes
; ===============================================================================================================================
Func _FakeYouGenerateAudio($sText, $sTTSModelToken, $sUUID = Default)
	If $sUUID = Default Then $sUUID = __GenerateUUID()
	ConsoleWrite("UUID: " &$sUUID & @CRLF)
	Local $oJson = Null
	Json_Put($oJson, ".tts_model_token", $sTTSModelToken)
	Json_Put($oJson, ".uuid_idempotency_token", $sUUID)
	Json_Put($oJson, ".inference_text", $sText)
	Local $sJson = Json_Encode($oJson)
	ConsoleWrite($sJson & @CRLF)
	Local $sJsonReturn = __HttpPost("https://api.fakeyou.com/tts/inference", $sJson)
	ConsoleWrite($sJsonReturn & @CRLF)
	$oJson = Json_Decode($sJsonReturn)
	If $sJsonReturn = "" Or Not __FakeYou_IsSuccess($oJson) Then Return SetError(1, 0, "")
	Return Json_Get($oJson, '["inference_job_token"]')
EndFunc   ;==>_FakeYouGenerateAudio

; #FUNCTION# ====================================================================================================================
; Name ..........: _FakeYouGetAudioURL
; Description ...: Gets the final URL of the requested audio. To avoid problems, it is important that when you generate an audio, you first call to _FakeYouWaitForAudioComplete function to wait until the request completes, and after then call this function, because if you do this you will be able to get the URL without problems. Otherwise, you will get a result like "null" or something.
; Syntax ........: _FakeYouGetAudioURL($sToken)
; Parameters ....: $sToken              - The job token.
; Return values .: The final URL
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: Yes
; ===============================================================================================================================
Func _FakeYouGetAudioURL($sToken)
	$sStatus = _FakeYouGetAudioStatus($sToken)
	$oDecodeJson = Json_Decode($sStatus)
	$sAudioPath = Json_get($oDecodeJson, '["state"]["maybe_public_bucket_wav_audio_path"]')
	If Not StringLeft($sAudioPath, 21) = "/tts_inference_output" Then
		Return SetError(1, 0, "")
	Else
		Return "https://storage.googleapis.com/vocodes-public" & $sAudioPath
	EndIf
EndFunc   ;==>_FakeYouGetAudioURL

; #FUNCTION# ====================================================================================================================
; Name ..........: _FakeYouGetVoicesCategoriesList
; Description ...: Get the available categories.
; Syntax ........: _FakeYouGetVoicesCategoriesList()
; Parameters ....: None
; Return values .: An array with the list of categories.
; Author ........: Danifirex, Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: No
; ===============================================================================================================================
Func _FakeYouGetVoicesCategoriesList()
	Local $sJson = __HttpGet("https://api.fakeyou.com/category/list/tts")
	ConsoleWrite($sJson & @CRLF)
	Local $oJson = Json_Decode($sJson)
	If $sJson = "" Or Not __FakeYou_IsSuccess($oJson) Then Return SetError(1, 0, "")
	Local $aoJson = Json_Get($oJson, '["categories"]')
	If Not IsArray($aoJson) Then Return SetError(2, 0, "")
	Local $aVoicesCategories[UBound($aoJson)][12]
	Local $aMembers[] = ["category_token", "model_type", "maybe_super_category_token", "can_directly_have_models", "can_have_subcategories", _
			"can_only_mods_apply", "name", "name_for_dropdown", "is_mod_approved", "created_at", _
			"updated_at", "deleted_at"]
	For $i = 0 To UBound($aoJson) - 1
		For $x = 0 To UBound($aMembers) - 1
			$aVoicesCategories[$i][$x] = Json_Get($aoJson[$i], '["' & $aMembers[$x] & '"]')
		Next
	Next
	Return $aVoicesCategories
EndFunc   ;==>_FakeYouGetVoicesCategoriesList

; #FUNCTION# ====================================================================================================================
; Name ..........: _FakeYouGetVoicesList
; Description ...: Get the list of voices.
; Syntax ........: _FakeYouGetVoicesList()
; Parameters ....: None
; Return values .: A 2d array with the info. of the available voices.
; Author ........: Danifirex, Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: No
; ===============================================================================================================================
Func _FakeYouGetVoicesList()
	Local $sJson = __HttpGet("https://api.fakeyou.com/tts/list")
	;ConsoleWrite($sJson & @CRLF)
	Local $oJson = Json_Decode($sJson)
	If $sJson = "" Or Not __FakeYou_IsSuccess($oJson) Then Return SetError(1, 0, "")
	Local $aoJson = Json_Get($oJson, '["models"]')
	If Not IsArray($aoJson) Then Return SetError(2, 0, "")
	Local $aVoices[UBound($aoJson)][15]
	Local $aMembers[] = ["model_token", "tts_model_type", "creator_user_token", "creator_username", "creator_display_name", _
			"creator_gravatar_hash", "title", "ietf_language_tag", "ietf_primary_language_subtag", "is_front_page_featured", _
			"is_twitch_featured", "maybe_suggested_unique_bot_command", "category_tokens", "created_at", "updated_at"]
	Local $sMemberValue = ""
	For $i = 0 To UBound($aoJson) - 1
		For $x = 0 To UBound($aMembers) - 1
			$sMemberValue = Json_Get($aoJson[$i], '["' & $aMembers[$x] & '"]')
			If $aMembers[$x] = "category_tokens" Then
				For $n = 0 To UBound($sMemberValue) - 1
					$aVoices[$i][$x] &= Json_Get($sMemberValue, '[' & $n & ']') & (($n < UBound($sMemberValue) - 1) ? "|" : "")
				Next
			Else
				$aVoices[$i][$x] = $sMemberValue
			EndIf
		Next
	Next
	Return $aVoices
EndFunc   ;==>_FakeYouGetVoicesList

; #INTERNAL_USE_ONLY# ===========================================================================================================
; Name ..........: __FakeYou_IsSuccess
; Description ...: (internal) Checks if the call completed successfully.
; Syntax ........: __FakeYou_IsSuccess(Byref $oJson)
; Parameters ....: $oJson               - [JSON] object.
; Return values .: None
; Author ........: Danifirex, Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: No
; ===============================================================================================================================
Func __FakeYou_IsSuccess(ByRef $oJson)
	Return Json_ObjExists($oJson, 'success')
EndFunc   ;==>__FakeYou_IsSuccess

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
