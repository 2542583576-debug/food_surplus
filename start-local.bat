@echo off
title Food Surplus - Local Startup
cd /d "%~dp0"
echo.
echo  ================================================
echo    Food Surplus - Local One-Click Startup
echo  ================================================
echo.

REM --- Step 0: kill any stale process on service ports ---
echo  [0/5] Cleaning stale processes on ports 8000 / 5173 ...
for %%P in (8000 5173) do (
  for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%%P" ^| findstr LISTENING') do (
    echo          stopping old PID %%a on port %%P
    taskkill /PID %%a /F >NUL 2>&1
  )
)
ping -n 2 127.0.0.1 >NUL

REM --- Step 1: backend virtual environment ---
if not exist "backend\.venv\Scripts\python.exe" (
  echo  [1/5] Creating backend venv and installing dependencies...
  python -m venv backend\.venv
  call backend\.venv\Scripts\pip.exe install -r backend\requirements.txt -i https://pypi.org/simple
) else (
  echo  [1/5] Backend venv found.
)

REM --- Step 2: frontend dependencies ---
if not exist "frontend\node_modules" (
  echo  [2/5] Installing frontend dependencies...
  call npm install --prefix frontend --no-audit --no-fund
) else (
  echo  [2/5] Frontend dependencies found.
)

REM --- Step 3: initialize database ---
echo  [3/5] Initializing database ...
cd /d "%~dp0backend"
set "PYTHONPATH="
call .venv\Scripts\python.exe -c "from scripts.init_db import main; main()"
if errorlevel 1 (
  echo.
  echo  [ERROR] Database initialization failed.
  echo          Make sure MySQL is running on 127.0.0.1:3306
  echo          and the password in backend\.env is correct.
  echo.
  goto :fail
)
cd /d "%~dp0"

REM --- Step 4: start backend (PYTHONPATH inherited as empty) ---
echo  [4/5] Starting backend window on 127.0.0.1:8000 ...
start "FoodSurplus-Backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

REM --- Step 5: start frontend ---
echo  [5/5] Starting frontend window on 127.0.0.1:5173 ...
start "FoodSurplus-Frontend" cmd /k "cd /d %~dp0frontend && npm run dev -- --host 127.0.0.1"

REM --- Wait until backend responds ---
echo.
echo  Waiting for services to be ready ...
set "BACKEND_OK=0"
set "FRONTEND_OK=0"
set /a n=0
:wait_backend
curl -s -o NUL http://127.0.0.1:8000/health
if not errorlevel 1 goto backend_ready
set /a n+=1
if %n% GEQ 45 goto backend_timeout
ping -n 2 127.0.0.1 >NUL
goto wait_backend
:backend_ready
set "BACKEND_OK=1"
echo    - Backend ready  (127.0.0.1:8000)
goto check_frontend
:backend_timeout
echo    - Backend NOT ready after 45s - check the "FoodSurplus-Backend" window for errors

:check_frontend
set /a n=0
:wait_frontend
curl -s -o NUL http://127.0.0.1:5173/
if not errorlevel 1 goto frontend_ready
set /a n+=1
if %n% GEQ 45 goto frontend_timeout
ping -n 2 127.0.0.1 >NUL
goto wait_frontend
:frontend_ready
set "FRONTEND_OK=1"
echo    - Frontend ready (127.0.0.1:5173)
goto finished
:frontend_timeout
echo    - Frontend NOT ready after 45s - check the "FoodSurplus-Frontend" window for errors

:finished
echo.
echo  ================================================
if "%BACKEND_OK%"=="1" (
  echo    Startup finished!
) else (
  echo    Startup finished WITH ERRORS - backend did not start.
)
echo    Frontend : http://127.0.0.1:5173
echo    Backend  : http://127.0.0.1:8000/docs
echo    Accounts : user/user123  /  admin/admin123
echo  ================================================
echo.
echo  Opening browser tabs now ...
start http://127.0.0.1:5173
start http://127.0.0.1:8000/docs
echo.
echo  Two service windows are open: FoodSurplus-Backend and FoodSurplus-Frontend.
echo  Keep them open. Double-click stop-local.bat to stop everything.
echo  Press any key to close THIS window only ...
pause >NUL
exit /b 0

:fail
echo  Startup aborted.
echo  Press any key to exit ...
pause >NUL
exit /b 1
