"""
修复Structuring测试中的Mock设置
使Chain的Mock正确返回期望的值
"""

with open('test_doc_reader_structuring.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复所有测试中的Chain Mock
# 问题：Chain是通过 prompt | llm | parser 构建的
# 我们需要Mock这个管道操作符的结果

# 策略：直接Mock structure_item_with_llm的返回值，而不是Mock内部实现
# 或者正确地Mock整个Chain

# 简单方法：为所有需要测试错误情况的测试，直接Mock function返回值

import re

# 查找所有使用mock_chain.invoke的测试并修复
# 将 mock_prompt.from_template.return_value 改为 mock_prompt.from_messages.return_value

content = re.sub(
    r'mock_prompt\.from_template\.return_value',
    'mock_prompt.from_messages.return_value.__or__.return_value.__or__.return_value',
    content
)

# 保存
with open('test_doc_reader_structuring.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Fixed Chain Mock in Structuring tests")
print("  - Changed from_template to from_messages")
print("  - Fixed chain operator (__or__) mocking")

