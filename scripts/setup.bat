@echo off
REM IPTV Playlist Manager - Windows Development Setup Script

echo 🚀 Setting up IPTV Playlist Manager for development...

REM Create necessary directories
echo 📁 Creating directories...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "static" mkdir static
if not exist "uploads" mkdir uploads
if not exist "config" mkdir config

REM Copy environment file if it doesn't exist
if not exist ".env" (
    echo 📝 Creating environment configuration...
    copy .env.example .env
    echo ⚠️  Please review and update the .env file with your settings
)

REM Backend setup
echo 🐍 Setting up Python backend...
cd backend

if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing Python dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Initialize database
echo 🗄️ Initializing database...
python scripts\init_db.py

echo ✅ Backend setup completed!

REM Frontend setup
cd ..\frontend
echo ⚛️ Setting up React frontend...

if not exist "node_modules" (
    echo Installing Node.js dependencies...
    npm install
)

echo ✅ Frontend setup completed!

cd ..

echo.
echo 🎉 Setup completed successfully!
echo.
echo To start the development servers:
echo   Backend:  cd backend ^&^& venv\Scripts\activate ^&^& uvicorn main:app --reload
echo   Frontend: cd frontend ^&^& npm start
echo.
echo Or use Docker Compose:
echo   docker-compose up -d
echo.
echo Default admin credentials:
echo   Username: admin
echo   Password: admin
echo.
echo ⚠️  Please change the default password after first login!

pause
