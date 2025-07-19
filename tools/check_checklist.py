import yaml
import sys

def main():
    with open("v6_parallel_dev_checklist.yaml", "r") as f:
        checklist = yaml.safe_load(f)
    failed = False
    for k, v in checklist.items():
        if isinstance(v, bool) and v is False:
            print(f"[FAIL] {k} is false")
            failed = True
        if k == "ast_test_coverage" and isinstance(v, int) and v < 90:
            print(f"[FAIL] ast_test_coverage < 90: {v}")
            failed = True
    if failed:
        print("Checklist 未全綠，build fail")
        sys.exit(1)
    print("Checklist 全綠，通過驗證")
    sys.exit(0)

if __name__ == "__main__":
    main() 