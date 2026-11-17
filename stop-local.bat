@echo off
title Food Surplus - Local Stop
echo.
echo  ================================================
echo    Food Surplus - Stop Local Services
echo  ================================================
echo.

echo  Stopping services on port 8000 (backend) and 5173 (frontend) ...
echo.

set FOUND=0
for %%P in (8000 5173) do (
  for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%%P" ^| findstr LISTENING') do (
    echo    Killing PID %%a on port %%P ...
    taskkill /PID %%a /F >NUL 2>&1
    set FOUND=1
  )
)

echo.
if "%FOUND%"=="1" (
  echo  Done. Local services stopped.
) else (
  echo  No running local services found - already stopped.
)
echo.
echo  Press any key to close this window ...
pause >NUL
exit /b 0
