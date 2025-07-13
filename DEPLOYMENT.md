# 自動部署說明

## 概述

本專案已設定 GitHub Actions 自動部署，當您 push 程式碼到 GitHub 時，會自動建置 Windows .exe 檔案。

## 自動部署流程

### 1. 每次 Push 觸發建置
- 當您 push 程式碼到 `main` 或 `master` 分支時
- GitHub Actions 會自動在 Windows 環境中建置 .exe 檔案
- 建置結果會作為 Artifact 上傳，您可以在 Actions 頁面下載

### 2. 發布版本 (Release)
- 當您建立並 push 一個 tag (例如 `v1.0.0`) 時
- 會自動建立一個 GitHub Release
- Windows .exe 檔案會作為 Release Asset 上傳
- 使用者可以直接從 Release 頁面下載

## 使用方法

### 本地測試建置
```bash
# 安裝依賴
pip install -r requirements.txt

# 執行建置腳本
python build_exe.py
```

### 觸發自動部署

#### 方法 1: 一般建置 (Artifact)
```bash
# Push 到主分支
git add .
git commit -m "Update code"
git push origin main
```

#### 方法 2: 發布版本 (Release)
```bash
# 建立並 push tag
git tag v1.0.0
git push origin v1.0.0
```

## 檔案說明

### GitHub Actions 工作流程
- `.github/workflows/build-windows-exe.yml`: 一般建置工作流程
- `.github/workflows/release.yml`: 發布版本工作流程

### 建置配置
- `CppStructParser.spec`: PyInstaller 規格檔案
- `build_exe.py`: 本地建置腳本
- `requirements.txt`: 包含 PyInstaller 依賴

## 建置結果

### Artifact 下載
1. 前往 GitHub 專案的 Actions 頁面
2. 點擊最新的工作流程執行
3. 在 Artifacts 區域下載 `CppStructParser-Windows`

### Release 下載
1. 前往 GitHub 專案的 Releases 頁面
2. 點擊最新的 Release
3. 下載 `CppStructParser-Windows.exe`

## 注意事項

1. **建置時間**: 首次建置可能需要 5-10 分鐘
2. **檔案大小**: .exe 檔案約 20-50MB (包含 Python 運行時)
3. **相容性**: 建置的 .exe 檔案可在 Windows 7+ 上執行
4. **防毒軟體**: 某些防毒軟體可能會誤報，這是正常現象

## 故障排除

### 建置失敗
1. 檢查 Actions 頁面的錯誤訊息
2. 確認所有依賴都已正確安裝
3. 檢查程式碼是否有語法錯誤

### 本地建置問題
1. 確保已安裝 Python 3.7+
2. 安裝 PyInstaller: `pip install pyinstaller`
3. 執行 `python build_exe.py` 查看詳細錯誤訊息

## 自訂建置

如需修改建置配置，請編輯以下檔案：
- `CppStructParser.spec`: 修改 PyInstaller 設定
- `.github/workflows/*.yml`: 修改 GitHub Actions 工作流程
- `requirements.txt`: 新增或移除依賴 