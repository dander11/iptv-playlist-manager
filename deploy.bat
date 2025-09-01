@echo off
REM IPTV Playlist Manager - Windows Deploy Script
REM This script automates the deployment process on Windows

setlocal enabledelayedexpansion

REM Configuration
set "REPO_URL=git@github.com:dander11/iptv-playlist-manager.git"
set "APP_NAME=iptv-playlist-manager"
set "DEFAULT_PORT=8000"

REM Function to print status messages
:print_status
echo [INFO] %~1
goto :eof

:print_warning
echo [WARN] %~1
goto :eof

:print_error
echo [ERROR] %~1
goto :eof

:print_header
echo ========================================
echo   IPTV Playlist Manager - Quick Deploy
echo ========================================
goto :eof

REM Function to generate JWT secret (Windows compatible)
:generate_jwt_secret
powershell -Command "& {$bytes = New-Object byte[] 32; (New-Object Security.Cryptography.RNGCryptoServiceProvider).GetBytes($bytes); [Convert]::ToBase64String($bytes) -replace '[^a-zA-Z0-9]', '' | Write-Output}"
goto :eof

REM Function to check prerequisites
:check_prerequisites
call :print_status "Checking prerequisites..."

docker --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Docker is not installed. Please install Docker Desktop first."
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit /b 1
)

git --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Git is not installed. Please install Git first."
    exit /b 1
)

call :print_status "All prerequisites met!"
goto :eof

REM Function to clone repository
:clone_repo
if exist "%APP_NAME%" (
    call :print_warning "Directory %APP_NAME% already exists. Updating..."
    cd /d "%APP_NAME%"
    git pull origin main
) else (
    call :print_status "Cloning repository..."
    git clone %REPO_URL% %APP_NAME%
    cd /d "%APP_NAME%"
)
goto :eof

REM Function to setup environment
:setup_environment
call :print_status "Setting up environment..."

if not exist ".env" (
    if exist ".env.production" (
        copy ".env.production" ".env" >nul
        call :print_status "Created .env from .env.production template"
    ) else (
        REM Create basic .env file
        call :generate_jwt_secret > temp_secret.txt
        set /p JWT_SECRET=<temp_secret.txt
        del temp_secret.txt
        
        (
            echo # IPTV Playlist Manager Configuration
            echo JWT_SECRET_KEY=!JWT_SECRET!
            echo CORS_ORIGINS=*
            echo VALIDATION_SCHEDULE=0 2 * * *
            echo MAX_PLAYLIST_SIZE=104857600
            echo LOG_LEVEL=INFO
            echo PORT=8000
        ) > .env
        call :print_status "Created .env file with generated JWT secret"
    )
) else (
    call :print_warning ".env file already exists, skipping creation"
)

REM Check if JWT_SECRET_KEY needs to be generated
findstr /C:"JWT_SECRET_KEY=" .env | findstr /C:"JWT_SECRET_KEY=$" >nul 2>&1
if not errorlevel 1 (
    call :generate_jwt_secret > temp_secret.txt
    set /p NEW_JWT_SECRET=<temp_secret.txt
    del temp_secret.txt
    
    powershell -Command "(Get-Content .env) | ForEach-Object { $_ -replace 'JWT_SECRET_KEY=.*', 'JWT_SECRET_KEY=!NEW_JWT_SECRET!' } | Set-Content .env"
    call :print_status "Generated new JWT secret key"
)
goto :eof

REM Function to deploy application
:deploy_app
call :print_status "Deploying application..."

REM Check if port is available
netstat -an | findstr ":8000 " >nul 2>&1
if not errorlevel 1 (
    call :print_warning "Port %DEFAULT_PORT% is already in use. You may need to change the port mapping."
)

REM Build and start the application
docker-compose -f docker-compose.standalone.yml build
docker-compose -f docker-compose.standalone.yml up -d

call :print_status "Application deployed successfully!"
goto :eof

