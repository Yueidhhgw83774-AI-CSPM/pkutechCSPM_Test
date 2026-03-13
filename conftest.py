# -*- coding: utf-8 -*-
"""
AI-CSPM テストプロジェクト ルート conftest.py

このファイルは pytest 起動時に最初に自動読み込みされる。
プロジェクトルート（TestReport/）の .env を解析し、
SourceCodeRoot を sys.path へ追加する。
配下のすべての conftest.py・テストファイルは
os.environ["SourceCodeRoot"] を参照できる。
"""

import os
import re
import sys
from pathlib import Path

# ============================================================
# .env 読み込み：プロジェクトルートの固定パス
# ============================================================
_ROOT_DIR = Path(__file__).parent.resolve()   # = TestReport/
_ENV_FILE = _ROOT_DIR / ".env"


def _parse_env(env_path: Path) -> dict:
    """
    .env ファイルを解析してキーと値の辞書を返す。
    コメント行（#）と空行は無視する。
    """
    result = {}
    if not env_path.exists():
        return result
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*['\"]?(.*?)['\"]?\s*$", line)
        if m:
            result[m.group(1)] = m.group(2).strip()
    return result


# .env を読み込み os.environ へ反映する（既存の環境変数は上書きしない）
_env_vars = _parse_env(_ENV_FILE)
for _key, _val in _env_vars.items():
    os.environ.setdefault(_key, _val)

# ============================================================
# SourceCodeRoot を sys.path に追加する
# ============================================================
_SOURCE_CODE_ROOT = os.environ.get("SourceCodeRoot", "").strip().strip("'\"")
if _SOURCE_CODE_ROOT and _SOURCE_CODE_ROOT not in sys.path:
    sys.path.insert(0, _SOURCE_CODE_ROOT)

# ============================================================
# TestReport ルートディレクトリ自体を sys.path に追加する
# → 任意の深さのサブディレクトリから
#   `from env_loader import PROJECT_ROOT` を利用可能にする
# ============================================================
_ROOT_DIR_STR = str(_ROOT_DIR)
if _ROOT_DIR_STR not in sys.path:
    sys.path.insert(0, _ROOT_DIR_STR)

# ============================================================
# デバッグ用確認（pytest 起動時に表示）
# ============================================================
print(f"\n[RootConftest] プロジェクトルート  : {_ROOT_DIR}")
print(f"[RootConftest] .env ファイル        : {_ENV_FILE}")
print(f"[RootConftest] SourceCodeRoot       : {_SOURCE_CODE_ROOT}")
print(f"[RootConftest] sys.path[0]          : {sys.path[0] if sys.path else '(空)'}\n")

