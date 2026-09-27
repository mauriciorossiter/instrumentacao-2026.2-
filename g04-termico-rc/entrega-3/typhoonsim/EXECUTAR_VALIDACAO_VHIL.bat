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

echo Iniciando compilacao, execucao VHIL, aquisicao e analise...
typhoon-python executar_validacao_vhil.py
set "RESULTADO=%ERRORLEVEL%"

if not "%RESULTADO%"=="0" (
    echo.
    echo A validacao nao terminou com sucesso. Leia a mensagem acima.
    pause
    exit /b %RESULTADO%
)

echo.
echo Validacao concluida. Os arquivos estao em resultados_vhil.
echo Recompile o relatorio para incorporar automaticamente os dados.
pause
exit /b 0
