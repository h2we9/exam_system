[Setup]
AppName=نظام توزيع المراقبين
AppVersion=2.0
DefaultDirName={autopf}\ExamSystem
DefaultGroupName=نظام توزيع المراقبين
OutputDir=Output
OutputBaseFilename=ExamSystem_Setup
Compression=lzma
SolidCompression=yes
SetupIconFile=icon.ico
; Add these lines
WizardStyle=modern
WizardSizePercent=120
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=no
DisableFinishedPage=no

[Languages]
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\نظام توزيع المراقبين.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\نظام توزيع المراقبين"; Filename: "{app}\نظام توزيع المراقبين.exe"
Name: "{commondesktop}\نظام توزيع المراقبين"; Filename: "{app}\نظام توزيع المراقبين.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\نظام توزيع المراقبين.exe"; Description: "{cm:LaunchProgram,نظام توزيع المراقبين}"; Flags: nowait postinstall skipifsilent