import subprocess
import sys
import os
# 自動設置 PYTHONPATH=src 並重啟腳本
if "PYTHONPATH" not in os.environ or "src" not in os.environ["PYTHONPATH"]:
    os.environ["PYTHONPATH"] = "src"
    os.execv(sys.executable, [sys.executable] + sys.argv)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
import unittest
import shutil

# 強制使用 .venv/bin/python
VENV_PYTHON = os.path.join(os.path.dirname(__file__), '.venv', 'bin', 'python')


def run_pytest(args, desc, use_xvfb=False):
    print(f"\n==== {desc} ====")
    cmd = [VENV_PYTHON, "-m", "pytest"] + args
    if use_xvfb:
        if shutil.which("xvfb-run") is None:
            print("[警告] headless 環境下未偵測到 xvfb-run，請安裝 Xvfb (Linux: sudo apt install xvfb, macOS: brew install xquartz)")
            print("將直接執行 pytest，可能會 skip GUI 測試...")
        else:
            cmd = ["xvfb-run", "-a"] + cmd
    result = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        return 0
    # fallback 條件
    if "No module named pytest" in (result.stderr or ""):
        print("pytest 未安裝，fallback 用 unittest 執行...")
        return run_unittest(args, desc)
    # 其他 pytest 失敗直接顯示
    print(result.stdout)
    print(result.stderr)
    return result.returncode

def iter_test_cases(suite):
    # 遞迴展開 TestSuite，產生所有 TestCase
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from iter_test_cases(test)
        else:
            yield test

def run_unittest(args, desc):
    print(f"[unittest fallback] {desc}")
    loader = unittest.TestLoader()
    suite = None
    if args and args[0].startswith('--ignore='):
        # 執行所有 tests/ 下的 test_*.py，排除指定檔案
        ignore_file = args[0].split('=')[1]
        all_suites = loader.discover('tests', pattern='test_*.py')
        filtered_tests = [tc for tc in iter_test_cases(all_suites) if ignore_file not in tc.id()]
        suite = unittest.TestSuite(filtered_tests)
    elif args and args[0].endswith('.py'):
        # 只執行指定檔案
        test_file = os.path.splitext(os.path.basename(args[0]))[0]
        suite = loader.loadTestsFromName(f"tests.{test_file}")
    else:
        suite = loader.discover('tests', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1

def main():
    # Step 1: 執行非 GUI 測試
    non_gui_args = [
        "--ignore=tests/test_struct_view.py",
        "--ignore=packing/test_executable.py",
    ]
    use_xvfb = not os.environ.get("DISPLAY")
    non_gui_result = run_pytest(
        non_gui_args,
        "Step 1: 執行非 GUI 測試",
        use_xvfb=use_xvfb,
    )

    # Step 2: 執行 GUI 測試
    gui_args = ["tests/test_struct_view.py"]
    # 若無 DISPLAY，則用 xvfb-run 包裝
    use_xvfb = not os.environ.get("DISPLAY")
    gui_result = run_pytest(gui_args, "Step 2: 執行 GUI 測試", use_xvfb=use_xvfb)

    print("\n==== 測試結果彙總 ====")
    if non_gui_result == 0 and gui_result == 0:
        print("✅ 所有測試通過")
        sys.exit(0)
    else:
        print("❌ 有測試失敗")
        sys.exit(1)

if __name__ == "__main__":
    main() 