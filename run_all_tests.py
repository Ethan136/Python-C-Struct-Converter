import subprocess
import sys


def run_pytest(args, desc):
    print(f"\n==== {desc} ====")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest"] + args,
            check=False
        )
        return result.returncode
    except Exception as e:
        print(f"執行 {desc} 時發生錯誤: {e}")
        return 1


def main():
    # Step 1: 執行非 GUI 測試
    non_gui_args = ["--ignore=tests/test_struct_view.py"]
    non_gui_result = run_pytest(non_gui_args, "Step 1: 執行非 GUI 測試")

    # Step 2: 執行 GUI 測試
    gui_args = ["tests/test_struct_view.py"]
    gui_result = run_pytest(gui_args, "Step 2: 執行 GUI 測試")

    print("\n==== 測試結果彙總 ====")
    if non_gui_result == 0 and gui_result == 0:
        print("✅ 所有測試通過")
        sys.exit(0)
    else:
        print("❌ 有測試失敗")
        sys.exit(1)


if __name__ == "__main__":
    main() 