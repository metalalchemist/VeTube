#AutoIt3Wrapper_Compile_Both=N
#AutoIt3Wrapper_UseX64=n
#AutoIt3Wrapper_Change2CUI=N
#AutoIt3Wrapper_Res_Description=Tacotron 2 support for VeTube
#AutoIt3Wrapper_Res_Fileversion=0.1.0.0
;#AutoIt3Wrapper_Res_Fileversion_Use_Template=%YYYY.%MO.%DD.0
#AutoIt3Wrapper_Res_Fileversion_AutoIncrement=p
;#AutoIt3Wrapper_Res_Fileversion_First_Increment=y
#AutoIt3Wrapper_Res_ProductName=Tacotron4VeTube
#AutoIt3Wrapper_Res_ProductVersion=0.1.0.0
#AutoIt3Wrapper_Res_CompanyName=Mateo Cedillo
#AutoIt3Wrapper_Res_LegalCopyright=© 2018-2022 MT Programs, All rights reserved
;#AutoIt3Wrapper_Res_Language=12298
;#AutoIt3Wrapper_AU3Check_Parameters=-d -w 1 -w 2 -w 3 -w 4 -w 5 -w 6 -w 7 -v1 -v2 -v3
#AutoIt3Wrapper_Run_Tidy=n
;#AutoIt3Wrapper_Run_Au3Stripper=y
#Au3Stripper_Parameters=/so
;#AutoIt3Wrapper_Versioning=v
;#AutoIt3Wrapper_Run_Before="buildsounds.bat"
;#AutoIt3Wrapper_Run_After=encrypter-auto.exe
#EndRegion ;**** Directives created by AutoIt3Wrapper_GUI ****
; Tacotron2 for VeTube
;By Mateo Cedillo
;set directives for pragma
#pragma compile(Out, TT4VeTube.exe)
; #pragma compile(Icon, C:\Program Files\AutoIt3\Icons\au3.ico)
#pragma compile(UPX, False)
;#pragma compile(Compression, 2)
#pragma compile(inputboxres, false)
#pragma compile(FileDescription, Tacotron 2 support for vetube)
#pragma compile(ProductName, Tacotron4VeTube)
#pragma compile(ProductVersion, 0.1.0.0)
#pragma compile(Fileversion, 0.1.0.0)
#pragma compile(InternalName, "mateocedillo.TT2")
#pragma compile(LegalCopyright, © 2018-2022 MT Programs, All rights reserved)
#pragma compile(CompanyName, 'MT Programs')
#pragma compile(OriginalFilename, TT4VeTube.exe)
;includes:
#include <AutoItConstants.au3>
;#include "include\bassfunctions.au3"
#include <comboConstants.au3>
;#include "include\fakeyou.au3"
#include <FileConstants.au3>
#include "include\GenerateAudio.au3"
#include "include\getfile.au3"
#include <GuiConstantsEx.au3>
#include <GuiListBox.au3>
#include "include\Json.au3"
#include "include\reader.au3"
#include "include\voiceDownloader.au3"
#include "include\zip.au3"
; verificamos el proceso:
If Not ProcessExists("vetube.exe") Then
	MsgBox(16, "Error", "El complemento no se puede inicializar porque vetube no está abierto. Saliendo...")
	Exit
EndIf
; falta por hacer: sistema de actualizaciones del plugin.
; creamos o revisamos las configuraciones:
If Not FileExists(@ScriptDir & "\config") Then DirCreate(@ScriptDir & "\config")
$sJson = _GetFileData(@ScriptDir & "\..\..\..\data.json") ; esto corresponde a que de la carpeta client retrocede a la del plugin, la del plugin retrocede a la carpeta plugins y estando en la carpeta de plug-ins retrocede a la carpeta principal de vetube.
If @error Then
	MsgBox(16, "Error", "Ha ocurrido un error al leer las configuraciones del programa.")
	Exit
