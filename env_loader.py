# -*- coding: utf-8 -*-
"""
env_loader.py — AI-CSPM テストプロジェクト共通 env 読み込みユーティリティ

使用方法:
    # conftest.py または test_*.py のトップに記述する
    from env_loader import PROJECT_ROOT

    # または関数として利用する
    from env_loader import get_source_code_root
    source_root = get_source_code_root()

動作の優先順位:
    1. os.environ["SourceCodeRoot"] （ルート conftest.py が設定済みの場合）
    2. ディレクトリツリーを遡って .env ファイルを自動検出する
"""

import os
import re
import sys
from pathlib import Path


# ============================================================
# ユーティリティ関数
# ============================================================

def find_env_file(start: Path = None) -> Path | None:
    """
    指定ディレクトリからルート方向へ遡り、最初に見つかった .env ファイルのパスを返す。
    見つからない場合は None を返す。

    Args:
        start: 検索開始パス。省略時はこのファイルのディレクトリ。
    """
    current = (start or Path(__file__)).resolve()
    # ファイルパスが渡された場合は親ディレクトリから開始する
    if current.is_file():
        current = current.parent
    for directory in [current, *current.parents]:
        candidate = directory / ".env"
        if candidate.exists():
            return candidate
    return None


def _read_key(env_path: Path, key: str) -> str:
    """
    .env ファイルから指定キーの値を読み込む。
    見つからない場合は空文字列を返す。
    """
    pattern = re.compile(
        r"^\s*" + re.escape(key) + r"\s*=\s*['\"]?(.+?)['\"]?\s*$"
    )
    for line in env_path.read_text(encoding="utf-8").splitlines():
        m = pattern.match(line)
        if m:
            return m.group(1).strip()
    return ""


def get_source_code_root() -> str:
    """
    SourceCodeRoot のパス文字列を取得する。

    優先順位:
      1. os.environ["SourceCodeRoot"] （ルート conftest.py が設定済み）
      2. ディレクトリツリーを遡って .env を検出し値を読み込む
    """
    # 優先度1: 環境変数（ルート conftest.py が設定済みの場合）
    from_env = os.environ.get("SourceCodeRoot", "").strip().strip("'\"")
    if from_env:
        return from_env

    # 優先度2: ディレクトリツリーを遡って .env を検索する
    env_file = find_env_file(Path(__file__))
    if env_file:
        value = _read_key(env_file, "SourceCodeRoot")
        if value:
            return value

    return ""


def get_env_value(key: str) -> str:
    """
    任意のキーを .env から取得する。
    os.environ に存在する場合はそちらを優先する。

    Args:
        key: .env のキー名
    """
    from_env = os.environ.get(key, "").strip().strip("'\"")
    if from_env:
        return from_env
    env_file = find_env_file(Path(__file__))
    if env_file:
        return _read_key(env_file, key)
    return ""


# ============================================================
# モジュールレベルで PROJECT_ROOT を解決して sys.path に追加する
# ============================================================
_project_root_str: str = get_source_code_root()
PROJECT_ROOT: Path = Path(_project_root_str) if _project_root_str else Path.cwd()

if _project_root_str and _project_root_str not in sys.path:
    sys.path.insert(0, _project_root_str)

