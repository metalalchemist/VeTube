#include <FileConstants.au3>
Func _GetFileData($sFile)
if not FileExists($sFile) then Return SetError(1, 0, "")
$hFile = FileOpen($sFile, $fo_read)
If $hFile = -1 then Return SetError(3, 0, "")
$sData = FileRead($hFile)
FileClose($hFile)
return $sData
EndFunc