# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — Hub de Ferramentas NITTRANS
# Gere o bundle com: pyinstaller hub.spec --noconfirm

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('Logo.png', '.'),
        ('logo.ico', '.'),
    ],
    hiddenimports=[
        # Interface
        'customtkinter',
        'PIL._tkinter_finder',
        # Geocodificação
        'geopy.geocoders',
        'geopy.extra.rate_limiter',
        'certifi',
        # PDF
        'pdfplumber',
        'pdfminer',
        'pdfminer.high_level',
        # Excel / dados
        'pandas',
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
        'xlrd',
        # Progresso
        'tqdm',
        # Sub-módulos do hub (importados diretamente por processamento.py)
        'LatitudeLongitude.enderecos',
        'LimpezaArquivo.limpeza',
        'OrganizadorTxtDetran.decifradorTxt',
        'PdfExcelMultas.pdfDeferidoIndeferido',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'notebook',
        'IPython',
        'pytest',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HubNITTRANS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # sem janela de console (app GUI)
    icon='logo.ico',        # gerado automaticamente pelo build.ps1
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='HubNITTRANS',
)