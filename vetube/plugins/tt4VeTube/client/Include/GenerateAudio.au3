#include "net.au3"
Func _GenerateAudio($sModelName, $sText)
	local $sResponse = __HttpGet("http://localhost:5000/?name=" &$sModelName &"&text=" &$sText)
	if @error then Return SetError(1, 0, "")
	return $sResponse
EndFunc