@echo off
chcp 65001 >nul
title ECO-SHOP - 价目表预览
cd /d "%~dp0"
echo ======================================
echo   价目表本地服务器启动中...
echo ======================================
echo.
echo 访问地址: http://localhost:8081/listino.html
echo 按 Ctrl+C 停止服务器
echo.
start "" "http://localhost:8081/listino.html"
python -m http.server 8081
