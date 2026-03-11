@echo off
REM MCP Plugin Sessions 测试执行验证脚本
echo ========================================
echo MCP Plugin Sessions 测试验证
echo ========================================
echo.
echo 预期结果: 67 passed, 7 skipped
echo.

cd /d "%~dp0source"

echo 运行测试...
echo.
python -m pytest test_mcp_plugin_sessions.py -v --tb=short

echo.
echo ========================================
echo 测试完成！
echo ========================================
echo.
echo 如果看到 "67 passed, 7 skipped" 则表示成功！
echo.
echo 查看详细报告:
echo   - Markdown: reports\TestReport_mcp_plugin_sessions.md
echo   - JSON: reports\TestReport_mcp_plugin_sessions.json
echo.
pause

