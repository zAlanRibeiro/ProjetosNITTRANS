; ============================================================
; setup.iss — Instalador do Hub de Ferramentas NITTRANS
; Compilar com: Inno Setup 6  (https://jrsoftware.org/isdl.php)
; Ou rodar build.ps1 que faz tudo automaticamente.
; ============================================================

#define AppName    "Hub de Ferramentas NITTRANS"
#define AppVersion "4.0"
#define AppExeName "HubNITTRANS.exe"
#define AppId      "NITTRANS-HUB-FERRAMENTAS-2026"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=NITTRANS
AppVerName={#AppName} {#AppVersion}

; Instala em AppData\Local (sem UAC, sem precisar de admin)
DefaultDirName={localappdata}\Programs\HubNITTRANS
DefaultGroupName={#AppName}

; Saída do instalador
OutputDir=Output
OutputBaseFilename=Setup_HubNITTRANS_v{#AppVersion}
SetupIconFile=..\logo.ico

; Compressão máxima
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

; Sem UAC necessário
PrivilegesRequired=lowest

; Visual moderno
WizardStyle=modern
DisableProgramGroupPage=yes
ShowLanguageDialog=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; \
  Description: "Criar ícone na Área de Trabalho"; \
  GroupDescription: "Atalhos:"; \
  Flags: checkedonce

[Files]
; Copia todo o bundle gerado pelo PyInstaller
Source: "..\dist\HubNITTRANS\*"; \
  DestDir: "{app}"; \
  Flags: ignoreversion recursesubdirs createallsubdirs

; Cache de geocodificação pré-preenchido — não sobrescreve se o usuário já tem um
Source: "..\LatitudeLongitude\cache_enderecos.json"; \
  DestDir: "{app}\LatitudeLongitude"; \
  Flags: ignoreversion onlyifdoesntexist

; Cache de ruas do Detran Limpo — não sobrescreve cache acumulado pelo usuário
Source: "..\DetranLimpo\cache_ruas.json"; \
  DestDir: "{app}\DetranLimpo"; \
  Flags: ignoreversion onlyifdoesntexist skipifsourcedoesntexist

[Icons]
; Menu Iniciar
Name: "{group}\{#AppName}";         Filename: "{app}\{#AppExeName}"
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"

; Área de trabalho (opcional, marcado por padrão)
Name: "{userdesktop}\{#AppName}"; \
  Filename: "{app}\{#AppExeName}"; \
  Tasks: desktopicon

[Run]
; Oferecer iniciar o app ao final da instalação
Filename: "{app}\{#AppExeName}"; \
  Description: "Iniciar {#AppName} agora"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove as pastas de trabalho geradas pelo app (entrada, backup, resultados)
Type: filesandordirs; Name: "{app}\LatitudeLongitude"
Type: filesandordirs; Name: "{app}\LimpezaArquivo"
Type: filesandordirs; Name: "{app}\OrganizadorTxtDetran"
Type: filesandordirs; Name: "{app}\PdfExcelMultas"
Type: filesandordirs; Name: "{app}\ProcessosAbertos"
Type: filesandordirs; Name: "{app}\DetranLimpo"