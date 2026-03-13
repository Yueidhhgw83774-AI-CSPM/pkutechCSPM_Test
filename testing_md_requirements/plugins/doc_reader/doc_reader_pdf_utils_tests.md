# doc_reader_plugin/pdf_utils テストケース

## 1. 概要

`pdf_utils.py`は、PDF文書の操作・解析を担当するユーティリティモジュールです。pikepdfとpdfplumberを使用してPDFのバイナリ変換、言語検出、ページ番号検索、ページ範囲解析、ページ抽出を提供します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `get_binary` | pikepdf.Pdfをバイナリ（bytes）に変換 |
| `get_lang_code` | PDFの中間ページからテキストを抽出し言語を検出 |
| `find_first_page` | PDF内でページ番号が最初に現れるページを特定 |
| `parse_page_ranges` | "1-4, 8, 10"形式の文字列をページ番号リストに変換 |
| `extract_selected_page` | 指定されたページを抽出して新しいPDFを生成 |
| `extract_selected_to_end_page` | 開始ページから最終ページまでを抽出 |

### 1.2 カバレッジ目標: 90%

> **注記**: このモジュールは`ai_pretreatment.py`の主要依存であり、PDF処理の基盤を提供します。外部ライブラリ（pikepdf、pdfplumber、langdetect）への依存が多いため、全てモック化が必須です。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/doc_reader_plugin/pdf_utils.py` |
| テストコード | `test/unit/doc_reader_plugin/test_pdf_utils.py` |
| 依存: pikepdf | PDF操作ライブラリ |
| 依存: pdfplumber | PDF解析ライブラリ |
| 依存: langdetect | 言語検出ライブラリ |

### 1.4 補足情報

#### グローバル変数・ロガー設定
- `logger` (pdf_utils.py:14): モジュール専用ロガー

#### 主要分岐
- pdf_utils.py:43-44: `get_lang_code`での総ページ数0判定
- pdf_utils.py:54-56: `get_lang_code`での抽出ページなし判定
- pdf_utils.py:67-68: `get_lang_code`でのテキスト空判定
- pdf_utils.py:70-76: `get_lang_code`でのLangDetectException処理
- pdf_utils.py:109: `find_first_page`でのフッターテキスト存在判定
- pdf_utils.py:117: `find_first_page`での30ページ上限
- pdf_utils.py:134: `parse_page_ranges`での範囲形式判定
- pdf_utils.py:137-139: `parse_page_ranges`での逆順範囲判定
- pdf_utils.py:170-172: `extract_selected_page`での空ページリスト判定
- pdf_utils.py:192-194: `extract_selected_page`での抽出ページ0件判定

#### 正規表現パターン（find_first_page）
- `^\d+$` - 数字のみ
- `-\s*\d+\s*-$` - "- 1 -" 形式
- `[pP](?:age)?\.?\s*\d+` - "P. 1", "Page 1" 形式
- `\d+\s*/\s*\d+` - "1 / 10" 形式

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| PDFU-001 | get_binary: 正常変換 | 有効なpikepdf.Pdf | bytesデータ |
| PDFU-002 | get_lang_code: 日本語PDF検出 | 日本語テキストPDF | "ja" |
| PDFU-003 | get_lang_code: 英語PDF検出 | 英語テキストPDF | "en" |
| PDFU-004 | get_lang_code: 0ページPDF | 空のPDF | "unknown" |
| PDFU-005 | get_lang_code: テキストなしPDF | テキスト抽出不可PDF | "en" |
| PDFU-006 | get_lang_code: 500文字超で早期終了 | 長いテキストPDF | 言語コード（早期終了） |
| PDFU-007 | get_lang_code: カスタムpages_to_check | pages_to_check=5 | 言語コード |
| PDFU-008 | get_lang_code: ページ数 < pages_to_check | 2ページPDF, pages_to_check=5 | 全ページ処理 |
| PDFU-009 | find_first_page: 数字のみパターン | フッターに"1" | ページ番号 |
| PDFU-010 | find_first_page: ダッシュパターン | フッターに"- 1 -" | ページ番号 |
| PDFU-011 | find_first_page: Pageパターン | フッターに"Page 1" | ページ番号 |
| PDFU-012 | find_first_page: スラッシュパターン | フッターに"1 / 10" | ページ番号 |
| PDFU-013 | find_first_page: 見つからない場合 | ページ番号なしPDF | 1 |
| PDFU-014 | find_first_page: 30ページ上限 | 31ページ以上PDF | 30ページまで検索 |
| PDFU-015 | parse_page_ranges: 単一ページ | "5" | [5] |
| PDFU-016 | parse_page_ranges: 範囲指定 | "1-4" | [1, 2, 3, 4] |
| PDFU-017 | parse_page_ranges: 複合指定 | "1-4, 8, 10" | [1, 2, 3, 4, 8, 10] |
| PDFU-018 | parse_page_ranges: 重複除去・ソート | "5, 3, 5, 1" | [1, 3, 5] |
| PDFU-019 | extract_selected_page: 正常抽出 | 有効なPDF, "1-3" | 3ページのPDF |
| PDFU-020 | extract_selected_page: 範囲外ページスキップ | 5ページPDF, "1, 10" | 1ページのPDF |
| PDFU-021 | extract_selected_to_end_page: 正常抽出 | 10ページPDF, start=5 | 6ページのPDF |
| PDFU-022 | find_first_page: フッターテキストなし | フッターがNone/空 | 次ページへ進む |
| PDFU-023 | get_lang_code: 500文字境界値 | 499/500/501文字テキスト | 正確な閾値動作 |
| PDFU-024 | extract_selected_page: ページ番号境界値 | 0, 1, max, max+1 | 境界値での正確な動作 |

### 2.1 get_binary テスト

```python
# test/unit/doc_reader_plugin/test_pdf_utils.py
import pytest
import io
from unittest.mock import patch, MagicMock


class TestGetBinary:
    """get_binary関数のテスト

    NOTE: このクラスはフィクスチャを使用しません（MagicMockを直接作成）。
    """

    def test_get_binary_success(self):
        """PDFU-001: 正常変換"""
        # Arrange
        from app.doc_reader_plugin.pdf_utils import get_binary
        mock_pdf = MagicMock()
        expected_bytes = b"mock_pdf_content"

        def mock_save(stream):
            stream.write(expected_bytes)

        mock_pdf.save.side_effect = mock_save

        # Act
        result = get_binary(mock_pdf)

        # Assert
        assert isinstance(result, bytes)
        assert result == expected_bytes
        mock_pdf.save.assert_called_once()
```

### 2.2 get_lang_code テスト

```python
from langdetect import LangDetectException


