@echo off
echo ========================================
echo   RESTART SHOPIFY 2 ETSY CONVERTER
echo ========================================
echo.

echo [1/4] Arret des processus Python et Node...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM node.exe 2>nul
timeout /t 2 /nobreak >nul

echo [2/4] Nettoyage des fichiers temporaires...
if exist "backend\__pycache__" rmdir /S /Q "backend\__pycache__"
if exist "outputs" rmdir /S /Q "outputs"
if exist "uploads" rmdir /S /Q "uploads"
mkdir outputs
mkdir uploads

echo [3/4] Demarrage du backend Python...
start "Backend Python" cmd /k "cd backend && python app.py"
timeout /t 3 /nobreak >nul

echo [4/4] Demarrage du frontend Vite...
start "Frontend Vite" cmd /k "npm run dev"

echo.
echo ========================================
echo   SERVEURS DEMARRES !
echo ========================================
echo   Backend:  http://127.0.0.1:5000
echo   Frontend: http://127.0.0.1:5173
echo ========================================
echo.
pause
