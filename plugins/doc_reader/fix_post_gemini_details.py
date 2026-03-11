"""修复Post Gemini测试中的mock.details"""
import re

file_path = r'C:\pythonProject\python_ai_cspm\TestReport\plugins\doc_reader\doc_reader_post_gemini\source\test_doc_reader_post_gemini.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修复delay_client_error测试中的mock.details - 应该是dict而不是JSON字符串
# 查找所有的 mock_error.details = '{"error": ...}' 并改为 mock_error.details = {"error": ...}
content = re.sub(
    r'mock_error\.details = \'(\{[^\']+\})\'',
    lambda m: f'mock_error.details = {m.group(1)}',
    content
)

# 另一种可能的格式
content = re.sub(
    r'mock_error\.details = "(\{[^"]+\})"',
    lambda m: f'mock_error.details = {m.group(1)}',
    content
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Fixed mock.details in Post Gemini tests")

