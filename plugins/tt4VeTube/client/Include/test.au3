; test analizando base de datos de voces
#include <FileConstants.au3>
#include "Json.au3"
#include "net.au3"
; obsoleto:
;$sJson = __HttpGet("http://127.0.0.1:5000/voices")
;ConsoleWrite($sJson & @CRLF)
; obteniendo json:
$sVoiceJson = _GetConfig()
$oJson = Json_decode($sVoiceJson)
; nombre de voz:
$aKeys = Json_ObjGetKeys($oJson)
MsgBox(0, "", $aKeys[0])
; id de voz:
$aItems = Json_ObjGetItems($oJson)
MsgBox(0, "", $aItems[0])
; esto sería lo correcto para aplicar en el proyecto:
;$sVoice = json_get($oJson, '["' &$aKeys[0] &'"]')
;msgbox(0, "", $sVoice)
; cuántas voces hay:
$iCount = Json_ObjGetCount($oJson)
msgbox(0, "", $iCount)
Func _GetConfig()
$hFile = FileOpen(@scriptDir &"\voices.json", $fo_read)
If $hFile = -1 then Return SetError(1, 0, "")
$sConfig = FileRead($hFile)
FileClose($hFile)
return $sConfig
EndFunc
