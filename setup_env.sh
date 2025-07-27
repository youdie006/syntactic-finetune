#!/bin/bash

# Syntactic Fine-tuning Framework - Environment Setup
echo "🔧 Setting up Syntactic Fine-tuning Framework environment..."

# Python 버전 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
echo "✅ Found Python $PYTHON_VERSION"

# 가상환경 생성
echo "📦 Creating virtual environment..."
python3 -m venv venv

# 가상환경 활성화
echo "🚀 Activating virtual environment..."
source venv/bin/activate

# pip 업그레이드
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# 의존성 설치
echo "📚 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Environment setup complete!"
echo ""
echo "🎯 To activate the environment in the future:"
echo "   source venv/bin/activate"
echo ""
echo "🚀 Quick start:"
echo "   python3 run_experiment.py strategies"
echo "   python3 run_experiment.py run --name test --categories 8"
echo ""
echo "📚 For full documentation, see README.md"