EndIf
; la configuración de vetube está en formato JSON, vamos a descifrarla.
$oDecodeJson = Json_decode($sJson)
; esto se podría usar para un futuro. Lo siguiente son booleanos.
Global $bReader = json_get($oDecodeJson, '["reader"]')
Global $bSapi = json_get($oDecodeJson, '["sapi"]')
; la ruta del servidor:
Global $sServerPath = IniRead(@ScriptDir & "\config\config.st", "general", "server path", "")
If $sServerPath = "" Then
	; establecer y escribir:
	$sServerPath = @ScriptDir & "\..\server"
	IniWrite(@ScriptDir & "\config\config.st", "general", "server path", $sServerPath)
EndIf
; comprobar ejecución del servidor. El comportamiento de la primera línea después de este comentario para muchos inclyendo a mí, parecerá muy tonto; Ya que, verificando el proceso de python.exe podemos estar ejecutando otras cosas a parte del servidor. Si le ponemos a verificar únicamente el proceso app.exe estaríamos limitando totalmente las pruebas desde el código fuente, lo que conlleba que nos vemos en la obligación de compilar o hacer una versión distributiva del servidor.
If ProcessExists("python.exe") Or ProcessExists("app.exe") Then
	speaking("Servidor en aire. Saltando la ejecución...", True)
Else
	RunServer($sServerPath)
EndIf
Main()
Func RunServer($sPath)
	Local $sExe
	; verificar si el plug-in se ejecuta desde el código. Si es así, ejecuta el servidor desde su código también. Caso contrario, se ejecuta desde la versión compilada/distributiva.
	If @Compiled Then
		; Bueno, yo he compilado con cxFreece, pero desafortunadamente he conseguido algunos errores de ejecución al final. En base a este compilador, crea una ruta dist donde está una versión preparada. Puedes cambiar la parte de dist por la ruta donde está el servidor distribuido.
		$sExe = $sPath & "\dist\app.exe"
	Else
		; falta por hacer: hacer la verificación por si python está o no instalado.
		$sExe = "python " & $sPath & "\app.py"
	EndIf
	; ahora ejecutamos el servidor:
	If FileExists($sExe) And @Compiled Then
		speaking("Inicializando servidor...", True)
		Local $iPid = Run($sExe, $sPath, @SW_SHOW, 6)
	ElseIf FileExists($sPath & "\app.py") And Not @Compiled Then
		speaking("Inicializando servidor desde el código...", True)
		Local $iPid = Run($sExe, $sPath, @SW_SHOW, 6)
	Else
		MsgBox(16, "Error", "No se ha podido iniciar el servidor. Por favor, asegúrate de que las rutas son correctas.")
		Exit
	EndIf
	; vamos a monitorear o hacer un seguimiento de los mensajes de entrada que envía el servidor a la consola. Esto es útil para saver cuándo el servidor se inició.
	Local $sStdout
	While 1
		$sStdout = StdoutRead($iPid)
		If @error Then ExitLoop
		If $sStdout <> "" Then
			If StringInStr($sStdout, " * Serving Flask app 'app' (lazy loading)") Then
				Beep(500, 200)
				speaking("¡Servidor de voces iniciado!")
				ExitLoop
			EndIf
		EndIf
		Sleep(10) ; disminuyendo el uso de la CPU
	WEnd
