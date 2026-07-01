; ============================================================================
;  VeTube - Script de instalador (Inno Setup 6.3+)
;  ---------------------------------------------------------------------------
;  Genera "VeTube-setup.exe" a partir de la carpeta YA COMPILADA por
;  PyInstaller (dist\VeTube). Es un complemento: la versión portátil
;  (VeTube-x64.zip) se mantiene tal cual; este instalador se ofrece ADEMÁS.
;
;  Compilar (desde la raíz del repo):
;     iscc installer\vetube.iss
;  o pasando la versión desde el workflow (la etiqueta de git):
;     iscc /DMyAppVersion=3.8 installer\vetube.iss
;
;  Las rutas son relativas a la ubicación de este .iss (installer\), por lo
;  que funciona sin importar desde qué carpeta se invoque iscc.
; ============================================================================

; --- Version (sobreescribible con /DMyAppVersion=...). Por defecto: la de updater.py ---
#ifndef MyAppVersion
  #define MyAppVersion "3.8"
#endif

; --- Carpeta compilada (salida de PyInstaller + recursos). Sobreescribible con /DSourceDir=... ---
; Relativa a este .iss: installer\ -> ..\dist\VeTube  (= raiz_repo\dist\VeTube)
#ifndef SourceDir
  #define SourceDir "..\dist\VeTube"
#endif

#define MyAppName "VeTube"
#define MyAppExeName "run_main_window.exe"
#define MyAppPublisher "metalalchemist"
#define MyAppURL "https://github.com/metalalchemist/VeTube"

[Setup]
; AppId identifica la aplicacion de forma unica. NO cambiar entre versiones
; (asi las nuevas versiones actualizan la instalacion existente en vez de duplicarla).
AppId={{B7E6F3A2-9C4D-4E8B-A1F5-2D6C8E0A4B19}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases

; --- Instalacion POR USUARIO (sin administrador) ---
; VeTube se auto-actualiza (update\bootstrap) y descarga idiomas escribiendo
; en su PROPIA carpeta. Por eso NO debe instalarse en "Archivos de programa"
; (requeriria admin y fallarian tanto la auto-actualizacion como la descarga
; de idiomas desde "Ayuda > Actualizar idiomas"). Se instala en la carpeta
; local del usuario, sin UAC (mas comodo tambien con lectores de pantalla).
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; La build es de 64 bits.
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; --- Salida ---
OutputDir=.
OutputBaseFilename=VeTube-setup
Compression=lzma2/max
SolidCompression=yes

; Asistente moderno (se lee mejor con lectores de pantalla como NVDA/JAWS).
WizardStyle=modern
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}

; Icono del propio instalador (descomentar si se dispone de un .ico):
; SetupIconFile=..\ruta\al\icono.ico

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "french";  MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
; Acceso directo en el escritorio (casilla opcional, marcada por defecto).
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; ---------------------------------------------------------------------------
;  CLAVE (que no falte ninguna biblioteca):
;  Se empaqueta TODA la carpeta compilada de forma RECURSIVA. Asi se incluyen
;  automaticamente:
;    - _internal\  -> Python embebido + TODAS las DLL/.pyd y dependencias
;                     (incluido prism, recopilado con --collect-binaries prism)
;    - bootstrap.exe, chat_downloader\, 64\ (VLC), locales\, sounds\,
;      languages.json, etc.
;  No se listan las bibliotecas una por una: se toma la build COMPLETA, la
;  misma que produce el zip portatil. Por tanto, si la portatil arranca, la
;  instalada tambien: es imposible que falte una dependencia.
; ---------------------------------------------------------------------------
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
; Acceso directo en el menu Inicio -> permite abrir VeTube escribiendo "VeTube" + Enter.
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
; Acceso directo en el escritorio (si se marco la tarea).
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
; Ofrecer iniciar VeTube al terminar la instalacion.
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Al desinstalar, borrar tambien lo que la app haya escrito DESPUES y que el
; instalador no registro (idiomas descargados, auto-actualizaciones, logs).
Type: filesandordirs; Name: "{app}"
