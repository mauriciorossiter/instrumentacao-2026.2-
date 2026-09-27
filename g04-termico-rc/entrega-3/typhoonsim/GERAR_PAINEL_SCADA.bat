@echo off
setlocal
cd /d "%~dp0"

where typhoon-python >nul 2>nul
if errorlevel 1 (
    echo ERRO: typhoon-python nao foi encontrado.
    echo Abra o Typhoon HIL Control Center 2026.2 e tente novamente.
    pause
    exit /b 1
)

echo Gerando instrumento_estatico_generico.cus em modo Capture...
typhoon-python gerar_painel_scada.py --capture --force
set "RESULTADO=%ERRORLEVEL%"

if not "%RESULTADO%"=="0" (
    echo.
    echo O painel nao foi gerado. Leia a mensagem acima.
    pause
    exit /b %RESULTADO%
)

echo.
echo Painel gerado: instrumento_estatico_generico.cus
echo Carregue o modelo em SCADA VHIL mode e abra esse arquivo no HIL SCADA.
pause
exit /b 0
