"""テストパス検証スクリプト"""
import sys
from pathlib import Path

print("=" * 60)
print("路径验证")
print("=" * 60)

# 現在のファイル位置
current = Path(__file__).resolve()
print(f"\n当前文件: {current}")

# プロジェクトルートディレクトリを計算する
# source -> mcp_plugin_router -> mcp -> plugins -> TestReport -> python_ai_cspm -> platform_python_backend-testing
project_root = current.parent.parent.parent.parent.parent.parent / "platform_python_backend-testing"
print(f"\n项目根目录: {project_root}")
print(f"存在: {project_root.exists()}")

if project_root.exists():
    app_dir = project_root / "app"
    print(f"\napp目录: {app_dir}")
    print(f"存在: {app_dir.exists()}")

    if app_dir.exists():
        mcp_plugin = app_dir / "mcp_plugin"
        print(f"\nmcp_plugin目录: {mcp_plugin}")
        print(f"存在: {mcp_plugin.exists()}")

        router_py = mcp_plugin / "router.py"
        print(f"\nrouter.py: {router_py}")
        print(f"存在: {router_py.exists()}")

# 試してsys.pathに追加してインポートする
sys.path.insert(0, str(project_root))
print(f"\nsys.path已添加: {project_root}")

try:
    from app.mcp_plugin.router import router
    print("\n✅ 导入成功!")
except ImportError as e:
    print(f"\n❌ 导入失败: {e}")

