@echo off
REM Syntactic Fine-tuning Framework - Environment Setup (Windows)
echo 🔧 Setting up Syntactic Fine-tuning Framework environment...

REM Python 버전 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.9 or higher.
    pause
    exit /b 1
)

echo ✅ Found Python
python --version

REM 가상환경 생성
echo 📦 Creating virtual environment...
python -m venv venv

REM 가상환경 활성화
echo 🚀 Activating virtual environment...
call venv\Scripts\activate

REM pip 업그레이드
echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

REM 의존성 설치
echo 📚 Installing dependencies...
pip install -r requirements.txt

echo.
echo ✅ Environment setup complete!
echo.
echo 🎯 To activate the environment in the future:
echo    venv\Scripts\activate
echo.
echo 🚀 Quick start:
echo    python run_experiment.py strategies
echo    python run_experiment.py run --name test --categories 8
echo.
echo 📚 For full documentation, see README.md
pause