class TestGetLangCode:
    """get_lang_code関数のテスト

    NOTE: このクラスで使用する mock_pdf_with_pages フィクスチャは
    conftest.py に定義してください（セクション5参照）。
    以下のフィクスチャ定義は仕様説明用のインライン例示です。
    """

    # NOTE: 以下のフィクスチャはconftest.pyに移動してください
    # @pytest.fixture
    # def mock_pdf_with_pages(self):
    #     """ページを持つPDFモック（→ conftest.py に一元化）"""
    #     ...（セクション5の共通フィクスチャ定義を参照）

    def test_detect_japanese(self, mock_pdf_with_pages):
        """PDFU-002: 日本語PDF検出"""
        # Arrange
        from app.doc_reader_plugin.pdf_utils import get_lang_code
        japanese_text = "これは日本語のテストテキストです。" * 20
        mock_pdf = mock_pdf_with_pages([japanese_text] * 5)

        with patch("app.doc_reader_plugin.pdf_utils.detect") as mock_detect:
            mock_detect.return_value = "ja"

            # Act
            result = get_lang_code(mock_pdf)

            # Assert
            assert result == "ja"
            mock_detect.assert_called_once()

    def test_detect_english(self, mock_pdf_with_pages):
        """PDFU-003: 英語PDF検出"""
        # Arrange
        from app.doc_reader_plugin.pdf_utils import get_lang_code
        english_text = "This is an English test text for language detection." * 20
        mock_pdf = mock_pdf_with_pages([english_text] * 5)

        with patch("app.doc_reader_plugin.pdf_utils.detect") as mock_detect:
            mock_detect.return_value = "en"

            # Act
            result = get_lang_code(mock_pdf)

            # Assert
            assert result == "en"

    def test_zero_pages_returns_unknown(self):
        """PDFU-004: 0ページPDF

        pdf_utils.py:43-44 の条件分岐をカバー
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import get_lang_code
        mock_pdf = MagicMock()
        mock_pdf.pages = []

        # Act
        result = get_lang_code(mock_pdf)

        # Assert
        assert result == "unknown"

    def test_no_text_returns_en(self, mock_pdf_with_pages):
        """PDFU-005: テキストなしPDF

        pdf_utils.py:67-68 の条件分岐をカバー
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import get_lang_code
        mock_pdf = mock_pdf_with_pages([None, None, None])

        # Act
        result = get_lang_code(mock_pdf)

        # Assert
        assert result == "en"

    def test_early_exit_on_500_chars(self, mock_pdf_with_pages):
        """PDFU-006: 500文字超で早期終了

        pdf_utils.py:64-65 の条件分岐をカバー
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import get_lang_code
        long_text = "A" * 600  # 500文字超
        mock_pdf = mock_pdf_with_pages([long_text, "Second page", "Third page"])

        # 各ページのextract_textを明示的にMagicMockとして設定
        # （assert_not_calledを正しく動作させるため）
        for i in range(1, 3):  # 2ページ目と3ページ目
            mock_pdf.pages[i].extract_text = MagicMock(return_value=["Second page", "Third page"][i-1])

        with patch("app.doc_reader_plugin.pdf_utils.detect") as mock_detect:
            mock_detect.return_value = "en"

            # Act
            result = get_lang_code(mock_pdf)

            # Assert
            # 最初のページで500文字超えるので、2, 3ページ目は処理されない
            assert mock_pdf.pages[0].extract_text.call_count == 1
            # 2, 3ページ目のextract_textは呼ばれていない
            assert mock_pdf.pages[1].extract_text.call_count == 0
            assert mock_pdf.pages[2].extract_text.call_count == 0
            # 早期終了後もdetectは呼ばれる
            mock_detect.assert_called_once()

    def test_custom_pages_to_check(self, mock_pdf_with_pages):
        """PDFU-007: カスタムpages_to_check"""
        # Arrange
        from app.doc_reader_plugin.pdf_utils import get_lang_code
        mock_pdf = mock_pdf_with_pages(["Text"] * 10)

        with patch("app.doc_reader_plugin.pdf_utils.detect") as mock_detect:
            mock_detect.return_value = "en"

            # Act
            result = get_lang_code(mock_pdf, pages_to_check=5)

            # Assert
            assert result == "en"

    def test_fewer_pages_than_pages_to_check(self, mock_pdf_with_pages):
        """PDFU-008: ページ数 < pages_to_check（中間抽出の境界条件）

        pdf_utils.py:52の中間ページ抽出ロジックをテスト。
        2ページのPDFでpages_to_check=5の場合:
        - middle_start_index = max(0, 2 // 2 - 5 // 2) = max(0, 1 - 2) = 0
        - pages_to_process = pdf.pages[0:5] → 実際には[0:2]が返される（2ページ全て）

        NOTE: pdf_utils.py:54-56の分岐（if not pages_to_process）は、
        実際には到達不可能なコード（フェイルセーフ）。削除を推奨。
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import get_lang_code
        # 2ページのみで、pages_to_check=5の場合
        mock_pdf = mock_pdf_with_pages(["Text page 1", "Text page 2"])

        with patch("app.doc_reader_plugin.pdf_utils.detect") as mock_detect:
            mock_detect.return_value = "en"

            # Act
            result = get_lang_code(mock_pdf, pages_to_check=5)

            # Assert
            assert result == "en"
            # スライス[0:5]は2ページ全てを返すので、両方処理される
            assert mock_pdf.pages[0].extract_text.called
            assert mock_pdf.pages[1].extract_text.called

    @pytest.mark.parametrize("text_length,should_continue_to_next", [
        (499, True),   # 500文字未満: 次ページへ進む
        (500, True),   # 丁度500文字: 次ページへ進む（条件は > 500）
        (501, False),  # 500文字超: 早期終了
    ])
    def test_text_length_boundary_for_lang_detection(self, mock_pdf_with_pages, text_length, should_continue_to_next):
        """PDFU-023: get_lang_code 500文字境界値

        pdf_utils.py:64-65 の境界値動作を検証。
        条件: if len(text) > 500
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import get_lang_code
        text = "A" * text_length
        mock_pdf = mock_pdf_with_pages([text, "Second page text"])

        with patch("app.doc_reader_plugin.pdf_utils.detect") as mock_detect:
            mock_detect.return_value = "en"

            # Act
            result = get_lang_code(mock_pdf)

            # Assert
            assert result == "en"
            if should_continue_to_next:
                # 次ページへ進む場合、2ページ目も処理される
                assert mock_pdf.pages[1].extract_text.called
            else:
                # 早期終了の場合、2ページ目は処理されない
                mock_pdf.pages[1].extract_text.assert_not_called()
```

### 2.3 find_first_page テスト

```python
class TestFindFirstPage:
    """find_first_page関数のテスト

    NOTE: このクラスで使用する mock_pdf_with_footer フィクスチャは
    conftest.py に定義してください（セクション5参照）。
    """

    # NOTE: 以下のフィクスチャはconftest.pyに移動してください
    # @pytest.fixture
    # def mock_pdf_with_footer(self):
    #     """フッター付きPDFモック（→ conftest.py に一元化）"""
    #     ...（セクション5の共通フィクスチャ定義を参照）

    def test_find_numeric_only_pattern(self, mock_pdf_with_footer):
        """PDFU-009: 数字のみパターン"""
        # Arrange
        from app.doc_reader_plugin.pdf_utils import find_first_page
        mock_pdf = mock_pdf_with_footer([None, "1", "2"])

        # Act
        result = find_first_page(mock_pdf)

        # Assert
        assert result == 2  # 2番目のページで"1"が見つかる

    def test_find_dash_pattern(self, mock_pdf_with_footer):
        """PDFU-010: ダッシュパターン"""
        # Arrange
        from app.doc_reader_plugin.pdf_utils import find_first_page
        mock_pdf = mock_pdf_with_footer([None, "- 1 -", "- 2 -"])

        # Act
        result = find_first_page(mock_pdf)

        # Assert
        assert result == 2

    def test_find_page_pattern(self, mock_pdf_with_footer):
        """PDFU-011: Pageパターン"""
        # Arrange
        from app.doc_reader_plugin.pdf_utils import find_first_page
        mock_pdf = mock_pdf_with_footer([None, "Page 1", "Page 2"])

        # Act
        result = find_first_page(mock_pdf)

        # Assert
        assert result == 2

    def test_find_slash_pattern(self, mock_pdf_with_footer):
        """PDFU-012: スラッシュパターン"""
        # Arrange
        from app.doc_reader_plugin.pdf_utils import find_first_page
        mock_pdf = mock_pdf_with_footer([None, "1 / 10", "2 / 10"])

        # Act
        result = find_first_page(mock_pdf)

        # Assert
        assert result == 2

    def test_not_found_returns_one(self, mock_pdf_with_footer):
        """PDFU-013: 見つからない場合

        pdf_utils.py:123-124 の分岐をカバー
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import find_first_page
        mock_pdf = mock_pdf_with_footer([None, None, None])

        # Act
        result = find_first_page(mock_pdf)

        # Assert
        assert result == 1

    def test_30_page_limit(self, mock_pdf_with_footer):
        """PDFU-014: 30ページ上限

        pdf_utils.py:117-118 の条件分岐をカバー
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import find_first_page
        # 35ページ、31ページ目以降にページ番号
        footer_texts = [None] * 30 + ["31", "32", "33", "34", "35"]
        mock_pdf = mock_pdf_with_footer(footer_texts)

        # Act
        result = find_first_page(mock_pdf)

        # Assert
        # 30ページまでしか検索しないので見つからない
        assert result == 1

    def test_footer_text_none_or_empty(self, mock_pdf_with_footer):
        """PDFU-022: フッターテキストなし

        pdf_utils.py:109 の条件分岐（if footer_text: がFalse）をカバー。
        フッターテキストがNoneまたは空文字列の場合、次のページへ進む。
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import find_first_page
        # 1ページ目: None, 2ページ目: 空文字列, 3ページ目: ページ番号あり
        mock_pdf = mock_pdf_with_footer([None, "", "1"])

        # Act
        result = find_first_page(mock_pdf)

        # Assert
        # 3ページ目で"1"が見つかる
        assert result == 3
```

### 2.4 parse_page_ranges テスト

```python
class TestParsePageRanges:
    """parse_page_ranges関数のテスト

    NOTE: このクラスはフィクスチャを使用しません（純粋な関数テスト）。
    """

    def test_single_page(self):
        """PDFU-015: 単一ページ"""
        # Arrange
        from app.doc_reader_plugin.pdf_utils import parse_page_ranges

        # Act
        result = parse_page_ranges("5")

        # Assert
        assert result == [5]

    def test_range(self):
        """PDFU-016: 範囲指定"""
        # Arrange
        from app.doc_reader_plugin.pdf_utils import parse_page_ranges

        # Act
        result = parse_page_ranges("1-4")

        # Assert
        assert result == [1, 2, 3, 4]

    def test_combined(self):
        """PDFU-017: 複合指定"""
        # Arrange
        from app.doc_reader_plugin.pdf_utils import parse_page_ranges

        # Act
        result = parse_page_ranges("1-4, 8, 10")

        # Assert
        assert result == [1, 2, 3, 4, 8, 10]

    def test_dedup_and_sort(self):
        """PDFU-018: 重複除去・ソート"""
        # Arrange
        from app.doc_reader_plugin.pdf_utils import parse_page_ranges

        # Act
        result = parse_page_ranges("5, 3, 5, 1")

        # Assert
        assert result == [1, 3, 5]
```

### 2.5 extract_selected_page テスト

```python
class TestExtractSelectedPage:
    """extract_selected_page関数のテスト

    NOTE: このクラスで使用する mock_pikepdf フィクスチャは
    conftest.py に定義してください（セクション5参照）。
    """

    # NOTE: 以下のフィクスチャはconftest.pyに移動してください
    # @pytest.fixture
    # def mock_pikepdf(self):
    #     """pikepdfモック（→ conftest.py に一元化）"""
    #     ...（セクション5の共通フィクスチャ定義を参照）

    def test_extract_success(self, mock_pikepdf):
        """PDFU-019: 正常抽出"""
        # Arrange
        from app.doc_reader_plugin.pdf_utils import extract_selected_page
        mock_pike, mock_new_pdf = mock_pikepdf

        mock_input_pdf = MagicMock()
        mock_pages = [MagicMock() for _ in range(5)]
        mock_input_pdf.pages = mock_pages

        # Act
        result = extract_selected_page(mock_input_pdf, "1-3")

        # Assert
        assert result == mock_new_pdf
        assert len(mock_new_pdf.added_pages) == 3  # フィクスチャの追跡用属性を使用

    def test_skip_out_of_range(self, mock_pikepdf):
        """PDFU-020: 範囲外ページスキップ

        pdf_utils.py:189-190 の条件分岐をカバー
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import extract_selected_page
        mock_pike, mock_new_pdf = mock_pikepdf

        mock_input_pdf = MagicMock()
        mock_pages = [MagicMock() for _ in range(5)]
        mock_input_pdf.pages = mock_pages

        # Act
        result = extract_selected_page(mock_input_pdf, "1, 10")  # 10は範囲外

        # Assert
        assert len(mock_new_pdf.added_pages) == 1  # 1のみ追加（フィクスチャの追跡用属性を使用）

    @pytest.mark.parametrize("page_input,pdf_pages,expected_added", [
        ("0", 10, 0),           # 0ページ（無効）
        ("1", 10, 1),           # 最小ページ（有効）
        ("10", 10, 1),          # 最大ページ（有効）
        ("11", 10, 0),          # 最大ページ+1（範囲外）
    ])
    def test_page_boundary_values(self, mock_pikepdf, page_input, pdf_pages, expected_added):
        """PDFU-024: extract_selected_page ページ番号境界値

        ページ番号の境界値（0, 1, max, max+1）での動作を検証。
        pdf_utils.py:185-190 の条件分岐をカバー。
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import extract_selected_page
        mock_pike, mock_new_pdf = mock_pikepdf
        # 各テスト実行前にadded_pagesをクリア（parametrize対応）
        mock_new_pdf.added_pages.clear()

        mock_input_pdf = MagicMock()
        mock_pages = [MagicMock() for _ in range(pdf_pages)]
        mock_input_pdf.pages = mock_pages

        # Act
        result = extract_selected_page(mock_input_pdf, page_input)

        # Assert
        assert len(mock_new_pdf.added_pages) == expected_added, \
            f"入力'{page_input}'で{expected_added}ページ追加されるべきところ、{len(mock_new_pdf.added_pages)}ページ追加されました"


class TestExtractSelectedToEndPage:
    """extract_selected_to_end_page関数のテスト

    NOTE: このクラスはextract_selected_pageをモック化するため、
    フィクスチャを使用しません。
    """

    def test_extract_to_end_success(self):
        """PDFU-021: 正常抽出"""
        # Arrange
        from app.doc_reader_plugin.pdf_utils import extract_selected_to_end_page

        with patch("app.doc_reader_plugin.pdf_utils.extract_selected_page") as mock_extract:
            mock_result = MagicMock()
            mock_extract.return_value = mock_result

            mock_input_pdf = MagicMock()
            mock_input_pdf.pages = [MagicMock() for _ in range(10)]

            # Act
            result = extract_selected_to_end_page(mock_input_pdf, 5)

            # Assert
            assert result == mock_result
            mock_extract.assert_called_once_with(mock_input_pdf, "5-10")
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| PDFU-E01 | get_lang_code: LangDetectException | 言語検出失敗 | "en"（デフォルト） |
| PDFU-E02 | find_first_page: 例外発生 | bbox抽出で例外 | 1（デフォルト） |
| PDFU-E03 | parse_page_ranges: 不正範囲（開始 > 終了） | "4-1" | [] |
| PDFU-E04 | parse_page_ranges: 不正範囲形式 | "a-b" | [] |
| PDFU-E05 | parse_page_ranges: 不正ページ番号（0以下） | "0" | [] |
| PDFU-E06 | parse_page_ranges: 不正ページ形式 | "abc" | [] |
| PDFU-E07 | extract_selected_page: 空ページリスト | "" | None |
| PDFU-E08 | extract_selected_page: 全ページ範囲外 | 5ページPDF, "10-15" | None |
| PDFU-E09 | extract_selected_page: PasswordError | パスワード保護PDF | None |
| PDFU-E10 | extract_selected_page: FileNotFoundError | 存在しないファイル | None |
| PDFU-E11 | extract_selected_page: その他例外 | 不明なエラー | None |

### 3.1 異常系テスト

```python
class TestGetLangCodeErrors:
    """get_lang_code関数のエラーハンドリングテスト

    NOTE: このクラスはフィクスチャを使用しません（MagicMockを直接作成）。
    """

    def test_lang_detect_exception(self):
        """PDFU-E01: LangDetectException

        pdf_utils.py:74-76 の例外処理をカバー
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import get_lang_code

        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Some text"
        mock_pdf.pages = [mock_page]

        with patch("app.doc_reader_plugin.pdf_utils.detect") as mock_detect:
            mock_detect.side_effect = LangDetectException("Detection failed")

            # Act
            result = get_lang_code(mock_pdf)

            # Assert
            assert result == "en"


class TestFindFirstPageErrors:
    """find_first_page関数のエラーハンドリングテスト

    NOTE: このクラスはフィクスチャを使用しません（MagicMockを直接作成）。
    """

    def test_exception_returns_one(self):
        """PDFU-E02: 例外発生時は1を返す

        pdf_utils.py:119-121 の例外処理をカバー
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import find_first_page

        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.within_bbox.side_effect = Exception("Extraction error")
        mock_pdf.pages = [mock_page]

        # Act
        result = find_first_page(mock_pdf)

        # Assert
        assert result == 1


class TestParsePageRangesErrors:
    """parse_page_ranges関数のエラーハンドリングテスト

    NOTE: このクラスはフィクスチャを使用しません（純粋な関数テスト）。
    """

    def test_invalid_range_start_greater_than_end(self):
        """PDFU-E03: 不正範囲（開始 > 終了）

        pdf_utils.py:137-139 の条件分岐をカバー
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import parse_page_ranges

        # Act
        result = parse_page_ranges("4-1")

        # Assert
        assert result == []

    def test_invalid_range_format(self):
        """PDFU-E04: 不正範囲形式

        pdf_utils.py:141-142 の例外処理をカバー
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import parse_page_ranges

        # Act
        result = parse_page_ranges("a-b")

        # Assert
        assert result == []

    def test_invalid_page_number_zero_or_negative(self):
        """PDFU-E05: 不正ページ番号（0以下）

        pdf_utils.py:146-148 の条件分岐をカバー
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import parse_page_ranges

        # Act
        result = parse_page_ranges("0")

        # Assert
        assert result == []

    def test_invalid_page_format(self):
        """PDFU-E06: 不正ページ形式

        pdf_utils.py:150-151 の例外処理をカバー
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import parse_page_ranges

        # Act
        result = parse_page_ranges("abc")

        # Assert
        assert result == []


class TestExtractSelectedPageErrors:
    """extract_selected_page関数のエラーハンドリングテスト

    NOTE: このクラスで使用する mock_pikepdf フィクスチャは
    conftest.py に定義してください（セクション5参照）。
    """

    # NOTE: 以下のフィクスチャはconftest.pyに移動してください
    # @pytest.fixture
    # def mock_pikepdf(self):
    #     """pikepdfモック（→ conftest.py に一元化）"""
    #     ...（セクション5の共通フィクスチャ定義を参照）

    def test_empty_page_list(self, mock_pikepdf):
        """PDFU-E07: 空ページリスト

        pdf_utils.py:170-172 の条件分岐をカバー
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import extract_selected_page
        mock_pike, _ = mock_pikepdf

        mock_input_pdf = MagicMock()
        mock_input_pdf.pages = [MagicMock() for _ in range(5)]

        # Act
        result = extract_selected_page(mock_input_pdf, "")

        # Assert
        assert result is None

    def test_all_pages_out_of_range(self, mock_pikepdf):
        """PDFU-E08: 全ページ範囲外

        pdf_utils.py:192-194 の条件分岐をカバー
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import extract_selected_page
        mock_pike, mock_new_pdf = mock_pikepdf

        mock_input_pdf = MagicMock()
        mock_input_pdf.pages = [MagicMock() for _ in range(5)]

        # Act
        result = extract_selected_page(mock_input_pdf, "10-15")

        # Assert
        assert result is None
        # フィクスチャの追跡用属性で、appendが呼ばれていないことを確認
        assert len(mock_new_pdf.added_pages) == 0

    def test_password_error(self, mock_pikepdf):
        """PDFU-E09: PasswordError

        pdf_utils.py:199-200 の例外処理をカバー
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import extract_selected_page
        mock_pike, _ = mock_pikepdf

        # pikepdf.errors.PasswordErrorを先に設定してからside_effectで使用
        mock_pike.errors.PasswordError = type("PasswordError", (Exception,), {})

        mock_input_pdf = MagicMock()
        mock_input_pdf.pages.__len__ = MagicMock(
            side_effect=mock_pike.errors.PasswordError("Password required")
        )

        # Act
        result = extract_selected_page(mock_input_pdf, "1")

        # Assert
        assert result is None

    def test_file_not_found_error(self, mock_pikepdf):
        """PDFU-E10: FileNotFoundError

        pdf_utils.py:201-202 の例外処理をカバー
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import extract_selected_page
        mock_pike, _ = mock_pikepdf

        mock_input_pdf = MagicMock()
        mock_input_pdf.pages.__len__ = MagicMock(side_effect=FileNotFoundError())

        # Act
        result = extract_selected_page(mock_input_pdf, "1")

        # Assert
        assert result is None

    def test_generic_exception(self, mock_pikepdf):
        """PDFU-E11: その他例外

        pdf_utils.py:203-204 の例外処理をカバー
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import extract_selected_page
        mock_pike, _ = mock_pikepdf

        mock_input_pdf = MagicMock()
        mock_input_pdf.pages.__len__ = MagicMock(side_effect=RuntimeError("Unknown error"))

        # Act
        result = extract_selected_page(mock_input_pdf, "1")

        # Assert
        assert result is None
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| PDFU-SEC-01 | ページ範囲インジェクション耐性 | `"1; rm -rf /"`, `"$(whoami)"` | int()変換失敗で空リスト。例: `"1; rm -rf /" → []` |
| PDFU-SEC-02 | 大規模ページ範囲メモリDoS耐性 [XFAIL] | `"1-10000000"` | メモリ10MB以内、処理5秒以内、または空リスト |
| PDFU-SEC-03 | エラーメッセージ情報漏洩防止 [XFAIL] | 機密情報を含む例外発生 | ログに機密情報（パスワード、パス）がマスキングされる |
| PDFU-SEC-04 | 負のページ番号インジェクション耐性 | `"-1"`, `"5, -3, 10"` | 負の値は無視。例: `"5, -3, 10" → [5, 10]` |
| PDFU-SEC-05 | 正規表現ReDoS耐性 | 大量空白/数字を含むフッター（5パターン） | 5秒以内に処理完了 |
| PDFU-SEC-06 | 依存ライブラリ脆弱性検証 | pip-auditスキャン | pikepdf≥8.0.0, pdfplumber≥0.10.0, langdetect≥1.0.9 |
| PDFU-SEC-07 | パスワード保護PDF連続処理耐性 [XFAIL] | 連続PasswordError発生 | レート制限が適用される |
| PDFU-SEC-08 | 並行処理スレッドセーフティ [XFAIL] | 10スレッド同時実行 | レースコンディションなし |

### OWASP Top 10 カバレッジ

| OWASP Category | テストID | カバー内容 |
|----------------|----------|-----------|
| A01:2021 – Broken Access Control | - | （該当なし：アクセス制御なし） |
| A02:2021 – Cryptographic Failures | - | （該当なし：暗号化処理なし） |
| A03:2021 – Injection | PDFU-SEC-01, PDFU-SEC-04, PDFU-SEC-05 | ページ範囲/負数/ReDoSインジェクション |
| A04:2021 – Insecure Design | PDFU-SEC-02, PDFU-SEC-07 | 範囲上限/レート制限の欠如 |
| A05:2021 – Security Misconfiguration | - | （該当なし：このモジュールでは設定処理なし） |
| A06:2021 – Vulnerable Components | PDFU-SEC-06 | 依存ライブラリ（pikepdf, pdfplumber, langdetect）の脆弱性検証 |
| A07:2021 – Auth Failures | - | （該当なし） |
| A08:2021 – Software/Data Integrity | - | （該当なし） |
| A09:2021 – Security Logging | PDFU-SEC-03 | 例外内容の無検証ログ出力（**実証リスク: MEDIUM**） |
| A10:2021 – SSRF | - | （該当なし） |

```python
# test/unit/doc_reader_plugin/test_pdf_utils_security.py
import pytest
import time
from unittest.mock import patch, MagicMock


@pytest.mark.security
class TestPdfUtilsSecurity:
    """pdf_utilsセキュリティテスト

    NOTE: このクラスはフィクスチャを使用しません（MagicMockを直接作成、または関数を直接テスト）。

    補足: 旧PDFU-SEC-02（パストラバーサル耐性）は削除されました。
    理由: parse_page_ranges()はファイルパス処理を一切行わないため、パストラバーサル攻撃の対象外。
    False Positive（脆弱性が存在しないのに検証する）を避けるため削除。
    """

    def test_page_range_injection_prevention(self):
        """PDFU-SEC-01: ページ範囲インジェクション耐性

        parse_page_ranges()はファイル操作やシステムコールを一切行わず、
        文字列をint()で数値変換するのみ。したがって「インジェクション」という
        用語は厳密には不正確だが、不正形式の入力が安全に処理されることを確認。

        【実装の挙動】
        1. 入力文字列をカンマ（,）で分割
        2. 各partをint()で変換し、ValueErrorなら警告ログ出力してスキップ
        3. ハイフン含む場合はsplit('-')で範囲として処理

        【このテストの目的】
        - 悪意ある入力（シェルコマンド風の文字列）が安全に拒否されることを確認
        - 実行環境に影響を与えないことを確認（実際にはint()が文字列を拒否するだけ）
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import parse_page_ranges

        # 各入力に対する具体的な期待値を定義
        # NOTE: 実装はsplit(',')でパースするため、カンマ以外の区切りは機能しない。
        # 各入力は1つのpartとして扱われ、int()でValueError→空リストになる。
        malicious_inputs_with_expected = [
            ("1; rm -rf /", []),            # "1; rm -rf /"全体がint()でValueError→[]
            ("1 && cat /etc/passwd", []),   # "1 && cat /etc/passwd"全体がValueError→[]
            ("1 | ls -la", []),             # "1 | ls -la"全体がValueError→[]
            ("$(whoami)", []),              # コマンド置換は無効、数値なし→[]
            ("`id`", []),                   # バッククォートは無効、数値なし→[]
            ("1\n2\n3", []),                # 改行を含むためint()でValueError→[]
            ("1\r\n2", []),                 # CRLFを含むためint()でValueError→[]
            # 参考: 正常なパターン
            ("1", [1]),                     # 正常な単一ページ
            ("1, 2, 3", [1, 2, 3]),         # 正常なカンマ区切り
        ]

        for malicious_input, expected in malicious_inputs_with_expected:
            # Act
            result = parse_page_ranges(malicious_input)

            # Assert
            assert result == expected, \
                f"入力'{repr(malicious_input)}'の処理結果が期待値と異なります: expected={expected}, actual={result}"
            for page in result:
                assert isinstance(page, int)
                assert page > 0

    @pytest.mark.slow  # CI実行から除外（pytest -m "not slow"）
    @pytest.mark.xfail(reason="範囲上限未実装 - parse_page_ranges()は任意の大きさの範囲を受け付けるためメモリ枯渇リスクあり")
    def test_large_page_range_memory_dos_prevention(self):
        """PDFU-SEC-02: 大規模ページ範囲メモリDoS耐性

        【実装失敗予定】pdf_utils.py:126-153 で範囲上限チェックが未実装

        極端に大きな範囲（1000万ページ）でもメモリ使用量が制限されることを確認。

        【実装改善推奨】parse_page_ranges()には範囲上限がなく、以下のリスクがある:
        - "1-10000000" → 約80MBメモリ消費
        - "1-100000000" → 約800MBメモリ消費 → サーバークラッシュ
        実装側で範囲上限（例: 10000ページ）を設定することを推奨。

        【XFAILの理由】現在の実装では範囲上限がないため、このテストは失敗が期待される。
        実装改善後にXFAILマーカーを削除すること。
        """
        import tracemalloc
        # Arrange
        from app.doc_reader_plugin.pdf_utils import parse_page_ranges

        # メモリトラッキング開始
        tracemalloc.start()

        # 攻撃的な大規模範囲（1000万ページ）
        large_range = "1-10000000"

        # Act
        start_time = time.time()
        result = parse_page_ranges(large_range)
        elapsed_time = time.time() - start_time

        # メモリ使用量取得
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Assert 1: メモリ使用量が10MB以内
        assert peak < 10 * 1024 * 1024, \
            f"メモリ使用量が{peak / (1024*1024):.2f}MBで制限を超えています（DoSリスク）"

        # Assert 2: 処理時間が5秒以内
        assert elapsed_time < 5.0, \
            f"処理に{elapsed_time:.2f}秒かかりました（DoSリスク）"

        # Assert 3: 結果が空または範囲上限以内
        assert len(result) == 0 or len(result) <= 10000, \
            f"返されたページ数が{len(result)}で範囲上限を超えています"

    @pytest.mark.xfail(reason="エラーメッセージの構造化・マスキング処理未実装 - logger.error(f'{e}')が外部ライブラリの例外メッセージをそのまま出力するため、機密情報漏洩リスクあり（実証値: MEDIUM）")
    @pytest.mark.parametrize("test_case,func_name,setup_mock", [
        ("get_lang_code", "get_lang_code", "setup_lang_detect_error"),
        ("find_first_page", "find_first_page", "setup_find_page_error"),
        ("extract_selected_page", "extract_selected_page", "setup_extract_error"),
    ])
    def test_no_sensitive_info_in_all_functions(self, test_case, func_name, setup_mock, caplog):
        """PDFU-SEC-03: エラーメッセージ情報漏洩防止

        【実装失敗予定】pdf_utils.py:75,120,200,204 でエラーメッセージがそのままログ出力される

        【検証内容】
        現在の実装では例外オブジェクトをそのまま`logger.error(f'{e}')`で出力している。
        以下のシナリオで機密情報漏洩が発生する:
        1. pikepdf.errors.PasswordError: 実際のパスワード文字列が含まれる可能性
        2. FileNotFoundError: 内部ファイルパスが含まれる
        3. LangDetectException: 処理中のテキスト断片が含まれる可能性

        【実装改善推奨】
        - 構造化ログ採用（例: `logger.error("Lang detection failed", exc_info=True)`）
        - エラーメッセージのサニタイズ処理追加
        - 機密情報を含む可能性のある例外タイプのフィルタリング

        【対象箇所】
        - pdf_utils.py:75 (get_lang_code内のLangDetectException)
        - pdf_utils.py:120 (find_first_page内のException)
        - pdf_utils.py:200 (extract_selected_page内のPasswordError)
        - pdf_utils.py:204 (extract_selected_page内のException)

        【XFAILの理由】現在の実装ではマスキング処理がないため、このテストは失敗が期待される。
        実装改善後にXFAILマーカーを削除すること。
        """
        import logging
        from langdetect import LangDetectException

        sensitive_password = "SecretPassword123"
        sensitive_path = "/etc/shadow"

        with caplog.at_level(logging.ERROR):
            if test_case == "get_lang_code":
                # Arrange: get_lang_code内のLangDetectException
                from app.doc_reader_plugin.pdf_utils import get_lang_code
                mock_pdf = MagicMock()
                mock_page = MagicMock()
                mock_page.extract_text.return_value = "Some text"
                mock_pdf.pages = [mock_page]

                with patch("app.doc_reader_plugin.pdf_utils.detect") as mock_detect:
                    mock_detect.side_effect = LangDetectException(
                        f"Error accessing {sensitive_path} with password: {sensitive_password}"
                    )
                    # Act
                    result = get_lang_code(mock_pdf)

            elif test_case == "find_first_page":
                # Arrange: find_first_page内のException
                from app.doc_reader_plugin.pdf_utils import find_first_page
                mock_pdf = MagicMock()
                mock_page = MagicMock()
                mock_page.within_bbox.side_effect = Exception(
                    f"Access denied for {sensitive_path} password: {sensitive_password}"
                )
                mock_pdf.pages = [mock_page]
                # Act
                result = find_first_page(mock_pdf)

            elif test_case == "extract_selected_page":
                # Arrange: extract_selected_page内のException
                from app.doc_reader_plugin.pdf_utils import extract_selected_page
                with patch("app.doc_reader_plugin.pdf_utils.pikepdf") as mock_pike:
                    mock_pike.Pdf.new.return_value = MagicMock()
                    mock_pike.errors.PasswordError = Exception

                    mock_input_pdf = MagicMock()
                    mock_input_pdf.pages.__len__ = MagicMock(
                        side_effect=Exception(f"Error with password: {sensitive_password}")
                    )
                    # Act
                    result = extract_selected_page(mock_input_pdf, "1")

            # Assert: 機密情報がログに含まれていないことを確認
            log_output = caplog.text
            assert sensitive_password not in log_output, \
                f"{test_case}: パスワード情報がログに出力されています。実装側でマスキング処理を追加してください。"
            assert sensitive_path not in log_output or test_case == "extract_selected_page", \
                f"{test_case}: ファイルパス情報がログに出力されています。実装側でマスキング処理を追加してください。"

    def test_negative_page_injection_prevention(self):
        """PDFU-SEC-04: 負のページ番号インジェクション耐性

        負の値を含む範囲が安全に処理されることを確認。
        具体的な期待値を定義し、実装の動作を検証する。

        【セキュリティリスク】
        - Pythonの負インデックス機能を悪用した配列逆順アクセス
        - 例: "5, -1, 10" → pdf.pages[-1]で最後のページにアクセスされるリスク
        - 実装側でpage_num-1の処理がある場合、-2になり2番目から最後のページにアクセス

        【実装の挙動】
        - ハイフンを含む場合、split('-')で分割
        - "1--5"はsplit('-')で['1', '', '5']の3要素になりValueError→空リスト
        - 負のページ番号は pdf_utils.py:146-148 で page_num <= 0 チェックにより除外される
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import parse_page_ranges

        # 各入力に対する具体的な期待値を定義
        # NOTE: "1--5"はsplit('-')で3要素になるためmap(int, ...)がValueErrorを発生
        negative_inputs_with_expected = [
            ("-1", []),               # 負の単独値は無効
            ("-10--5", []),           # 負の範囲は無効
            ("1--5", []),             # split('-')で['1','','5']の3要素→ValueError→[]
            ("-1-5", []),             # 負の開始は無効（"-1-5"は範囲として解釈不可）
            ("5, -3, 10", [5, 10]),   # 負の値のみスキップ
        ]

        for negative_input, expected in negative_inputs_with_expected:
            # Act
            result = parse_page_ranges(negative_input)

            # Assert
            assert result == expected, \
                f"入力'{negative_input}'の処理結果が期待値と異なります: expected={expected}, actual={result}"
            for page in result:
                assert page > 0

    @pytest.mark.parametrize("malicious_footer,description", [
        ("1 " + " " * 10000 + "/ 1", "大量空白（\\s*パターン）"),
        ("-" + " " * 5000 + "1" + " " * 5000 + "-", "ダッシュパターン"),
        ("Page " + "P" * 1000 + "1", "繰り返しパターン"),
        ("9" * 100000, "大量数字（^\\d+$パターン）"),
        ("1 " + " " * 5000 + "/" + " " * 5000 + " 1", "ネストした空白（\\s*/\\s*パターン）"),
    ])
    def test_footer_regex_redos_prevention(self, malicious_footer, description):
        """PDFU-SEC-05: フッター正規表現ReDoS耐性

        大量の空白や繰り返しを含むフッターテキストで、
        正規表現処理が5秒以内に完了することを確認。

        【リスク】find_first_page()でDoS攻撃が成立する可能性
        【対象】pdf_utils.py:88-94の正規表現パターン（全4パターンをテスト）:
        - r"^\\d+$" (数字のみ) → "9" * 100000 でテスト
        - r"-\\s*\\d+\\s*-$" (ダッシュパターン)
        - r"[pP](?:age)?\\.?\\s*\\d+" (Pageパターン)
        - r"\\d+\\s*/\\s*\\d+" (スラッシュパターン) → ネストした空白でテスト
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import find_first_page

        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.page_number = 1
        mock_page.height = 100
        mock_page.width = 50
        mock_within_bbox = MagicMock()
        mock_within_bbox.extract_text.return_value = malicious_footer
        mock_page.within_bbox.return_value = mock_within_bbox
        mock_pdf.pages = [mock_page]

        # Act: ReDoS攻撃パターンで処理時間を測定
        start_time = time.time()
        result = find_first_page(mock_pdf)
        elapsed_time = time.time() - start_time

        # Assert: 5秒以内に完了すること
        assert elapsed_time < 5.0, \
            f"{description}でReDoS検出: {elapsed_time:.2f}秒"

    def test_no_known_cve_in_dependencies(self):
        """PDFU-SEC-06: 依存ライブラリの既知脆弱性検証

        pip-audit等のツールで依存関係をスキャンし、
        CRITICAL/HIGHの脆弱性が存在しないことを確認。

        【対象CVE】
        - pikepdf: CVE-2022-37454（QPDF 11.1.1の整数オーバーフロー）
        - pdfplumber: CVE-2022-25238（pdfminer.six 20211012のコード実行脆弱性）
        - langdetect: 既知の脆弱性なし（2025-05時点）

        NOTE: このテストは環境依存のため、CI/CD環境でpip-auditを使用した
        自動スキャンを推奨。本テストはユニットテストとしてバージョン確認のみ行う。
        環境差異で不安定になる場合は、スキップまたは別ジョブに分離すること。

        【依存パッケージ】packagingライブラリが必要（pip install packaging）
        【最終更新】2026-02-03
        【参照】
        - https://github.com/pikepdf/pikepdf/security/advisories
        - https://github.com/pdfminer/pdfminer.six/security/advisories
        """
        import importlib.metadata
        from packaging import version  # 正確なバージョン比較に必要

        # Arrange: 最低限のセキュリティバージョンを定義
        min_secure_versions = {
            "pikepdf": "8.0.0",      # CVE-2022-37454修正（QPDF 11.1.1の脆弱性対応）
            "pdfplumber": "0.10.0",  # pdfminer.six 20221105以降（CVE-2022-25238対応）
            "langdetect": "1.0.9",   # 既知の脆弱性なし（2025-05時点）
        }

        # Act & Assert
        for package, min_version_str in min_secure_versions.items():
            try:
                installed_version_str = importlib.metadata.version(package)
                # packaging.versionを使用して正確なバージョン比較
                installed_ver = version.parse(installed_version_str)
                min_ver = version.parse(min_version_str)

                assert installed_ver >= min_ver, \
                    f"{package}のバージョン{installed_version_str}は脆弱性が報告されています。{min_version_str}以上にアップデートしてください。"
            except importlib.metadata.PackageNotFoundError:
                pytest.skip(f"{package}がインストールされていません")

    @pytest.mark.xfail(reason="レート制限未実装 - パスワード保護PDF連続処理でブルートフォース攻撃の踏み台になるリスク")
    def test_password_protected_pdf_rate_limiting(self):
        """PDFU-SEC-07: パスワード保護PDF連続処理の耐性

        【実装失敗予定】pdf_utils.py:199-200 でレート制限が未実装

        1秒以内に10回のPasswordErrorが発生した場合、
        適切なレート制限が適用されることを確認。

        【リスク】パスワード解析試行の踏み台にされる可能性
        【対象】pdf_utils.py:199-200

        【XFAILの理由】現在の実装ではレート制限がないため、このテストは失敗が期待される。
        実装改善後にXFAILマーカーを削除すること。
        """
        # Arrange
        from app.doc_reader_plugin.pdf_utils import extract_selected_page
        import time

        with patch("app.doc_reader_plugin.pdf_utils.pikepdf") as mock_pike:
            mock_pike.Pdf.new.return_value = MagicMock()
            mock_pike.errors.PasswordError = Exception

            mock_input_pdf = MagicMock()
            mock_input_pdf.pages.__len__ = MagicMock(
                side_effect=mock_pike.errors.PasswordError("Password required")
            )

            # Act: 10回連続でPasswordErrorを発生させる
            error_count = 0
            start_time = time.time()
            for _ in range(10):
                result = extract_selected_page(mock_input_pdf, "1")
                if result is None:
                    error_count += 1
            elapsed_time = time.time() - start_time

            # Assert: レート制限により、10回のエラーが1秒以上かかること
            assert elapsed_time >= 1.0, \
                f"10回のPasswordErrorが{elapsed_time:.2f}秒で処理されました。レート制限が必要です。"

    @pytest.mark.xfail(reason="スレッドセーフティ未検証 - 並行PDF処理時の競合状態リスクあり")
    def test_concurrent_pdf_processing_thread_safety(self):
        """PDFU-SEC-08: 並行処理時のスレッドセーフティ

        【実装失敗予定】pdf_utils.py:14 でグローバルなlogger使用による競合リスク

        10スレッドで同時にparse_page_ranges()を呼び出し、
        レースコンディションが発生しないことを確認。

        【リスク】
        - ログメッセージの混在
        - 予期しない例外の発生
        - グローバルなlogger使用による競合

        【XFAILの理由】現在の実装ではスレッドセーフティが未検証のため。
        実装スコープ外の機能であり、並行処理が必要な場合は別途検討すること。
        """
        import concurrent.futures
        from app.doc_reader_plugin.pdf_utils import parse_page_ranges

        # Arrange
        inputs = [f"1-{i*100}" for i in range(1, 11)]
        results = []
        errors = []

        def process_range(page_range):
            try:
                return parse_page_ranges(page_range)
            except Exception as e:
                return e

        # Act: 10スレッドで同時実行
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(process_range, inp) for inp in inputs]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if isinstance(result, Exception):
                    errors.append(result)
                else:
                    results.append(result)

        # Assert: エラーが発生していないこと
        assert len(errors) == 0, f"並行処理中にエラーが発生しました: {errors}"
        assert len(results) == 10, f"全ての処理が完了していません: {len(results)}/10"
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_pdf_utils_module` | テスト間のモジュール状態リセット（必要な場合のみ） | function | No |
| `mock_pdf_with_pages` | ページを持つPDFモック | function | No |
| `mock_pdf_with_footer` | フッター付きPDFモック | function | No |
| `mock_pikepdf` | pikepdfライブラリのモック | function | No |

> **NOTE**: `reset_pdf_utils_module`は`autouse=False`に変更されました。
> pdf_utils.pyには状態を持つグローバル変数がほとんどないため、全テストでの強制リセットは過剰です。
> 実際にモジュール状態のリセットが必要なテストケースでのみ明示的に使用してください。

### 共通フィクスチャ定義

```python
# test/unit/doc_reader_plugin/conftest.py
import sys
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def reset_pdf_utils_module():
    """テストごとにモジュールのグローバル状態をリセット（必要な場合のみ使用）

    ロガー設定やグローバル変数の影響を排除するため、
    テスト後にモジュールをsys.modulesから削除します。

    NOTE: pdf_utils.pyには状態を持つグローバル変数がほとんどないため、
    autouse=Trueは過剰。実際にモジュール状態のリセットが必要なテスト
    （例: ロガーハンドラの検証）でのみ明示的に使用すること。
    並列テスト実行時の競合を避けるため、autouse=Falseに変更。
    """
    yield

    # テスト後にクリーンアップ
    modules_to_remove = [
        key for key in sys.modules
        if key.startswith("app.doc_reader_plugin")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def mock_pdf_with_pages():
    """ページを持つPDFモック（pdfplumber用）"""
    def create_mock_pdf(pages_text_list):
        mock_pdf = MagicMock()
        mock_pages = []
        for text in pages_text_list:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = text
            mock_pages.append(mock_page)
        mock_pdf.pages = mock_pages
        return mock_pdf
    return create_mock_pdf


@pytest.fixture
def mock_pdf_with_footer():
    """フッター付きPDFモック（pdfplumber用）"""
    def create_mock_pdf(footer_texts):
        mock_pdf = MagicMock()
        mock_pages = []
        for i, footer_text in enumerate(footer_texts):
            mock_page = MagicMock()
            mock_page.page_number = i + 1
            mock_page.height = 100
            mock_page.width = 50
            mock_within_bbox = MagicMock()
            mock_within_bbox.extract_text.return_value = footer_text
            mock_page.within_bbox.return_value = mock_within_bbox
            mock_pages.append(mock_page)
        mock_pdf.pages = mock_pages
        return mock_pdf
    return create_mock_pdf


@pytest.fixture
def mock_pikepdf():
    """pikepdfライブラリのモック（ページ追加追跡機能付き）"""
    with patch("app.doc_reader_plugin.pdf_utils.pikepdf") as mock_pike:
        mock_new_pdf = MagicMock()
        # pagesはMagicMockで追跡可能にする（listは属性代入不可のため）
        added_pages = []
        mock_new_pdf.pages = MagicMock()
        mock_new_pdf.pages.append = MagicMock(side_effect=lambda p: added_pages.append(p))
        mock_new_pdf.added_pages = added_pages  # 追跡用属性

        mock_pike.Pdf.new.return_value = mock_new_pdf
        mock_pike.errors.PasswordError = type("PasswordError", (Exception,), {})
        yield mock_pike, mock_new_pdf
```

---

## 6. テスト実行例

```bash
# pdf_utils関連テストのみ実行
pytest test/unit/doc_reader_plugin/test_pdf_utils.py -v

# 特定のテストクラスのみ実行
pytest test/unit/doc_reader_plugin/test_pdf_utils.py::TestParsePageRanges -v

# カバレッジ付きで実行
pytest test/unit/doc_reader_plugin/test_pdf_utils.py --cov=app.doc_reader_plugin.pdf_utils --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/doc_reader_plugin/ -m "security" -v

# エラーハンドリングテストのみ実行
pytest test/unit/doc_reader_plugin/test_pdf_utils.py -k "Error" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 24 | PDFU-001 〜 PDFU-024 |
| 異常系 | 11 | PDFU-E01 〜 PDFU-E11 |
| セキュリティ | 8 | PDFU-SEC-01 〜 PDFU-SEC-08 |
| **合計** | **43** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestGetBinary` | PDFU-001 | 1 |
| `TestGetLangCode` | PDFU-002〜PDFU-008, PDFU-023 | 8 |
| `TestFindFirstPage` | PDFU-009〜PDFU-014, PDFU-022 | 7 |
| `TestParsePageRanges` | PDFU-015〜PDFU-018 | 4 |
| `TestExtractSelectedPage` | PDFU-019〜PDFU-020, PDFU-024 | 3 |
| `TestExtractSelectedToEndPage` | PDFU-021 | 1 |
| `TestGetLangCodeErrors` | PDFU-E01 | 1 |
| `TestFindFirstPageErrors` | PDFU-E02 | 1 |
| `TestParsePageRangesErrors` | PDFU-E03〜PDFU-E06 | 4 |
| `TestExtractSelectedPageErrors` | PDFU-E07〜PDFU-E11 | 5 |
| `TestPdfUtilsSecurity` | PDFU-SEC-01〜PDFU-SEC-08 | 8 |

### 実装失敗が予想されるテスト（XFAILマーカー付き）

以下のテストは現在の実装では**意図的に失敗**することが期待されます（`@pytest.mark.xfail`マーカー付き）。
各テストのdocstringには **【実装失敗予定】** が明記されています：

| テストID | 失敗理由 | 修正方針 |
|---------|---------|---------|
| PDFU-SEC-02 | parse_page_ranges()に範囲上限がなく、大規模範囲でメモリ枯渇リスク（**CRITICAL**） | 範囲上限（例: 10000ページ）を実装に追加 |
| PDFU-SEC-03 | pdf_utils.py:75,120,200,204でエラーメッセージがそのままログ出力される（**MEDIUM**） | 構造化ログ採用またはマスキング処理を追加 |
| PDFU-SEC-07 | パスワード保護PDF連続処理でレート制限がない（**MEDIUM**） | PasswordError発生時のレート制限を実装に追加 |
| PDFU-SEC-08 | 並行処理時のスレッドセーフティが未検証（**LOW**） | スレッドセーフなロガー設計を検討 |

### 注意事項

- テスト実行には `langdetect` パッケージが必要です
- PDFU-SEC-06の実行には `packaging` パッケージが必要です（バージョン比較用）
- **CRITICAL**: `@pytest.mark.security` と `@pytest.mark.slow` マーカーを `pyproject.toml` に登録しないと、対象テストがスキップまたは警告されます。以下を必ず追加してください：
  ```toml
  [tool.pytest.ini_options]
  markers = [
      "security: セキュリティ関連テスト",
      "slow: 実行時間の長いテスト（CI除外推奨）",
  ]

  [project.optional-dependencies]
  test = [
      "pytest",
      "pytest-cov",
      "packaging",  # PDFU-SEC-06のバージョン比較に必要
  ]
  ```

  **実行例:**
  ```bash
  # 通常テスト（slowを除外）
  pytest -m "not slow"

  # セキュリティテストのみ
  pytest -m "security"

  # 全テスト（CI/CD以外）
  pytest
  ```
- pikepdf、pdfplumber、langdetectはすべてモック化し、実際の外部接続は行いません
- **重要**: フィクスチャは `conftest.py` に定義されたものを使用し、テストコード内での重複定義は避けてください。
  本ドキュメント内のテストコードでフィクスチャ定義が記載されている箇所は、説明目的のみです。
  実装時は `conftest.py` に一元化してください
- PDFU-SEC-02はメモリ消費が大きいため、CIでは `@pytest.mark.slow` を追加して通常実行から除外することを推奨

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | 実際のPDFファイル処理をテストしない | 複雑なPDF構造でのエラーは別途統合テストが必要 | モックでカバー、統合テストは別途実施 |
| 2 | langdetectの実レスポンスをテストしない | 言語検出精度は未検証 | モックで言語コードを返す |
| 3 | 大規模PDFのパフォーマンステストなし | メモリ使用量・処理時間は未検証 | 性能テストは別途実施 |
| 4 | 正規表現パターンの網羅テストが限定的 | 全パターンの組み合わせは未検証 | 主要パターンのみカバー |
| 5 | parse_page_rangesに範囲上限なし（**CRITICAL**） | "1-10000000"で約80MB消費、DoS攻撃可能 | **PDFU-SEC-02をXFAILとし、実装側で範囲上限（例: 10000）を必須化** |
| 6 | 複数箇所でログマスキング未実装（**MEDIUM**） | 例外メッセージに機密情報が含まれる場合、複数箇所から漏洩 | **PDFU-SEC-03をXFAILとし、構造化ログまたはマスキング処理を実装** |
| 7 | 依存ライブラリの脆弱性未検証（**HIGH**） | CVE-2021-29421等の既知脆弱性への露出 | **PDFU-SEC-06追加、CI/CDにpip-audit統合** |
| 8 | 正規表現ReDoS攻撃検証が限定的（**MEDIUM**） | find_first_page()でDoS攻撃が成立する可能性 | **PDFU-SEC-05追加、regex最適化検討** |
| 9 | 並行処理時の競合状態未検証（**LOW**） | マルチスレッド環境での予期しない動作 | **PDFU-SEC-08をXFAILで追加** |
| 10 | pdf_utils.py:54-56は到達不可能コード | テストカバレッジに影響なし | 実装側で削除を推奨（フェイルセーフ分岐） |

### 削除されたテストケース

| ID（旧） | 削除理由 |
|---------|---------|
| 旧PDFU-SEC-02（パストラバーサル耐性） | parse_page_ranges()はファイルパス処理を一切行わないため、パストラバーサル攻撃の対象外。False Positive（脆弱性が存在しないのに検証する）を避けるため削除。後続のIDは繰り上げ済み。 |

---

## 9. 実装側への改善推奨事項

| 優先度 | 対象箇所 | 問題 | 推奨改善策 |
|-------|---------|------|----------|
| **CRITICAL** | pdf_utils.py:126-153 | `parse_page_ranges`に範囲上限なし（DoS脆弱性） | 範囲上限（例: 10000ページ）を追加。範囲超過時はlogger.errorで警告し、空リスト返却。 |
| **HIGH** | pyproject.toml | 依存ライブラリの脆弱性管理なし | CI/CDにpip-auditを統合し、CRITICAL/HIGH脆弱性を自動検出。 |
| **MEDIUM** | pdf_utils.py:75,120,200,204 | 例外メッセージに機密情報が含まれる可能性 | 構造化ログ（`exc_info=True`）採用、またはエラーメッセージのサニタイズ処理を追加。 |
| **MEDIUM** | pdf_utils.py:199-200 | パスワード保護PDF連続処理でレート制限なし | PasswordError発生時のレート制限（例: 10回/秒）を実装。 |
| **LOW** | pdf_utils.py:54-56 | 到達不可能な分岐コード | `if not pages_to_process:`分岐は実際には発生しないため削除を推奨。 |
| **LOW** | pdf_utils.py:14 | グローバルなlogger使用 | スレッドセーフなロガー設計を検討。 |
