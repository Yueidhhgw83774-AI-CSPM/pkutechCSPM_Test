"""
StructuringテストでのMock設定の修正
ChainのMockを期望値を正しく返すようにする
"""

with open('test_doc_reader_structuring.py', 'r', encoding='utf-8') as f:
    content = f.read()

# すべてのテストでのChain Mockの修正
# 問題：Chainはprompt | llm | parserで構成されます
# 我们需要Mockこのパイプ演算子の結果を必要とする

# stratégie：直接 `structure_item_with_llm` の返り値を Mock するのではなく、内部実装を Mock します
# または、Chain全体を正しくMockする

# 簡単な方法：テストで必要なエラー状況をテストするために、直接Mock functionの返却値を設定する。

import re

# mock_chain.invokeを使用しているすべてのテストを検出し、修正する
# mock_prompt.from_template.return_value を mock_prompt.from_messages.return_value に変更してください。

content = re.sub(
    r'mock_prompt\.from_template\.return_value',
    'mock_prompt.from_messages.return_value.__or__.return_value.__or__.return_value',
    content
)

# 保存する
with open('test_doc_reader_structuring.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Fixed Chain Mock in Structuring tests")
print("  - Changed from_template to from_messages")
print("  - Fixed chain operator (__or__) mocking")

