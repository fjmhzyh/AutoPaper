#define MyAppName "AutoPaper"
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif

[Setup]
AppId={{7E91A3A6-7DDF-4B3A-9F3E-D8E0200749D0}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=AutoPaper
SourceDir=..\..
DefaultDirName={localappdata}\AutoPaper
DefaultGroupName=AutoPaper
DisableProgramGroupPage=yes
OutputDir=release\{#MyAppVersion}\win
OutputBaseFilename=AutoPaper-{#MyAppVersion}-win-setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\AutoPaper.exe

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"; Flags: unchecked

[Files]
Source: "dist\AutoPaper\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\AutoPaper"; Filename: "{app}\AutoPaper.exe"
Name: "{autodesktop}\AutoPaper"; Filename: "{app}\AutoPaper.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\AutoPaper.exe"; Description: "启动 AutoPaper"; Flags: nowait postinstall skipifsilent
