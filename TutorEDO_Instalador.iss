#define AppName "Tutor EDO"
#define AppVersion "1.0.0"
#define AppPublisher "Tutor EDO"
#define PackageDir "Tutor_EDO_Portable"

[Setup]
AppId={{B1A65A99-BD55-4CF5-A61E-31CF9870A65D}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\Tutor EDO
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern
DisableProgramGroupPage=yes
Uninstallable=yes
OutputDir=.
OutputBaseFilename=Instalador_TutorEDO_Windows_x64
Compression=lzma2/fast
SolidCompression=yes

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "{#PackageDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: ".env,datos\tutor.sqlite3,datos\tutor.sqlite3-shm,datos\tutor.sqlite3-wal,*.pyc,python\Lib\site-packages\streamlit\.agents\*"

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\TutorEDO.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\TutorEDO.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\TutorEDO.exe"; Description: "Iniciar {#AppName}"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent
