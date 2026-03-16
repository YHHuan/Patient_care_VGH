# VGHTPE 查房摘要產生器 (AI)

自動抓取北榮住院病人資料，透過 Claude Sonnet 4.6 (OpenRouter) 產生結構化查房摘要。

## 功能

- 登入北榮 EMR → 依燈號/病房/病歷號搜尋病人
- **Round 1**: 自動抓取基本資料（admission note、vitals、labs、meds、imaging）
- **AI 分析**: Claude 判斷是否需要額外資料（cultures、I/O、duty notes 等）
- **Round 2+**: 針對 AI 要求的項目再次抓取（最多 3 輪）
- **產出**: 每位病人一份 Markdown 摘要 + 合併 Word 文件
- 內建防鎖機制（request 間隔 1.5-3.5 秒，病人間隔 30-60 秒）

## 在醫院電腦執行

### 方法 A：直接用 .exe（推薦）

不需要安裝 Python。從 [Releases](https://github.com/YHHuan/Patient_care_VGH/releases) 下載 `VGH_AI_Summary.exe`，雙擊即可執行。

**自行打包 .exe：**
```bash
# 在有 Python 的電腦上執行一次
pip install pyinstaller
pip install -e .
python build.py
# 產生 dist/VGH_AI_Summary.exe，複製到 USB 帶去醫院
```

### 方法 B：Portable Python（免安裝 Python）

1. 下載 [WinPython](https://winpython.github.io/)（免安裝版，約 500MB）
2. 放到 USB 隨身碟
3. 把此專案資料夾也放進 USB
4. 用 WinPython 的 terminal 執行 `pip install -e .` 再跑 `python gui.py`

### 方法 C：有 Python 的電腦

```bash
git clone https://github.com/YHHuan/Patient_care_VGH.git
cd Patient_care_VGH
pip install -e .
```

## 使用方式

### GUI（推薦）

```bash
python gui.py
# 或雙擊 VGH_AI_Summary.exe
```

1. 輸入北榮帳號密碼 + OpenRouter API Key
2. 選擇搜尋方式（燈號/病房/病歷號），輸入搜尋條件
3. 點「搜尋病人」
4. 點「產生 AI 摘要」→ 等待（每位病人約 2 分鐘）
5. 點「匯出 Word」產生 `.docx` 檔案

### CLI

```bash
# 依燈號查全部病人
python main.py --doctor-code 1234 --api-key sk-or-v1-xxxx

# 單一病人
python main.py --chart-no 12345678 --api-key sk-or-v1-xxxx

# 重試失敗的病人
python main.py --retry-failed

# 只重跑 AI（不重新抓資料）
python main.py --from-cache 12345678
```

### 環境變數（可選）

也可以建立 `.env` 檔案避免每次輸入：

```bash
cp .env.example .env
# 編輯 .env 填入帳密和 API Key
```

## OpenRouter API Key

1. 到 [openrouter.ai](https://openrouter.ai/) 註冊
2. 到 Keys 頁面建立一把 API Key
3. 在 GUI 的「OpenRouter Key」欄位貼上，或用 CLI 的 `--api-key` 參數

費用約 $0.01-0.03 / 病人（取決於資料量和 AI 輪數）。

## 輸出格式

每位病人產生如下 Markdown 摘要：

```markdown
# [床號] [姓名] - Day [N]

## 住院經歷 (Hospital Course)
（簡述住院原因、經過、重要事件）

## Objective
- VS: T/HR/RR/BP/SpO2
- Lab: CRP 12→8→5↓, WBC 15k→9.8k↓
- Imaging: CXR improved infiltration

## Assessment & Plan
#LLL pneumonia
* Blood culture(3/12): CRPA
* CXR(3/14): improved
- s/p Tazocin 4.5g Q8H (3/12-)
- consider de-escalate?
```

## 專案結構

```
├── main.py              # CLI 入口
├── gui.py               # Tkinter GUI
├── build.py             # PyInstaller 打包腳本
├── config/settings.py   # .env 設定
├── scraper/
│   ├── session.py       # 登入 + session 管理
│   ├── parser.py        # HTML → DataFrame
│   ├── endpoints.py     # URL 常數
│   ├── orchestrator.py  # crawl → AI → re-crawl 迴圈
│   └── fetchers/        # 9 個抓取模組
├── ai/
│   ├── client.py        # OpenRouter API
│   ├── prompts.py       # 分析 + 摘要 prompt
│   └── schema.py        # AI 回應格式
├── models/patient.py    # 資料模型
├── output/
│   ├── markdown.py      # Markdown 輸出
│   └── docx_export.py   # Word 匯出
└── cache/manager.py     # JSON 快取（斷點續傳）
```

## 致謝

基於學長的 VGH_function.py / VGH_GUI.py 查房工具改寫，加入 AI 摘要功能。
