@echo off
echo ========================================
echo ARPG Item Wiki - Production Deployment
echo ========================================
echo.

echo [1/6] Upgrading pip...
python -m pip install --upgrade pip
echo.

echo [2/6] Installing Pillow (stable version)...
pip install pillow==10.0.1 --no-cache-dir
if %errorlevel% neq 0 (
    echo ⚠️ Trying alternative method...
    pip install --only-binary=pillow pillow==10.0.1
)
echo.

echo [3/6] Installing core dependencies...
pip install streamlit==1.28.1 pandas==2.1.3
echo.

echo [4/6] Installing security dependencies...
pip install streamlit-authenticator==0.3.3
pip install bleach==6.1.0
pip install PyYAML==6.0.1
echo.

echo [5/6] Installing file validation...
pip install python-magic==0.4.27
pip install python-magic-bin==0.4.14
echo.

echo [6/6] Verifying installation...
python -c "import PIL; print(f'✅ Pillow {PIL.__version__} installed')"
python -c "import streamlit; print(f'✅ Streamlit {streamlit.__version__} installed')"
python -c "import streamlit_authenticator; print(f'✅ Auth module installed')"
echo.

echo ========================================
echo ✅ Deployment complete!
echo ========================================
echo.
echo Next steps:
echo 1. Verify auth config: .streamlit/auth_config.yaml
echo 2. Run: streamlit run app.py
echo.
pause