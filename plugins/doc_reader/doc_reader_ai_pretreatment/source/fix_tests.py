import re

# 读取文件
with open('test_doc_reader_ai_pretreatment.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复 ai_pretreatment 调用 - 添加必需参数
# 查找所有 await ai_pretreatment(mock_pdf 的调用并添加必需参数
pattern = r'await ai_pretreatment\(mock_pdf\)'
replacement = 'await ai_pretreatment(mock_pdf, platform=["aws"], categories="[]", job_id="test-job", output_lang="ja")'
content = re.sub(pattern, replacement, content)

# 修复带参数的调用
pattern = r'await ai_pretreatment\(mock_pdf,\s*(randomer|max_output|platform|output_language)'
def fix_call(match):
    param = match.group(1)
    if param == 'randomer':
        return f'await ai_pretreatment(mock_pdf, platform=["aws"], categories="[]", job_id="test-job", output_lang="ja", randomer'
    elif param == 'max_output':
        return f'await ai_pretreatment(mock_pdf, platform=["aws"], categories="[]", job_id="test-job", output_lang="ja", max_output'
    elif param == 'platform':
        return f'await ai_pretreatment(mock_pdf, platform'
    elif param == 'output_language':
        return f'await ai_pretreatment(mock_pdf, platform=["aws"], categories="[]", job_id="test-job", output_language'
content = re.sub(pattern, fix_call, content)

# 保存修复后的文件
with open('test_doc_reader_ai_pretreatment.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed ai_pretreatment function calls")

