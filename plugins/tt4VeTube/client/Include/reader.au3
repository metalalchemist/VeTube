#include-once
#include <File.au3>
#include "jfw.au3"
#include "kbc.au3"
#include "log.au3"
#include "menu_nvda.au3"
#include "NVDAControllerClient.au3"
#include "sapi.au3"
#include <StringConstants.au3>
#include "translator.au3"
Global $rd_Ver = "1.5.2"
global $lng = "en", $sSpeechHistory = "", $movement = 1, $historyEnhabled = True
;This is a script for interacting whit screen readers.
;this is a more extended version of the original reader.
;Author: Mateo Cedillo.
; #FUNCTION# ====================================================================================================================
; Name ..........: speaking
; Description ...: Speak any text, detecting screen reader first
; Syntax ........: speaking($sText [, $bInterrupt = false, , $bEnableHistory = False])
; Parameters ....: $sText                - the string or text to be spoken.
;                  $bInterrupt           - [optional] Configure if you want to enable other text speech interruption to speak this one, which means that any previously read text will be interrupted by this new one, if set to true; Otherwise, it waits until the previous text input is finished speaking and then speaks the new text. Default is false (Don't interrupt).
;                  $bEnableHistory           - [optional] Enhable's speech history support and adds that item to the list of history entries that can later be navigated with the keys. Default is false (disabled).
; Return values .: None
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: Yes
; ===============================================================================================================================
Func speaking($sText, $bInterrupt = False, $bEnableHistory = False)
	If IniRead(@ScriptDir & "\config\config.st", "accessibility", "Speak Whit", "") = "" Then
		$speak = autodetect()
	Else
		$inicheck = IniRead(@ScriptDir & "\config\config.st", "accessibility", "Speak Whit", "")
		Select
			Case $inicheck = "NVDA" Or $inicheck = "JAWS" Or $inicheck = "Sapi"
				$speak = $inicheck
			Case Else
				MsgBox(16, "ReaderEx", translate($lng, "Your text-to-speech settings are invalid. Autodetecting..."))
				$speak = autodetect()
		EndSelect
	EndIf
	Select
		Case $speak = "NVDA"
			If @AutoItX64 = 1 Then
				_nvdaControllerClient_Load(@ScriptDir & "\nvdaControllerClient64.dll")
			Else
				_nvdaControllerClient_Load()
			EndIf
			If @error Then
				MsgBox(16, translate($lng, "error"), translate($lng, "Cant load the NVDA DLL file"))
			Else
				If $bInterrupt Then _NVDAControllerClient_CancelSpeech()
				_NVDAControllerClient_SpeakText($sText)
				_NVDAControllerClient_BrailleMessage($sText)
			EndIf
		Case $speak = "Sapi"
			If not $bInterrupt Then
				speak($sText)
			Else
				speak($sText, 3)
			EndIf
		Case $speak = "JAWS"
			JFWSpeak($sText)
		Case Else
			MsgBox(16, translate($lng, "Error"), translate($lng, "Unable to determine text-to-speech output"))
			autodetect()
	EndSelect
	If $bEnableHistory And $historyEnhabled Then
		writeinlog("ReaderEx: Speech history activated")
		$sSpeechHistory &= $sText & @CRLF
		HotKeySet("{home}", "SpeechHistory")
		HotKeySet("{pgdn}", "SpeechHistory")
		HotKeySet("{PGUP}", "SpeechHistory")
		HotKeySet("{end}", "SpeechHistory")
		HotKeySet("{del}", "SpeechHistory")
		HotKeySet("{bs}", "SpeechHistory")
		HotKeySet("{c}", "SpeechHistory")
		speaking(translate($lng, "Speech history screen activated. Use home, end, back and page forward to navigate through messages. Press delete key to clear history entries, or back space to disable history forever. If an element is added, it will appear in the list."))
	Else
	EndIf
EndFunc   ;==>speaking
;internal:
; #FUNCTION# ====================================================================================================================
; Name ..........: disableHotkeys
; Description ...: [internal] Disable speech history and interaction keys with it.
; Syntax ........: disableHotkeys()
; Parameters ....: None
; Return values .: None
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: No
; ===============================================================================================================================
Func disableHotkeys()
	writeinlog("disabling hotkeys")
	$historyEnhabled = False
	HotKeySet("{home}")
	HotKeySet("{pgdn}")
	HotKeySet("{PGUP}")
	HotKeySet("{end}")
	HotKeySet("{del}")
	HotKeySet("{c}")
EndFunc   ;==>disableHotkeys
; #FUNCTION# ====================================================================================================================
; Name ..........: SpeechHistory
; Description ...: speech history support
; Syntax ........: SpeechHistory()
; Parameters ....: None
; Return values .: None
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: No
; ===============================================================================================================================
Func SpeechHistory()
	$aNavigator = StringSplit(StringTrimRight($sSpeechHistory, 1), @LF)
	Sleep(10)
	writeinlog(@HotKeyPressed)
	Switch @HotKeyPressed
		Case "{HOME}"
			If IsArray($aNavigator) Then
				$movement = 1
				speaking(translate($lng, "Home"))
				speaking($aNavigator[$movement])
				Beep(1100, 50)
			Else
				speaking(translate($lng, "No history"))
			EndIf
		Case "{PGUP}"
			If IsArray($aNavigator) Then
				$movement = $movement - 1
				If $movement <= 1 Then
					$movement = 1
					speaking(translate($lng, "Home"))
					Beep(1100, 50)
				EndIf
				speaking($aNavigator[$movement])
			Else
				speaking(translate($lng, "no history"))
			EndIf
		Case "{PGDN}"
			If IsArray($aNavigator) Then
				$movement = $movement + 1
				If $movement >= $aNavigator[0] Then
					$movement = $aNavigator[0]
					speaking(translate($lng, "End"))
					Beep(2200, 50)
				EndIf
				speaking($aNavigator[$movement])
			Else
				speaking(translate($lng, "no history"))
			EndIf
		Case "{END}"
			If IsArray($aNavigator) Then
				$movement = $aNavigator[0]
				speaking(translate($lng, "End"))
				speaking($aNavigator[$movement])
				Beep(2200, 50)
			Else
				speaking(translate($lng, "no history"))
			EndIf
		Case "{c}"
			If IsArray($aNavigator) Then
				clipPut($aNavigator[$movement])
				speaking(translate($lng, "copied to clipboard") &": " &$aNavigator[$movement])
			Else
				speaking(translate($lng, "no history"))
			EndIf
		Case "{DEL}"
			$aNavigator = ""
			$sSpeechHistory = ""
			speaking(translate($lng, "Speech history cleared"))
		case "{bs}"
			disableHotkeys()
			speaking(translate($lng, "History off"))
	EndSwitch
EndFunc   ;==>SpeechHistory
; #FUNCTION# ====================================================================================================================
; Name ..........: autodetect
; Description ...: autodetects which screen reader is being used
; Syntax ........: autodetect()
; Parameters ....: None
; Return values .: None
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: No
; ===============================================================================================================================
Func autodetect()
	If ProcessExists("NVDA.exe") Then
		Return "NVDA"
	EndIf
	If ProcessExists("JFW.exe") Then
		Return "JAWS"
	EndIf
	If Not ProcessExists("NVDA.exe") Or ProcessExists("JFW.exe") Then
		Return "sapi"
	EndIf
EndFunc   ;==>autodetect
; #FUNCTION# ====================================================================================================================
; Name ..........: CreateTTsDialog
; Description ...: simulate a dialog with tts
; Syntax ........: CreateTTsDialog($sDialogName, $sText [, $sTtsString = " press enter to continue, space to repeat information."])
; Parameters ....: $sDialogName                - string containing the title of the dialog
;                  $sText                - the string containing the text for the dialog. If it is a multiline text, don't worry, it displays it correctly as if it were a document.
;                  $sTtsString           - [optional] A dll struct value. Default is " press enter to continue.
;                  space to repeat information."- An unknown value.
; Return values .: None
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: No
; ===============================================================================================================================
Func CreateTtsDialog($sDialogName, $sText, $sTtsString = translate($lng, "press enter to continue, space to repeat information."))
	disableHotkeys()
	;Identifies if the dialog has more than one line. If so, we will have the user scroll through the lines with the arrows.
	if StringInStr($sText, @lf) then
		$isMultiLine = true
		$sTtsString = translate($lng, "Use the arrows to read this dialog and enter to continue")
		$separateML = StringSplit($sText, @lf)
		$dmove = 1
		speaking($sDialogName & "  " &translate($lng, "Dialog") & @LF & $separateml[1] & @lf & $SttsString, true)
	Else
		$isMultiLine = false
		speaking($sDialogName & "  " &translate($lng, "Dialog") & @LF & $sText & @lf & $SttsString, true)
	EndIF
	While 1
		$active_window = WinGetProcess("")
		If $active_window = @AutoItPID Then
		Else
			Sleep(10)
			ContinueLoop
		EndIf
		If _IsPressed($spacebar) Or _IsPressed($left) Or _IsPressed($right) Then
			if $isMultiLine then
				speaking($separateml[$dmove])
			Else
				speaking($sText & @LF & $sTtsString)
			EndIF
			While _IsPressed($spacebar) Or _IsPressed($left) Or _IsPressed($right)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($down) then
			if $isMultiLine then
				$dmove = $dmove +1
				If $dmove >= $separateML[0] Then
					$dmove = $separateml[0]
					speaking(translate($lng, "Press enter to continue"))
				EndIF
				speaking($separateML[$dmove])
			Else
				speaking($sText & @LF & $sTtsString)			
			EndIF
			While _IsPressed($down)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($up) then
			if $isMultiLine then
				$dmove = $dmove -1
				If $dmove <= 1 Then $dmove = 1
				speaking($separateML[$dmove])
			Else
				speaking($sText & @LF & $sTtsString)			
			EndIF
			While _IsPressed($up)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($home) then
			if $isMultiLine then
				$dmove = 1
				speaking($separateML[$dmove])
			Else
				speaking($sText & @LF & $sTtsString)			
			EndIF
			While _IsPressed($home)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($end) then
			if $isMultiLine then
				$dmove = $separateml[0]
				speaking($separateML[$dmove])
			Else
				speaking($sText & @LF & $sTtsString)			
			EndIF
			While _IsPressed($end)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($caps) and _IsPressed($tab) or _IsPressed($insert) and _IsPressed($tab) then
			speaking($sDialogName &", " &translate($lng, "Dialog"))
			While _IsPressed($caps) and _IsPressed($tab) or _IsPressed($insert) and _IsPressed($tab)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($tab) then
			speaking($sDialogName)
			While _IsPressed($tab)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($control) And _IsPressed($c) Then
			if $isMultiLine then
				ClipPut($separateml[$dmove])
			Else
				ClipPut($sText)
			EndIf
			speaking(translate($lng, "Copied to clipboard") &". " & clipGet())
			While _IsPressed($control) And _IsPressed($c)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($enter) Then
			While _IsPressed($enter)
				Sleep(10)
			WEnd
			ExitLoop
		EndIf
		Sleep(10)
	WEnd
EndFunc   ;==>TTsDialog
; #FUNCTION# ====================================================================================================================
; Name ..........: createTtsDocument
; Description ...: Document reader, interactive document, document manager with tts, etc. If i had to give a fuller description of this itself i would say its a greath document reader but based on tts and keyboard shortcuts.
; Syntax ........: createTtsDocument($sFiletoread, $sTitle)
; Parameters ....: $sFiletoread          - the string containing the name of the file (a document).
;                  $sTitle               - The string containing the title of the document mode screen.
; Return values .: None
; Author ........: Mateo Cedillo
; Modified ......:
; Remarks .......:
; Related .......:
; Link ..........:
; Example .......: No
; ===============================================================================================================================
Func createTtsDocument($sFiletoread, $sTitle, $bSelectionMode = false)
	disableHotkeys()
	writeinlog("ReaderEx.au3: Loading document mode...")
	writeinlog("Using ReaderEx version: " & $rd_Ver)
	$move_doc = 0
	$textselector = 0
	Local $r_file = FileReadToArray($sFiletoread)
	Local $iCountLines = @extended
	$not = 0
	$pages = 0
	$docError = 0
	$sprate = 0
	$spvol = 100
	Local $textselected = ""
	If @error Then
		speaking(translate($lng, "Error reading file..."))
		writeinlog("Document mode: File to read: " & $sFiletoread & " error. Error reading file.")
		$docError = 1
	Else
		if not $bSelectionmode then
			$smResult = translate($lng, "Selection mode off")
		Else
			$smResult = translate($lng, "Selection mode on")
		EndIf
		speaking($sTitle & " " & translate($lng, "document.") & @CRLF & $smResult)
		writeinlog("Document mode: Dialog: " & $sTitle & @CRLF & "file to read: " & $sFiletoread &@crlf &"Document information: Lines: " & $iCountLines)
	EndIf
	HotKeySet("{f1}")
	For $foundPages = 0 To $iCountLines Step 30
		$pages = $pages + 1
	Next
	writeinlog("Document mode: Total number of pages: " & $pages)
	While 1
		If $docError = 1 Then ExitLoop
		$active_window = WinGetProcess("")
		If $active_window = @AutoItPID Then
		Else
			Sleep(10)
			ContinueLoop
		EndIf
		If _IsPressed($f1) Then
			writeinlog("Document mode: f1 pressed")
			speaking(translate($lng, "Interaction commands:") & @CRLF & translate($lng, "Use the up and down arrows to read the document.") & @CRLF & translate($lng, "Use the home and end keys to go to the beginning or end of the document.") & @CRLF & translate($lng, "Use page up and page down to go forward or backward ten lines.") & @CRLF & translate($lng, "Use control+d and control+u to go forward or backward one page.") & @CRLF & translate($lng, "Press the s and r keys to enhable automatic reading. A to read all content from start to end, r to read from cursor position to end.") &@crlf &translate($lng, "Use control+shift+s to open selection mode, which will allow you to select multiple text marks and perform editing commands and operations.") & @CRLF & translate($lng, "Press the I key to open the print options, which will allow you to print the entire document or specific content.") & @CRLF & translate($lng, "Use the editing commands to cut, copy, paste and select all the text.") & @CRLF & translate($lng, "Escape to exit document mode."))
			While _IsPressed($f1)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($f2) Then
			writeinlog("Document mode: f2 pressed")
			speaking(translate($lng, "Information commands:") & @CRLF & translate($lng, "Press the e key to spell the current line.") & @CRLF & translate($lng, "Use the l key to speak the line number you are on.") & @CRLF & translate($lng, "Use the T key to check the number of total and remaining lines of the document.") & @CRLF & translate($lng, "Press SHIFT+P to see the total number of pages in the document (useful for printing, for example).") & @CRLF & translate($lng, "Commands to check number of words:") & @CRLF & translate($lng, "1: Speaks the total number of words in the entire document.") & @CRLF & translate($lng, "2: Speaks the total number of words in the current line.") & @CRLF & translate($lng, "3: Speaks the total number of words filled in the selection."), True)
			While _IsPressed($f2)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($f3) Then
			writeinlog("Document mode: f3 pressed")
			speaking(translate($lng, "Voice commands:") & @CRLF & translate($lng, "Press CTRL+SHIFT+plus (+) key to increase the reading speed.") & @CRLF & translate($lng, "Press CTRL+SHIFT+minus or dash (-) key to decrease the reading speed.") &@crlf &translate($lng, "You can also press the plus (+) or minus (-) key to increase or decrease the reading volume."), True)
			While _IsPressed($f3)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($home) Then
			writeinlog("Home pressed")
			If $bSelectionmode Then
				If Not $textselected = "" Then
					speaking(translate($lng, "Unselected"), True)
					$textselected = ""
				EndIf
			EndIf
			$move_doc = "0"
			if $r_file[$move_doc] = "" then
				speaking(translate($lng, "Blank line"))
			Else
				speaking($r_file[$move_doc], True)
			EndIf
			writeinlog("Home pressed. Position " &$move_doc)
			While _IsPressed($home)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($page_down) Then
			writeinlog("PGDN pressed")
			If $bSelectionmode Then
				For $I = $move_doc To $move_doc + 9
					If $move_doc >= $iCountLines - 1 Then
						$move_doc = $iCountLines - 1
					Else
						$textselected &= $r_file[$I] & @CRLF
						$move_doc = $move_doc + 1
					EndIf
				Next
				speaking(translate($lng, "Ten lines have been selected"), True)
				speaking($r_file[$move_doc], True)
				writeinlog("Selected line: " & $move_doc)
			Else
				$move_doc = $move_doc + 10
				If $move_doc >= $iCountLines Then
					$move_doc = $iCountLines - 1
					speaking(translate($lng, "document end. Press escape to back."), True)
				EndIf
				if $r_file[$move_doc] = "" then
					speaking(translate($lng, "Blank line"))
				Else
					speaking($r_file[$move_doc], True)
				EndIF
				writeinlog("line: " & $move_doc)
			EndIf
			While _IsPressed($page_down)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($page_up) Then
			If $bSelectionmode Then
				$textselector = 10
				For $I = $move_doc To $move_doc - 9 Step -1
					If $move_doc <= 0 Then
						$move_doc = "0"
					Else
						$textselected &= $r_file[$I - $textselector] & @CRLF
						$textselector = $textselector - 2
						$move_doc = $move_doc - 1
					EndIf
				Next
				speaking(translate($lng, "Ten lines have been selected"))
				speaking($r_file[$move_doc], True)
				writeinlog("Selected line: " & $move_doc)
			Else
				$move_doc = $move_doc - 10
				If $move_doc <= 0 Then $move_doc = "0"
					if $r_file[$move_doc] = "" then
						speaking(translate($lng, "Blank line"))
					Else
						speaking($r_file[$move_doc], True)
				EndIf
				writeinlog("Line: " & $move_doc)
			EndIf
			While _IsPressed($page_up)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($control) And _IsPressed($d) Then
			writeinlog("Control+d pressed. Forwarding page")
			If $bSelectionmode Then
				writeinlog("Selection mode on. Selecting the page...")
				For $I = $move_doc To $move_doc + 29
					If $move_doc >= $iCountLines - 1 Then
						$move_doc = $iCountLines - 1
					Else
						$textselected &= $r_file[$I] & @CRLF
						$move_doc = $move_doc + 1
					EndIf
				Next
				speaking(translate($lng, "Page was selected"))
				speaking($r_file[$move_doc])
			Else
				$move_doc = $move_doc + 30
				If $move_doc >= $iCountLines Then
					$move_doc = $iCountLines - 1
					speaking(translate($lng, "document end. Press escape to back."), True)
				EndIf
				speaking($r_file[$move_doc], True)
				writeinlog("Line: " & $move_doc)
			EndIf
			While _IsPressed($control) And _IsPressed($d)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($control) And _IsPressed($u) Then
			writeinlog("Control+U pressed")
			If $bSelectionmode Then
				writeinlog("Selection mode on. Selecting page...")
				$textselector = 30
				For $I = $move_doc To $move_doc - 29 Step -1
					If $move_doc <= 0 Then
						$move_doc = "0"
					Else
						$textselected &= $r_file[$I - $textselector] & @CRLF
						$textselector = $textselector - 2
						$move_doc = $move_doc - 1
					EndIf
				Next
				speaking(translate($lng, "Page was selected"))
				speaking($r_file[$move_doc], True)
			Else
				$move_doc = $move_doc - 30
				If $move_doc <= 0 Then $move_doc = "0"
				speaking($r_file[$move_doc], True)
				writeinlog("Line: " & $move_doc)
			EndIf
			While _IsPressed($control) And _IsPressed($u)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($end) Then
			If $bSelectionmode Then
				If Not $textselected = "" Then
					speaking(translate($lng, "Unselected"), True)
					$textselected = ""
				EndIf
			EndIf
			$move_doc = $iCountLines - 1
			if $r_file[$move_doc] = "" then
				speaking(translate($lng, "Blank line"))
			Else
				speaking($r_file[$move_doc] & @CRLF & translate($lng, "document end. Press escape to back."), True)
			EndIf
			writeinlog("Line: " & $move_doc)
			While _IsPressed($end)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($up) Then
			$move_doc = $move_doc - 1
			If $move_doc <= 0 Then
				If $bSelectionmode Then speaking(translate($lng, "You have reached the home of the document, there is nothing else to select."), True)
				$move_doc = "0"
			EndIf
			If $bSelectionmode Then
				$textselected &= $r_file[$move_doc] & @CRLF
				speaking(translate($lng, "Was selected") & " " & $r_file[$move_doc], True)
			Else
				if $r_file[$move_doc] = "" then
					speaking(translate($lng, "Blank line"))
				Else
					speaking($r_file[$move_doc], True)
				EndIf
				writeinlog("Line: " & $move_doc)
			EndIf
			While _IsPressed($up)
				If $bSelectionmode Then Beep(4000, 50)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($down) Then
			$move_doc = $move_doc + 1
			If $move_doc >= $iCountLines Then
				If $bSelectionmode Then speaking(translate($lng, "You have reached the end of the document, there is nothing else to select."))
				speaking(translate($lng, "document end. Press escape to back."), True)
				$move_doc = $iCountLines - 1
			EndIf
			If $bSelectionmode Then
				$textselected &= $r_file[$move_doc] & @CRLF
				speaking(translate($lng, "Was selected") & " " & $r_file[$move_doc], True)
			Else
				if $r_file[$move_doc] = "" then
					speaking(translate($lng, "Blank line"))
				Else
					speaking($r_file[$move_doc], True)
				EndIf
				writeinlog("Line: " & $move_doc)
			EndIf
			While _IsPressed($down)
				If $bSelectionmode Then Beep(4000, 50)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($l) Then
			writeinlog("L pressed")
			speaking(translate($lng, "Line:") & " " & $move_doc + 1, True)
			While _IsPressed($l)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($e) Then
			writeinlog("E pressed")
			if not $r_file[$move_doc] = "" then
				$lenght = StringLen($r_file[$move_doc])
				$remove = -1
				$remover = $lenght
				For $spell = 1 To $lenght
					$remove = $remove + 1
					$remover = $remover - 1
					speaking(StringTrimLeft(StringTrimRight($r_file[$move_doc], $remover), $remove))
					If StringTrimLeft(StringTrimRight($r_file[$move_doc], $remover), $remove) = " " Then speaking(translate($lng, "Space"))
					If StringTrimLeft(StringTrimRight($r_file[$move_doc], $remover), $remove) = ":" Then speaking(translate($lng, "Colon"))
					If StringTrimLeft(StringTrimRight($r_file[$move_doc], $remover), $remove) = "," Then speaking(translate($lng, "Comma"))
					If StringTrimLeft(StringTrimRight($r_file[$move_doc], $remover), $remove) = "-" Then speaking(translate($lng, "Dash"))
					If StringTrimLeft(StringTrimRight($r_file[$move_doc], $remover), $remove) = "'" Then speaking(translate($lng, "Apostrofe"))
					If StringTrimLeft(StringTrimRight($r_file[$move_doc], $remover), $remove) = '"' Then speaking(translate($lng, "Quotes"))
					If StringTrimLeft(StringTrimRight($r_file[$move_doc], $remover), $remove) = "(" Then speaking(translate($lng, "Open parentheses"))
					If StringTrimLeft(StringTrimRight($r_file[$move_doc], $remover), $remove) = ")" Then speaking(translate($lng, "Close parentheses"))
				Next
			else
				speaking(translate($lng, "blank line"))
			EndIf
			While _IsPressed($e)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($t) Then
			writeinlog("T pressed")
			speaking(translate($lng, "total lines:") & " " & $iCountLines & @CRLF & translate($lng, "Remaining lines:") & " " & $iCountLines - $move_doc - 1, True)
			While _IsPressed($t)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($shift) And _IsPressed($p) Then
			writeinlog("SHIFT+P pressed")
			speaking(translate($lng, "Total number of pages:") & " " & $pages, True)
			While _IsPressed($shift) And _IsPressed($p)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($control) and _IsPressed($shift) and _IsPressed($tPlus) Then
			writeinlog("CTRL+SHIFT+plus normal keyboard pressed")
			If IniRead(@ScriptDir & "\config\config.st", "accessibility", "Speak Whit", "") = "Sapi" Or autodetect() = "Sapi" Then
				$sprate = $sprate + 1
				sprate($sprate)
				If $sprate > 10 Then
					speaking(translate($lng, "Maximum speed"), True)
					$sprate = 10
				Else
					speaking(translate($lng, "Reading speed") & " " & $sprate, True)
				EndIf
			Else
				speaking(translate($lng, "This command is not supported in") & " " & autodetect() & ".", True)
			EndIf
			While _IsPressed($control) and _IsPressed($shift) and _IsPressed($tPlus)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($tPlus) Then
			writeinlog("plus normal keyboard pressed")
			If IniRead(@ScriptDir & "\config\config.st", "accessibility", "Speak Whit", "") = "Sapi" Or autodetect() = "Sapi" Then
				$spvol = $spvol + 10
				spvolume($spvol)
				If $spvol > 100 Then
					speaking(translate($lng, "Maximum volume"), True)
					$spvol = 100
				Else
					speaking(translate($lng, "Reading volume") & " " & $spvol, True)
				EndIf
			Else
				speaking(translate($lng, "This command is not supported in") & " " & autodetect() & ".", True)
			EndIf
			While _IsPressed($tPlus)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($control) and _IsPressed($shift) and _IsPressed($tMinus) Then
			writeinlog("CTRL+SHIFT+dash normal keyboard pressed")
			If IniRead(@ScriptDir & "\config\config.st", "accessibility", "Speak Whit", "") = "Sapi" Or autodetect() = "Sapi" Then
				$sprate = $sprate - 1
				sprate($sprate)
				If $sprate <= -10 Then
					speaking(translate($lng, "Minimum speed"), True)
					$sprate = -10
				Else
					speaking(translate($lng, "reading speed") & " " & $sprate, True)
				EndIf
			Else
				speaking(translate($lng, "This command is not supported in") & " " & autodetect() & ".", True)
			EndIf
			While _IsPressed($control) and _IsPressed($shift) and _IsPressed($tMinus)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($tMinus) Then
			writeinlog("dash normal keyboard pressed")
			If IniRead(@ScriptDir & "\config\config.st", "accessibility", "Speak Whit", "") = "Sapi" Or autodetect() = "Sapi" Then
				$spvol = $spvol - 10
				spvolume($spvol)
				If $spvol <= 0 Then
					speaking(translate($lng, "Minimum volume"), True)
					$spvol = 0
				Else
					speaking(translate($lng, "reading volume") & " " & $spvol, True)
				EndIf
			Else
				speaking(translate($lng, "This command is not supported in") & " " & autodetect() & ".", True)
			EndIf
			While _IsPressed($tMinus)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($control) And _IsPressed($c) Then
			If $textselected = "" Then
				speaking(translate($lng, "You have not selected text to copy!"), True)
			Else
				If Not ClipPut($textselected) = 0 Then
					speaking(translate($lng, "the text has been copied to that clipboard"), True)
				Else
					speaking(translate($lng, "An error occurred while sending text"), True)
				EndIf
				If $bSelectionmode Then
					$bSelectionmode = false
					speaking(translate($lng, "Selection mode off"))
				EndIf
			EndIf
			While _IsPressed($control) And _IsPressed($c)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($control) And _IsPressed($a) Then
			$textselected = ""
			speaking(translate($lng, "Selecting all..."), True)
			For $selecting = 0 To $iCountLines - 1
				$textselected &= $r_file[$selecting] & @CRLF
			Next
			speaking(translate($lng, "All text was selected"))
			If $bSelectionmode Then
				$bSelectionmode = false
				speaking(translate($lng, "Selection mode off"))
			EndIF
			While _IsPressed($control) And _IsPressed($a)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($control) And _IsPressed($shift) And _IsPressed($s) Then
			If $bSelectionmode Then
				speaking(translate($lng, "He left the selection mode"), True)
				$bSelectionmode = false
			Else
				speaking(translate($lng, "Entered to the selection mode"), True)
				$bSelectionmode = true
			EndIf
			While _IsPressed($control) And _IsPressed($shift) And _IsPressed($s)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($t1) Then
			$fixingdocumentwords = StringStripWS(FileRead($sFiletoread), $STR_STRIPSPACES)
			$counter = StringSplit($fixingdocumentwords, " ")
			speaking(translate($lng, "Total number of words in the entire document:") & " " & $counter[0], True)
			If $counter[0] = 0 Then speaking(translate($lng, "There are no words"))
			While _IsPressed($t1)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($t2) Then
			$fx = StringStripWS($r_file[$move_doc], $STR_STRIPSPACES)
			$ct = StringSplit($fx, " ")
			speaking(translate($lng, "Total number of words in this line:") & " " & $ct[0], True)
			If $ct[0] = 0 Then speaking(translate($lng, "There are no words"))
			While _IsPressed($t2)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($t3) Then
			If Not $textselected = "" Then
				$fx2 = StringStripWS($textselected, $STR_STRIPSPACES)
				$ct2 = StringSplit($fx2, " ")
				speaking(translate($lng, "Total number of words based on the selection:") & " " & $ct2[0], True)
			Else
				speaking(translate($lng, "No text selected!"))
			EndIf
			While _IsPressed($t3)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($s) Then
			writeinlog("S pressed")
			speaking(translate($lng, "Automatic reading mode activated") &". " &translate($lng, "Reading all the content."))
			for $Iread = 0 to $iCountLines -1
				$move_doc = $Iread
				speaking($r_file[$Iread])
				sleep(10)
			Next
			speaking(translate($lng, "Done"))
			While _IsPressed($s)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($r) Then
			writeinlog("R pressed")
			speaking(translate($lng, "Automatic reading mode activated") &". " &translate($lng, "Reading from position at cursor."))
			for $Iread = $move_doc to $iCountLines -1
				$move_doc = $Iread
				speaking($r_file[$Iread])
				sleep(10)
			Next
			speaking(translate($lng, "Done"))
			While _IsPressed($r)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($I) Then
			writeinlog("I pressed")
			$prtemp = @TempDir & "\prtemp.txt"
			$printmenu = reader_create_menu(translate($lng, "Print options, use the arrows to navigate and enter to start"), translate($lng, "Print the entire document") & "|" & translate($lng, "Print selection") & "|" & translate($lng, "Close this menu"), 1, translate($lng, "OF"))
			Select
				Case $printmenu = 1
					$estaimpreso = _FilePrint($sFiletoread)
					If $estaimpreso Then
						Beep(1960, 200)
						MsgBox(48, translate($lng, "Done"), translate($lng, "The document has been printed successfully!"))
					Else
						MsgBox(16, translate($lng, "Error"), translate($lng, "The document could not be printed.") & @CRLF & translate($lng, "Error code:") & " " & @error)
					EndIf
				Case $printmenu = 2
					If $textselected = "" Then
						MsgBox(16, translate($lng, "Error"), translate($lng, "No text selected!"))
					Else
						$tempcreate = FileOpen($prtemp, 1)
						If Not FileWrite($tempcreate, $textselected) Then MsgBox(16, translate($lng, "Error"), translate($lng, "Cannot set temporary file with contents of selected text to print"))
						Sleep(1000)
						$isPrinted = _FilePrint($prtemp)
						If $isPrinted Then
							Beep(1960, 200)
							MsgBox(48, translate($lng, "Done"), translate($lng, "the document has been printed successfully!"))
						Else
							MsgBox(16, translate($lng, "Error"), translate($lng, "The document could not be printed.") & @CRLF & translate($lng, "Error code:") & " " & @error)
						EndIf
					EndIf
					If FileExists($prtemp) Then FileDelete($prtemp)
				Case $printmenu = 3
					ContinueLoop
			EndSelect
			While _IsPressed($I)
				Sleep(50)
			WEnd
		EndIf
		If _IsPressed($escape) Then
			writeinlog("Escape pressed")
			$newfilename = ""
			$not = 0
			If Not $textselected = "" Then
				writeinlog("there are selected elements. Opening menu.")
				$sabemenu = reader_create_menu(translate($lng, "Attention! you have selected items. Would you like to save them?"), translate($lng, "Copy to clipboard") & "|" & translate($lng, "Save to a text file") & "|" & translate($lng, "Don't save") & "|" & translate($lng, "Cancel"), 1, translate($lng, "OF"))
				writeinlog("Menu item selected: " & $sabemenu)
				Select
					Case $sabemenu = 1
						ClipPut($textselected)
						speaking(translate($lng, "Copied to clipboard"), True)
						Sleep(1000)
						ExitLoop
					Case $sabemenu = 2
						$savefile = FileSaveDialog(translate($lng, "Save document elements..."), @ScriptDir & "\documents", translate($lng, "Text files (*.txt)"), $FD_FILEMUSTEXIST)
						If $savefile = "" Then
							$createname = StringSplit($r_file[0], " ")
							IF UBound($createname) >4 then
								For $I = 1 To 3
									$newfilename &= $createname[$I] & " "
								Next
								If StringInStr($newfilename, ",") Then $newfilename = StringReplace($newfilename, ",", "")
								If StringInStr($newfilename, ":") Then $newfilename = StringReplace($newfilename, ":", "")
								$savefile = @ScriptDir & "\documents\" & StringStripWS($newfilename, $STR_STRIPTRAILING) & ".txt"
							Else
								$savefile = @ScriptDir & "\documents\selection text" &@year &"-" &@mon &"-" &@mday &" " &@hour &":" &@min &":" &@sec &".txt"
							EndIf
						EndIf
						Beep(400, 70)
						speaking(translate($lng, "Saving file, please wait..."))
						$txtfile = FileOpen($savefile, 1)
						FileWrite($txtfile, $textselected)
						Sleep(2000)
						Beep(200, 70)
						speaking(translate($lng, "Finished"))
						Sleep(500)
						ExitLoop
					Case $sabemenu = 3
						$textselected = ""
						ExitLoop
					Case $sabemenu = 4
						ContinueLoop
				EndSelect
			EndIf
			While _IsPressed($escape)
				Sleep(50)
			WEnd
			Return $move_doc
		EndIf
		Sleep(10)
	WEnd
EndFunc   ;==>createTtsDocument
