@echo off
setlocal
cd /d "%~dp0"
echo === FaceAccess - Instalacao ===
if not exist ".venv\Scripts\python.exe" (
    where py >nul 2>&1
    if errorlevel 1 (
        python -c "import sys, struct; assert sys.version_info[:2] == (3,12) and struct.calcsize('P') == 8"
        if errorlevel 1 goto :erro_python
        python -m venv .venv
    ) else (
        py -3.12 -m venv .venv
    )
    if errorlevel 1 goto :erro_python
)
set "PY=%CD%\.venv\Scripts\python.exe"
"%PY%" -c "import sys, struct; assert sys.version_info[:2] == (3,12) and struct.calcsize('P') == 8, 'Use Python 3.12 de 64 bits'"
if errorlevel 1 goto :erro_python
"%PY%" -m pip install --upgrade pip setuptools==80.9.0 wheel
if errorlevel 1 goto :erro
"%PY%" -m pip install -r requirements-visual.txt
if errorlevel 1 goto :erro
"%PY%" -c "import cv2, numpy, customtkinter, PIL, mediapipe as mp; assert hasattr(mp.solutions, 'selfie_segmentation')"
if errorlevel 1 goto :erro
echo Interface visual instalada.
if not exist "rostos" mkdir "rostos"
"%PY%" -c "import dlib" >nul 2>&1
if not errorlevel 1 goto :reconhecimento
echo Para instalar o reconhecimento, use o arquivo Dlib do professor.
echo Escolha o arquivo com os termos cp312-cp312-win_amd64.whl.
echo Cole o caminho completo do arquivo abaixo ou Enter para instalar somente o visual.
set "DLIB_WHEEL="
set /p "DLIB_WHEEL=Arquivo Dlib: "
if not defined DLIB_WHEEL goto :somente_visual
set "DLIB_WHEEL=%DLIB_WHEEL:"=%"
if not exist "%DLIB_WHEEL%" goto :erro
"%PY%" -m pip install "%DLIB_WHEEL%"
if errorlevel 1 goto :erro
:reconhecimento
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 goto :erro
"%PY%" -c "import dlib, face_recognition, face_recognition_models"
if errorlevel 1 goto :erro
echo Instalacao completa. Interface e reconhecimento integrados. Execute iniciar.bat.
pause
exit /b 0
:somente_visual
echo Visual disponivel. Execute .venv\Scripts\python.exe abrir_terminal.py.
echo Para instalar o reconhecimento depois, execute instalar.bat novamente.
pause
exit /b 0
:erro_python
echo Instale Python 3.12 de 64 bits. Se a .venv foi criada com outra versao, renomeie-a antes de repetir.
pause
exit /b 1
:erro
echo A instalacao falhou. Confira a mensagem exibida acima.
pause
exit /b 1
