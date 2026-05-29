@echo off
echo Instalando dependencias...
pip install cryptography customtkinter pyinstaller

echo.
echo Gerando executavel...
pyinstaller --onefile --windowed --collect-data customtkinter --add-data "Logo.png;." --name "CriptografadorDeArquivos" criptografia.py

echo.
echo Pronto! O executavel esta em: dist\CriptografadorDeArquivos.exe
pause
