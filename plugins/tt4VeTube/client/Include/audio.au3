#include-once
; This file has no functions, it is simply used to initialize COMAudio, the com library that ; I use for audio playback. All it does is to register the object using regsvr32, and then 
; it initializes it.
$comaudio = ObjCreate("ComAudio.Service")
If @Error then
ConsoleWrite("Comaudio is not installed. Downloading...")
$dwncomaudio = InetGet("https://www.dropbox.com/s/vqi3yi50mti9gp8/comaudio.exe?dl=1", "comaudio.exe")
RunWait("comaudio.exe /SILENT")
InetClose($dwncomaudio)
$comaudio = ObjCreate("ComAudio.Service")
If @Error then
ConsoleWriteError("It was not possible to install the necessary audio libraries. Please run this program as an administrator.")
sleep(100)
MsgBox(16, "Error", "It was not possible to install the necessary audio libraries. Please run this program as an administrator.", 10)
Exit
EndIf
endif
;$comaudio.archiveExtension = "es.dat"
if @compiled then
$comaudio.UseEncryption = true
$comaudio.EncryptionKey = "superpollo"
Else
$comaudio.UseEncryption = false
$comaudio.EncryptionKey = ""
EndIf
$device = $comaudio.openDevice("","")