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


def run_pytest(args, timeout=15):
    import subprocess
    # 確保每個 test function 都有 15 秒 timeout
    if '--timeout=15' not in args:
        args = ['--timeout=15'] + args
    # 強制載入 pytest_timeout plugin
    cmd = [VENV_PYTHON, "-m", "pytest"] + args
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout  # 單一 pytest 子程序 timeout（可設高一點）
        )
        return result
    except subprocess.TimeoutExpired as e:
        print(f"[Timeout] pytest 執行超過 {timeout} 秒：{cmd}")
        return subprocess.CompletedProcess(cmd, returncode=1, stdout='', stderr=str(e))

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
    non_gui_result = run_pytest(non_gui_args)

    # Step 2: 執行 GUI 測試
    gui_args = ["tests/view/test_struct_view.py"]
    gui_result = run_pytest(gui_args)

    # 確保 faillog 資料夾存在
    faillog_dir = os.path.join("tests", "faillog")
    os.makedirs(faillog_dir, exist_ok=True)
    debuglog_path = os.path.join(faillog_dir, "latest_fail.log")
    if non_gui_result.returncode != 0 or gui_result.returncode != 0:
        with open(debuglog_path, "w", encoding="utf-8") as f:
            f.write("==== Non-GUI 測試 stdout ====" + "\n")
            f.write(non_gui_result.stdout or "<empty>" + "\n")
            f.write("==== Non-GUI 測試 stderr ====" + "\n")
            f.write(non_gui_result.stderr or "<empty>" + "\n")
            f.write("==== GUI 測試 stdout ====" + "\n")
            f.write(gui_result.stdout or "<empty>" + "\n")
            f.write("==== GUI 測試 stderr ====" + "\n")
            f.write(gui_result.stderr or "<empty>" + "\n")
        print(f"❌ 有測試失敗，詳細錯誤已輸出到 {debuglog_path}")
    print("\n==== 測試結果彙總 ====")
    if non_gui_result.returncode == 0 and gui_result.returncode == 0:
        print("✅ 所有測試通過")
        sys.exit(0)
    else:
        print("❌ 有測試失敗")
        sys.exit(1)

if __name__ == "__main__":
    main() 