@echo off
echo ========================================
echo  Shopify 2 Etsy - Demarrage
echo ========================================
echo.

REM Verifier si node_modules existe
if not exist "node_modules\" (
    echo Installation des dependances frontend...
    call npm install
    echo.
)

REM Verifier si les dependances Python sont installees
echo Verification des dependances Python...
pip show Flask >nul 2>&1
if errorlevel 1 (
    echo Installation des dependances Python...
    pip install -r requirements.txt
    echo.
)

REM Creer les dossiers necessaires
if not exist "uploads\" mkdir uploads
if not exist "outputs\" mkdir outputs
if not exist "backend\" mkdir backend

REM Creer le fichier .env s'il n'existe pas
if not exist ".env" (
    echo Creation du fichier .env...
    copy .env.example .env
    echo.
    echo IMPORTANT: Editez le fichier .env et ajoutez votre cle API Gemini
    echo.
)

echo ========================================
echo  Demarrage des serveurs...
echo ========================================
echo.
echo Backend Flask: http://localhost:5000
echo Frontend React: http://localhost:3000
echo.
echo Appuyez sur Ctrl+C pour arreter les serveurs
echo.

REM Demarrer le backend en arriere-plan
start "Shopify2Etsy Backend" cmd /k "python backend\app.py"

REM Attendre 3 secondes
timeout /t 3 /nobreak >nul

REM Demarrer le frontend
start "Shopify2Etsy Frontend" cmd /k "npm run dev"

echo.
echo Les serveurs sont en cours de demarrage...
echo Ouvrez http://localhost:3000 dans votre navigateur
echo.
pause