EndFunc   ;==>RunServer
Func Main()
	Local $bFirstStart = True, $bFound = False
	Local $hWND
	Local $iOldCount = "", $iCount = ""
	Local $sText = "", $sWindowName = "Chat en vivo"
	Local $ConfigPath = @ScriptDir & "\Config\config.st"
	Local $sChatName = IniRead($ConfigPath, "General", "read name chats", "")
	; Config. Por defecto para la lectura de nombres de los que envían los chats. Por defecto nombre y mensaje, tal cual lo hace vetube.
	If $sChatName = "" Then
		$sChatName = "yes"
		IniWrite($ConfigPath, "General", "read name chats", $sChatName)
	EndIf
	Local $sDataPath = $sServerPath & "\data"
	Local $sVoice = IniRead($ConfigPath, "voice settings", "voice", "")
	; listamos las voces disponibles y excluimos el modelo de hifi-gan, más adelante sabremos para qué:
	Local $aVoiceFiles = _FileListToArrayRec($sDataPath, "*.pt|hifigan.pt", 1, 0, 2)
	; comprobación de modelos:
	If $sVoice = "" Then
		MsgBox(48, "¡Atención!", "Parece que no tienes voces descargadas. A continuación, se te redirigirá al apartado de descarga." & @CRLF & "Después de hacer esto, deberás reiniciar el complemento.")
		; falta por hacer: detectar qué voces tiene el usuario para que solo muestre las que no tiene en lugar de todas (es decir, las nuevas).
		; falta por hacer #2: descargar la muestra de audio de la voz seleccionada después de ella.
		; falta #3: hacer los audios de cada voz para el botón previsualizar.
		_Descargador_de_voces()
	ElseIf Not FileExists($sDataPath & "\" & $sVoice & ".pt") Then
		MsgBox(16, "Error", "No se ha podido localizar la voz " & $sVoice & ", el archivo del modelo de voz se movió o se eliminó. Saliendo...")
		Exitpersonaliced()
	ElseIf $aVoiceFiles[0] = 1 Then
		IniWrite($ConfigPath, "voice settings", "voice", $aVoiceFiles[1])
	ElseIf Not FileExists($sDataPath & "\config.json") Or Not FileExists($sDataPath & "\hifigan.pt") Then
		; descargamos el vocoder hifi-gan
		speaking("Hemos comprobado que faltan archivos del vocoder. Descargándolos...")
		Local $percent
		$sURL = "https://www.dropbox.com/s/ahrhmku86cfiagt/hifigan.zip?dl=1"
		$dwn = InetGet($sURL, $sDataPath & "\hifi-gan.zip", 1, 1)
		; obtenemos el tamaño del archivo:
		$Size = InetGetSize($sURL)
		; esperamos mientras la descarga está en curso para consultar el progreso:
		While Not InetGetInfo($dwn, 2)
			$Size2 = InetGetInfo($dwn, 0)
			$oldpercent = $percent
			$percent = Int($Size2 / $Size * 100)
			$iSize = $Size - $Size2
			If $percent <> $oldpercent Then speaking($percent & "%")
			Sleep(10)
		WEnd
		speaking("Extrayendo contenidos...")
		; descomprimir el vocoder:
		_Zip_UnzipAll($sDataPath & "\hifi-gan.zip", $sDataPath, 0)
		If @error Then
			Switch @error
				Case 1
					MsgBox(16, "Error", "No se ha podido descargar el vocoder. Comprueba la conexión a internet o inténtalo más tarde.")
				Case 2
					MsgBox(16, "Error fatal", "¡Falta la biblioteca para manejar archivos zip!")
				Case 3
					MsgBox(16, "Error", "Hay bibliotecas zip que no han sido registradas")
			EndSwitch
			Exitpersonaliced()
		EndIf
		Sleep(1000)
		FileDelete($sDataPath & "\hifi-gan.zip")
		speaking("¡Listo!")
	EndIf
	;establecer atajos globales:
	HotKeySet("^+e", "exitpersonaliced")
	HotKeySet("^+s", "Settings")
	; ejecutamos la función que espera a la ventana.
	If $bFirstStart Then $bFound = pause()
	; si la bentana está activa...
	If $bFound Then
		$hWND = WinActivate("Chat en vivo")
		$idList = ControlGetHandle($hWND, "", "ListBox1")
		Sleep(1000)
		speaking("¡Complemento en ejecución! Puedes pulsar los atajos control+shift+s para configuraciones del complemento o control+shift+e para salir del cliente", True)
		; el bucle en donde podamos monitorear la lista en caso de nuevos elementos:
		While WinExists($sWindowName)
			$iOldCount = $iCount
			$iCount = _GUICtrlListBox_GetCount($idList)
			If $iCount <> $iOldCount Then
				; registrar texto de la lista:
				$sText = _GUICtrlListBox_GetText($idList, $iCount - 1)
				; si el usuario no prefiere que se lean los nombres de chats...
				If $sChatName = "No" Then $sText = StringSplit($sText, ": ", $STR_ENTIRESPLIT)[2]
				; solicitar el audio al servidor. Me he dado cuenta que al menos Http_get experimenta un pequeño bloqueo cuando envía la solicitud. Esto al ser ejecutado en un servidor local. Puede funcionar mucho mejor si hosteamos el servidor en una VPS, en una página WEB, por ejemplo.
				$sRequest = _GenerateAudio($sVoice, $sText)
				If @error Then MsgBox(16, "Error", "Ha ocurrido un error durante el envío de la solicitud al servidor. Provablemente cayó o no está disponible")
			Else
				ContinueLoop
			EndIf
			Sleep(30)
		WEnd
		$bFirstStart = False
		pause($bFirstStart)
	EndIf
EndFunc   ;==>Main
func _Descargador_de_voces()
	if not @Compiled then
		return downloadvoices(null, default)
	else
		return downloadvoices(default, "online")
	EndIf
	If @error Then
		switch @error
			case 1
				MsgBox(16, "Error", "No se ha encontrado la lista de voces desde el código del servidor")
			case 2
				MsgBox(16, "Algo falló", "No hemos podido acceder a la lista de voces, ya que esto se debe a una posible caída del servidor en línea o tu conexión a internet. Saliendo...")
			case 3
				MsgBox(16, "Error técnico", "No se ha realizado esta operación debido a parámetros incorrectos.")
			case 4
				msgbox(16, "error", "La base de datos de voces está corrupta. Esto puede ser por cuestiones de caída de servidor o por tu conexión a internet.")
		EndSwitch
		exitpersonaliced()
	EndIf
EndFunc
Func pause($bFirstStart = True)
	; función que se encarga de dormir el plugin mientras la ventana de chat no está activa.
	speaking("Esperando ejecución del chat...")
	While 1
		If WinExists("Chat en vivo") Then
			Return True
			ExitLoop
		EndIf
		Sleep(50)
	WEnd
	speaking("Ventana de chat detectada. Corriendo tt4vetube...")
	If Not $bFirstStart Then Main()
EndFunc   ;==>pause
Func Settings()
	Local $ConfigPath = @ScriptDir & "\Config\config.st"
	Local $sDataPath = $sServerPath & "\data"
	Local $sResultsPath = $sServerPath & "\results"
	Local $sChatName = IniRead($ConfigPath, "General", "read name chats", "")
	Local $sVoice = IniRead($ConfigPath, "voice settings", "voice", "")
	$hWindow = GUICreate("Configuración del complemento tt4vetube")
	$tablabel = GUICtrlCreateLabel("Categorías:", 10, 10, 70, 20)
	$pestana = GUICtrlCreateTab(10, 20, 200, 100)
	$tabitem1 = GUICtrlCreateTabItem(translate($lng, "Configuración general"))
	$idReadnames = GUICtrlCreateCheckbox("Leer los nombres de los que envían los chats", 50, 100 + (0 * 25), 350, 25)
	If $sChatName = "yes" Then GUICtrlSetState($idReadnames, $GUI_CHECKED)
	$idClearcache = GUICtrlCreateButton("Borrar caché de audios del servidor", 50, 100 + (1 * 25), 350, 25)
	$idTabitem2 = GUICtrlCreateTabItem("Configuración de voz")
	$idChangevoice = GUICtrlCreateLabel("Seleccionar voz", 50, 110 + (0 * 25), 200, 25)
	$idChoosev = GUICtrlCreateCombo("", 230, 110 + (0 * 25) - 5, 100, 30, BitOR($CBS_DROPDOWNLIST, $CBS_AUTOHSCROLL))
	$aFiles = _FileListToArrayRec($sDataPath, "*.pt|hifigan.pt", 1, 0, 2)
	For $i = 1 To $aFiles[0]
		GUICtrlSetData($idChoosev, StringTrimRight($aFiles[$i], 3))
	Next
	$idDwnvoices = GUICtrlCreateButton("Descargar voces", 230, 110 + (1 * 25) - 5, 100, 30)
	$idRequestvoices = GUICtrlCreateButton("¿Te gustaría que agreguemos una nueva voz? Solicítanosla aquí", 230, 110 + (1 * 25) - 5, 100, 30)
	GUICtrlCreateTabItem("")
	$idDeleteconfig = GUICtrlCreateButton("borrar configuraciones", 160, 240, 50, 30)
	$idBTN_Close = GUICtrlCreateButton("&aplicar", 230, 240, 50, 30)
	GUISetState(@SW_SHOW)
	While 1
		Switch GUIGetMsg()
			Case $idReadnames
				If _IsChecked($idReadnames) Then
					IniWrite($ConfigPath, "General", "read name chats", "Yes")
				Else
					IniWrite($ConfigPath, "General", "read name chats", "No")
				EndIf
			Case $idClearcache
				If FileExists($sResultsPath & "\*.wav") Then
					FileDelete($sResultsPath & "\*.wav")
					MsgBox(48, "Información", "La caché ha sido borrada.")
				Else
					MsgBox(16, "Error", "No hay caché disponible.")
				EndIf
			Case $idChoosev
				$sComboRead = GUICtrlRead($idChoosev)
				IniWrite($ConfigPath, "voice settings", "voice", $sComboRead)
				SoundPlay($sDataPath & "\" & $sComboRead & ".wav", 0)
			Case $idDwnvoices
				_Descargador_de_voces()
			Case $idDeleteconfig
				clear()
			Case $idRequestvoices
				ShellExecute("https://docs.google.com/forms/d/e/1FAIpQLSffCTHIw5dgqHKrzFT2EhGJUzGRchn77_noB3nEktFcjntQNw/viewform?usp=sf_link")
			Case -3, $idBTN_Close
				GUIDelete($hWindow)
				ExitLoop
		EndSwitch
	WEnd
EndFunc   ;==>Settings
Func clear()
	$confirmarborrado = MsgBox(4, "Borrar configuraciones", "¿Estás seguro?")
	Select
		Case $confirmarborrado = 6
			$ifisdeleting = FileDelete(@ScriptDir & "\config\config.st")
			If $ifisdeleting = 0 Then
				MsgBox(16, "Error", "No se puede eliminar el archivo de configuración.")
			Else
				MsgBox(48, "Información", "Reinicia el complemento para que los cambios surtan efecto.")
				Exitpersonaliced()
			EndIf
	EndSelect
EndFunc   ;==>clear
Func Exitpersonaliced()
	$sOnExit = IniRead(@ScriptDir & "\config\config.st", "general", "on exit warning", "")
	If $sOnExit = "" Then
		MsgBox(48, "Antes de salir", "El cliente se cerrará; sin embargo, el servidor aún está  ejecución, por lo que tendrás que cerrarlo manualmente." & @CRLF & "A continuación, ve a la ventana que empieza con una ruta de archivo. Enfócala y, seguidamente, presiona CTRL+c para salir." & @CRLF & "Nota: Este mensaje solo se mostrará una vez.")
		IniWrite(@ScriptDir & "\config\config.st", "general", "on exit warning", "1")
	EndIf
	Exit
EndFunc   ;==>Exitpersonaliced
Func _IsChecked($idControlID)
	Return BitAND(GUICtrlRead($idControlID), $GUI_CHECKED) = $GUI_CHECKED
EndFunc   ;==>_IsChecked
