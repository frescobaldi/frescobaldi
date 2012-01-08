[Setup]
AppName=Frescobaldi
AppVersion=2.0.1
DefaultDirName={pf}\Frescobaldi
DefaultGroupName=Frescobaldi
UninstallDisplayIcon={app}\frescobaldi.exe
Compression=lzma2
SolidCompression=yes

SourceDir=frozen\
OutputDir=..\dist\
OutputBaseFilename=Frescobaldi-2.0.1.installer
SetupIconFile=frescobaldi_app\icons\frescobaldi.ico
LicenseFile=..\COPYING
WizardImageFile=..\frescobaldi-wininst.bmp
WizardImageStretch=no

[Files]
Source: "*.*"; DestDir: "{app}"; Flags: recursesubdirs;

[Icons]
Name: "{group}\Frescobaldi"; Filename: "{app}\frescobaldi.exe";

[Tasks]
Name: assocly; Description: "Associate Frescobaldi with &LilyPond files";

[Registry]
Root: HKCR; Subkey: "LilyPond\shell\frescobaldi"; ValueType: string; ValueName: ""; ValueData: "Edit with &Frescobaldi..."; Flags: uninsdeletekey
Root: HKCR; Subkey: "LilyPond\shell\frescobaldi\command"; ValueType: string; ValueName: ""; ValueData: """{app}\frescobaldi.exe"" ""%1"""
Tasks: assocly; Root: HKCR; Subkey: "LilyPond\shell"; ValueType: string; ValueName: ""; ValueData: "frescobaldi";

