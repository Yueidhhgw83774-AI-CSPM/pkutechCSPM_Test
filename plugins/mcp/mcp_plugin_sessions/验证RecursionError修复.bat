@echo off
echo ========================================
echo 验证 RecursionError 修复
echo ========================================
echo.

cd /d "%~dp0source"

echo 运行有问题的测试...
python -m pytest test_mcp_plugin_sessions.py::TestSessionsRouter::test_delete_session_success test_mcp_plugin_sessions.py::TestSessionsSecurity::test_session_deletion_cleanup -v

echo.
echo 如果上面显示 2 passed，则修复成功！
echo.
pause

echo.
echo 运行完整测试套件...
python -m pytest test_mcp_plugin_sessions.py -v --tb=short

echo.
echo 期望: 67 passed, 7 skipped
echo.
pause

