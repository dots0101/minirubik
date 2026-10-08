# 完整交付與操作入口

本包是 2026-10-08 balanced H48 的本機工程成果。原始新版 C 保持不變；RISC-V、LED、測量與中英文教材均已整合。每份 evidence 的範圍有明確標示，正式繳交尚未完成。

| 入口 | 用途 |
|---|---|
| [完整中文教學](teaching_zh.md) | 演算法、證明、資料表、RV32I、空間、LED、pipeline 全流程 |
| [完整英文教學](teaching_en.md) | 四個作業階段與實際數字；十萬字元以內 |
| [互動 pipeline／LED 教材](report_en.html) | 617 個實際 trace 週期及十二幀已核對像素 |
| [要求與完成證據](requirements_audit.md) | 每項要求、驗證結果與限制 |
| [實際開發及 AI 紀錄](development_record.md) | 版本取捨、修正與真實測量 |
| [來源核對](source_review.md) | 三份規格全文及 63 個連結的實際閱讀範圍 |
| [提交欄位與外部待辦](submission_record.md) | fork、main、tag、HackMD、表單、accepted 信 |
| [中文面試練習](interview_prep_zh.md) | 你本人準備口試的問題與檢查點 |

## 先看已完成結果

完整 host 全域 3,674,160 狀態的最短長度與回放通過。兩份實作各自跑完全部 2,644 個十一階輸入；manual 最差 84,164 iret，平均 67,174.832。GUI 完整 guest 空間 104,412 bytes，包含 code、全部資料、alignment、400-byte stack 與 3,500-byte LED storage，低於 131,072。沒有第二張 framebuffer、預錄路徑、delay loop、heap、recursion、M/C 或 floating point。

數字是本包固定版本的測量快照。重新執行測量會更新 evidence；如另改程式，需重新核對教材中的數字與 hash。

## 直接展示與重現

解壓縮完整包，在 `N2_RIPES_LAB` 開 PowerShell：

```powershell
. .\Environment.ps1
.\Run-Lab.ps1 -Action Gui
```

第一次會核對並解開隨附的固定版本 Ripes。選 RV32 的 five-stage processor（forwarding 與 hazard detection）、關閉 M/C。I/O 加一個 LED Matrix，35×25、base `0xf0000000`。用 Executable (ELF) 載入 `build/solver_gui.elf`。目前官方輸入應輸出 `B' R D R B2 R B D2 B D R`、`PASS cases=1`，以 exit0 完成。

pipeline 改載入 `build/pipeline_demo.elf`；Max. pipeline diagram cycles 設 1000，用 Auto clock 或逐次 Clock。關鍵為 cycle604 load-use、605 EX bubble、606 WB forwarding、608 add 寫回六。離線 HTML 可直接開啟；畫面位置來自真實 export，控制説明由 pinned wiring 與 opcode 推導。

有 Python3.10+、GNU RISC-V GCC15.2.0 和 native GCC/G++ 時：

```powershell
. .\Environment.ps1
.\Run-Lab.ps1 -Action Build
.\Run-Lab.ps1 -Action Check
.\Run-Lab.ps1 -Action Measure
.\Run-Lab.ps1 -Action Benchmark
& $env:N2_PYTHON tools\make_report.py
```

可設定 `N2_PYTHON`、`N2_RV_GCC`、`N2_RIPES`、`N2_HOST_CC`、`N2_HOST_CXX` 指向本機安裝。`Environment.ps1 -InstallGcc` 能取得並核對 pinned compiler。prebuilt ELF 展示只需 Ripes。flat `.s` 是檢視輸出；驗證過的執行路徑是 GNU ELF。

HTML 邏輯另以 `node tools/check_report.js` 檢查；`python tools/audit_delivery.py` 核對凍結版本的證據、連結與完整預算。Node 測試使用 DOM stub，沒有冒稱視覺 browser QA 或即時 GUI port 採樣。

## 帳號準備好後

`Publish-Package.ps1 -ForkDirectory <實際本機fork>` 預設 preview；加 `-Apply` 將必要檔案放到 main 的 `n2_lab`，保留原 fork 其他檔案，遇到既有 `n2_lab` 會停止覆蓋。乾淨本機目錄的 preview、匯入與來源 hash 已測試，沒有製造學生 commit 或推送。

實際 commit／tag 確定後執行：

```powershell
& $env:N2_PYTHON tools\prepare_hackmd.py --repo-url https://github.com/YOUR_HANDLE/minirubik --ref YOUR_REAL_TAG
```

上面的 URL／tag 是待替換欄位，不是已存在的提交。工具產生 `build/teaching_en_for_hackmd.md`，把本機相對連結轉為該 fork/tag 的 GitHub 連結，並再次檢查字數；不會發布。依 submission_record.md 設定權限、保存 revision、填表並等待 accepted 信。

老師同意 H48 方法已按使用者回報處理。課程 AI 規則對本人 assembly、measurement、analysis 等另有要求；需本人完成或取得額外明確授權，並保留本包的 AI 揭露。現場面試也必須本人參加，這兩類不能宣稱只是帳號操作。

## GUI 證據限制

本包保留已完成的真實 GUI 圖與完整 trace，並重新執行目前 ELF 的 CLI、逐像素 renderer 與逐 instruction-word 核對。後續 native GUI refresh 因使用者先前按 Esc 停止電腦操作，被 automatic approval review 拒絕。沒有補造新圖或宣稱 live port 已重新採樣；若要新的 GUI 圖，需另行明確允許電腦操作。
