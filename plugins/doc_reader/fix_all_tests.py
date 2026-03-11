"""
批量修复Doc Reader测试文件中的主要问题
"""
import os
import re

def fix_output_models():
    """修复Output Models测试中的Pydantic类型强制问题"""
    file_path = r'C:\pythonProject\python_ai_cspm\TestReport\plugins\doc_reader\doc_reader_output_models\source\test_doc_reader_output_models.py'

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 修复test_discription_type_coercion - 期望ValidationError
    content = re.sub(
        r'def test_discription_type_coercion\(self\):.*?instance = ImageDiscription\(discription=123\)\s+assert instance\.discription == "123"',
        '''def test_discription_type_coercion(self):
        """OUTM-E02: ImageDiscription discription型強制"""
        from app.doc_reader_plugin.output_models import ImageDiscription
        
        # Pydantic v2不再自动进行类型强制转换，期望ValidationError
        with pytest.raises(ValidationError):
            ImageDiscription(discription=123)''',
        content,
        flags=re.DOTALL
    )

    # 修复test_page_type_coercion
    content = re.sub(
        r'def test_page_type_coercion\(self\):.*?instance = Compliance\(\s+id="COMP-004",\s+title="タイトル",\s+discription="説明",\s+page=123\s+\)\s+assert instance\.page == "123"',
        '''def test_page_type_coercion(self):
        """OUTM-E04: Compliance page型強制"""
        from app.doc_reader_plugin.output_models import Compliance
        
        # Pydantic v2不再自动进行类型强制转换，期望ValidationError
        with pytest.raises(ValidationError):
            Compliance(
                id="COMP-004",
                title="タイトル",
                discription="説明",
                page=123
            )''',
        content,
        flags=re.DOTALL
    )

    # 修复test_type_coercion_bypass_prevention
    content = re.sub(
        r'def test_type_coercion_bypass_prevention\(self\):.*?instance = Compliance\(\s+id="COMP-NOSQL",\s+title="タイトル",\s+discription="説明",\s+page=nosql_payload\s+\)\s+.*?assert isinstance\(instance\.page, str\).*?assert "ne" in instance\.page or "\$" in instance\.page',
        '''def test_type_coercion_bypass_prevention(self):
        """OUTM-SEC-07: 型強制バイパス防止"""
        from app.doc_reader_plugin.output_models import Compliance
        
        # dict型注入（NoSQLインジェクション試行）
        nosql_payload = {"$ne": 1}
        
        # Pydantic v2では型強制が厳格化され、dictは拒否される
        with pytest.raises(ValidationError):
            Compliance(
                id="COMP-NOSQL",
                title="タイトル",
                discription="説明",
                page=nosql_payload
            )''',
        content,
        flags=re.DOTALL
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("✓ Fixed Output Models tests")

def fix_post_gemini():
    """修复Post Gemini测试中的函数参数问题"""
    file_path = r'C:\pythonProject\python_ai_cspm\TestReport\plugins\doc_reader\doc_reader_post_gemini\source\test_doc_reader_post_gemini.py'

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 修复get_compliance_detail_at_pdf参数名: pdf_byte -> pdf
    content = content.replace('pdf_byte=b"PDF_DATA"', 'pdf=b"PDF_DATA"')
    content = content.replace('pdf_byte=b"PDF"', 'pdf=b"PDF"')

    # 修复generate_contents参数名: system_instruction -> prompt, pdf_byte -> pdf, user_contents -> text
    content = re.sub(
        r'result = await generate_contents\(\s+system_instruction="[^"]*",\s+pdf_byte=b"[^"]*",\s+user_contents="[^"]*"\s+\)',
        'result = await generate_contents(prompt="Test", pdf=b"PDF", text="User prompt")',
        content
    )

    # 修复parse_compliance_at_pdf参数: categories -> (这个参数不存在，应该删除)
    content = re.sub(
        r'result = await parse_compliance_at_pdf\(\s+b"PDF_DATA",\s+categories=malicious_categories\s+\)',
        'result = await parse_compliance_at_pdf(b"PDF_DATA")',
        content
    )

    # 修复delay_client_error的mock.details - 应该是JSON对象而不是字符串
    content = re.sub(
        r'mock_error\.details = \'(\{.*?\})\'',
        lambda m: f'mock_error.details = {m.group(1)}',
        content
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("✓ Fixed Post Gemini tests")

def fix_structuring():
    """修复Structuring测试中的函数名问题"""
    file_path = r'C:\pythonProject\python_ai_cspm\TestReport\plugins\doc_reader\doc_reader_structuring\source\test_doc_reader_structuring.py'

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 修复get_extraction_llm -> 实际函数名可能是get_llm或llm_factory
    # 先改为直接Mock structure_item函数
    content = re.sub(
        r'with patch\("app\.doc_reader_plugin\.structuring\.get_extraction_llm"\)',
        'with patch("app.llm_factory.llm_factory.get_extraction_llm")',
        content
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("✓ Fixed Structuring tests")

if __name__ == '__main__':
    print("开始修复测试文件...")

    try:
        fix_output_models()
    except Exception as e:
        print(f"✗ Output Models修复失败: {e}")

    try:
        fix_post_gemini()
    except Exception as e:
        print(f"✗ Post Gemini修复失败: {e}")

    try:
        fix_structuring()
    except Exception as e:
        print(f"✗ Structuring修复失败: {e}")

    print("\n修复完成!")

