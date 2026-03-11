@echo off
REM 运行 checkpointer 测试
cd /d C:\pythonProject\python_ai_cspm\TestReport\checkpointer\source
python simple_test.py > test_output.txt 2>&1
type test_output.txt
echo.
echo ========================================
echo 测试输出已保存到 test_output.txt
echo ========================================
