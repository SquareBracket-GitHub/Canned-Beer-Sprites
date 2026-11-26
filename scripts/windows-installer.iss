; Build with scripts/build_installer.py. Install for the current user only.
#ifndef AppVersion
  #error AppVersion is required
#endif
#ifndef SourceExe
  #error SourceExe is required
#endif
#ifndef ReleaseDir
  #error ReleaseDir is required
#endif
#ifndef AppIcon
  #error AppIcon is required
#endif

[Setup]
AppId={{31576DA3-18DA-4E17-B45C-CCBD33C2C5C4}
AppName=canned beer sprites
AppVersion={#AppVersion}
AppPublisher=New Potato
AppPublisherURL=https://github.com/SquareBracket-GitHub/Canned-Beer-Sprites
AppSupportURL=https://github.com/SquareBracket-GitHub/Canned-Beer-Sprites/issues
DefaultDirName={localappdata}\Programs\canned beer sprites
DefaultGroupName=canned beer sprites
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir={#ReleaseDir}
OutputBaseFilename=canned-beer-sprites-v{#AppVersion}-windows-x64-setup
SetupIconFile={#AppIcon}
UninstallDisplayIcon={app}\canned-beer-sprites.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
#ifdef SignedBuild
SignTool=CBSSign
SignedUninstaller=yes
#endif

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: checkedonce

[Files]
Source: "{#SourceExe}"; DestDir: "{app}"; DestName: "canned-beer-sprites.exe"; Flags: ignoreversion

[Icons]
Name: "{group}\canned beer sprites"; Filename: "{app}\canned-beer-sprites.exe"; WorkingDir: "{app}"; AppUserModelID: "SquareBracket.CannedBeerSprites"
Name: "{autodesktop}\canned beer sprites"; Filename: "{app}\canned-beer-sprites.exe"; WorkingDir: "{app}"; AppUserModelID: "SquareBracket.CannedBeerSprites"; Tasks: desktopicon

[Run]
Filename: "{app}\canned-beer-sprites.exe"; Description: "Launch canned beer sprites"; Flags: nowait postinstall skipifsilent
