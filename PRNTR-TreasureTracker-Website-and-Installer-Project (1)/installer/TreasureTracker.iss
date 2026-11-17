#define MyAppName "PRNTR Treasure Tracker"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "PRNTR"
#define MyAppExeName "TreasureTracker.exe"
[Setup]
AppId={{A709C437-441B-42B4-A7B2-DB3164028F79}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\PRNTR Treasure Tracker
DefaultGroupName={#MyAppName}
PrivilegesRequired=lowest
OutputDir=..\output
OutputBaseFilename=TreasureTrackerSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
[Files]
Source: "..\dist\TreasureTracker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autoprograms}\PRNTR Treasure Tracker"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Treasure Tracker"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Treasure Tracker"; Flags: nowait postinstall skipifsilent
