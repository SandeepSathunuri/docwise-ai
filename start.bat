@echo off
echo Starting Advanced RAG System...
echo.

echo Checking if Ollama is running...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Ollama is not running!
    echo Please start Ollama first: ollama serve
    echo Then pull the required model: ollama pull deepseek-r1-distill-llama-70b
    pause
    exit /b 1
)

echo Ollama is running ✓
echo.

echo Starting Backend Server...
start "RAG Backend" cmd /k "cd backend && pipenv run python app.py"

echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo Starting Frontend Server...
start "RAG Frontend" cmd /k "cd frontend && npm start"

echo.
echo ========================================
echo Advanced RAG System is starting up!
echo ========================================
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Both servers will open in separate windows.
echo Close this window when you're done.
echo ========================================

pause