REM Function to show deployment info
:show_deployment_info
echo.
echo 🎉 Deployment Complete!
echo.
echo Application URLs:
echo   Web UI: http://localhost:%DEFAULT_PORT%
echo   API Docs: http://localhost:%DEFAULT_PORT%/docs
echo   Health Check: http://localhost:%DEFAULT_PORT%/health
echo   M3U8 Playlist: http://localhost:%DEFAULT_PORT%/playlist.m3u8
echo.
echo Useful Commands:
echo   View logs: docker-compose -f docker-compose.standalone.yml logs -f
echo   Stop app: docker-compose -f docker-compose.standalone.yml down
echo   Restart app: docker-compose -f docker-compose.standalone.yml restart
echo   Update app: git pull ^&^& docker-compose -f docker-compose.standalone.yml up -d --build
echo.
echo Configuration:
echo   Edit .env file to customize settings
echo   Data stored in Docker volumes: iptv_data, iptv_logs
echo.
echo Next Steps:
echo 1. Open http://localhost:%DEFAULT_PORT% in your browser
echo 2. Register a new user account
echo 3. Add your first IPTV playlist
echo 4. Enjoy your unified playlist!
goto :eof

REM Function to show help
:show_help
echo IPTV Playlist Manager - Windows Quick Deploy Script
echo.
echo Usage: %~nx0 [OPTIONS]
echo.
echo Options:
echo   -h, --help     Show this help message
echo   -u, --update   Update existing installation
echo   -s, --stop     Stop the application
echo   -r, --restart  Restart the application
echo   --logs         Show application logs
echo   --status       Show application status
echo.
echo Examples:
echo   %~nx0                Deploy the application
echo   %~nx0 --update       Update existing installation
echo   %~nx0 --logs         View application logs
goto :eof

REM Function to update application
:update_app
call :print_status "Updating application..."
git pull origin main
docker-compose -f docker-compose.standalone.yml down
docker-compose -f docker-compose.standalone.yml build --no-cache
docker-compose -f docker-compose.standalone.yml up -d
call :print_status "Application updated successfully!"
goto :eof

REM Function to stop application
:stop_app
call :print_status "Stopping application..."
docker-compose -f docker-compose.standalone.yml down
call :print_status "Application stopped!"
goto :eof

REM Function to restart application
:restart_app
call :print_status "Restarting application..."
docker-compose -f docker-compose.standalone.yml restart
call :print_status "Application restarted!"
goto :eof

REM Function to show logs
:show_logs
docker-compose -f docker-compose.standalone.yml logs -f
goto :eof

REM Function to show status
:show_status
docker-compose -f docker-compose.standalone.yml ps
goto :eof

REM Main deployment function
:main_deploy
call :print_header
call :check_prerequisites
call :clone_repo
call :setup_environment
call :deploy_app
call :show_deployment_info
goto :eof

REM Parse command line arguments
if "%~1"=="" goto main_deploy
if "%~1"=="-h" goto show_help
if "%~1"=="--help" goto show_help

if "%~1"=="-u" goto handle_update
if "%~1"=="--update" goto handle_update

if "%~1"=="-s" goto handle_stop
if "%~1"=="--stop" goto handle_stop

if "%~1"=="-r" goto handle_restart
if "%~1"=="--restart" goto handle_restart

if "%~1"=="--logs" goto handle_logs
if "%~1"=="--status" goto handle_status

call :print_error "Unknown option: %~1"
call :show_help
exit /b 1

:handle_update
if exist "%APP_NAME%" (
    cd /d "%APP_NAME%"
    call :update_app
) else (
    call :print_error "Application not found. Run without arguments to deploy first."
    exit /b 1
)
goto :eof

:handle_stop
if exist "%APP_NAME%" (
    cd /d "%APP_NAME%"
    call :stop_app
) else (
    call :print_error "Application not found."
    exit /b 1
)
goto :eof

:handle_restart
if exist "%APP_NAME%" (
    cd /d "%APP_NAME%"
    call :restart_app
) else (
    call :print_error "Application not found."
    exit /b 1
)
goto :eof

:handle_logs
if exist "%APP_NAME%" (
    cd /d "%APP_NAME%"
    call :show_logs
) else (
    call :print_error "Application not found."
    exit /b 1
)
goto :eof

:handle_status
if exist "%APP_NAME%" (
    cd /d "%APP_NAME%"
    call :show_status
) else (
    call :print_error "Application not found."
    exit /b 1
)
goto :eof

:main_deploy
call :print_header
call :check_prerequisites
call :clone_repo
call :setup_environment
call :deploy_app
call :show_deployment_info
