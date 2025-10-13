@echo off
REM Rebuild Docker image with training support

echo 🐳 Rebuilding Coaxial Recorder with ACTUAL training support...
echo.
echo ✅ What's new:
echo   - Real PyTorch Lightning training (NO MORE SIMULATION!)
echo   - MFA vs Basic training options
echo   - RTX 5060 Ti optimization (CUDA 12.1)
echo   - GPU memory management for 16GB VRAM
echo.

REM Stop existing container
echo Stopping existing container...
docker-compose --profile gpu down

REM Rebuild image
echo.
echo Building new image (this may take several minutes)...
docker-compose --profile gpu build --no-cache

REM Start container
echo.
echo Starting container...
docker-compose --profile gpu up -d

REM Wait for health check
echo.
echo Waiting for application to start...
timeout /t 10 /nobreak >nul

REM Check status
echo.
echo Checking container status...
docker ps | findstr coaxial-recorder

echo.
echo ✅ Rebuild complete!
echo.
echo 🚀 Access the application at: http://localhost:8000
echo.
echo 📊 Check GPU status:
echo   docker exec coaxial-recorder-gpu nvidia-smi
echo.
echo 🔧 View logs:
echo   docker logs -f coaxial-recorder-gpu
echo.
pause

