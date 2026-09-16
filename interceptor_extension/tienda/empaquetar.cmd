@echo off
rem Arma el ZIP que se sube a la Chrome Web Store.
rem
rem Uso, desde la raiz del repositorio:
rem     interceptor_extension\tienda\empaquetar.cmd
rem
rem Deja vetube-extension.zip en esta misma carpeta (tienda), con manifest.json
rem en la raiz del ZIP, que es lo que exige la tienda. Solo entra lo que la
rem extension usa en el navegador: ni las pruebas, ni la documentacion, ni el
rem material de la ficha de la tienda. Si se agrega un archivo a la extension,
rem hay que sumarlo a ARCHIVOS (pruebas/pruebas.js lo comprueba).
rem
rem Usa el tar.exe de Windows (10 y 11 lo traen), que arma ZIP de verdad con
rem la opcion -a. Compress-Archive de PowerShell 5.1 no sirve: guarda las rutas
rem con barra invertida y la tienda las rechaza.

setlocal
set "ARCHIVOS=manifest.json background.js logica.js popup.html popup.js iconos"
set "SALIDA=%~dp0vetube-extension.zip"

pushd "%~dp0.."
if exist "%SALIDA%" del "%SALIDA%"
"%SystemRoot%\System32\tar.exe" -a -c -f "%SALIDA%" %ARCHIVOS%
set "RESULTADO=%ERRORLEVEL%"
popd

if not "%RESULTADO%"=="0" (
  echo No se pudo armar el ZIP. Codigo de error: %RESULTADO%
  exit /b %RESULTADO%
)

echo Listo: %SALIDA%
echo Contenido:
"%SystemRoot%\System32\tar.exe" -t -f "%SALIDA%"
