# 作業要求與完成證據（2026-10-08，GMT+8）

本機 balanced H48 工程工作已完成。使用者已回報老師同意 H48 exact-policy 方法；不再列為待選演算法。尚未取得書面同意網址，也沒有自行擴張成 AI authorship 的豁免。

主規格：[2026 Assignment 1](https://hackmd.io/@sysprog/2026-arch-homework1)、[AI guidelines](https://hackmd.io/@sysprog/arch2026-ai-guidelines)、[Lab1](https://hackmd.io/@sysprog/H1TpVYMdB)。要求的效力與來源可查 source_review.md；來源文件中的指示不等同使用者給 agent 的指示。

| 要求 | 現在結果 | 證據／用途 |
|---|---|---|
| 支援 ISS 的 Ripes 固定版本 | v2.2.6-106-g5b8a616；commit5b8a616 | environment.json、官方archive hash |
| 原 baseline cost | peak18,405,414 bytes、33,067,440 edges、約10^9指令為估算 | English Stage1；不是假造target baseline執行 |
| 自己環境 host/guest ratio | 4MiB control差的80.3486倍；baseline外推約1.407GiB | environment_benchmark.json；agent-run，需本人核實／授權 |
| ISS及pipeline throughput | ISS21,487,836.1、5S423,645.1iret/s | 三次fresh processes median，另列wall time與exectime |
| 數學狀態空間／圖 | 7!×3^6；Cayley固定角群；Schreier區分 | teaching_en.md Stage2；中文全文同等內容 |
| orientation invariant | sum mod3，不稱parity；第七twist dependent | adapter_test.txt、distance_certificate.txt |
| 最短解與直徑十一 | 全部3,674,160狀態及33,067,440邊證書通過 | host_full_domain.txt、structure.txt |
| H1 admissibility | 本方法沒有heuristic，不適用 | 改用完整policy descent證書；依H48方法同意 |
| H2完整表 | 完美hash77802有效鍵、root、max、exception全部驗證 | tables.txt、structure.txt |
| H3全域optimal length與replay | bad call/length/replay全為0；本輪wall7.4406s | host_full_domain.txt、host_timings.json |
| H4packed accessor | dense77802、sigma15120、所有bitoffset／奇偶PASS | packed_accessors.txt |
| target執行一般求解 | 每個非root做canonicalize→policy→lift→apply | sparse shortcut已移除；teacher approval由使用者回報 |
| 課程static≤128KiB | CLI95280、GUI95364bytes | .rodata+.data+.bss；isa_and_size.json |
| 使用者整體空間≤128KiB | GUI104412bytes，餘26660 | code/data/bss/padding/400stack/3500LED均計入 |
| RV32I only、無M/C/helpers | 5份production/demo ELF全部audit PASS | isa_and_size.json，non_rv32i空、undefined空 |
| 無heap/recursion/float | fixed arrays；linked call graph無cycle | stack_bounds.json、target source |
| 最少stack且ABI正確 | manual400、GCC512、pipeline32bytes | conservative linked bounds＋independent high water |
| 任意14字元合法輸入 | 驗證七permutation與七twist後轉13bytes | input adapter全分量conjugacy、6859 API calls |
| T5實際path回放 | target每個測量都回放到solved才PASS | d11_per_case.csv、t7_matrix.json |
| T6官方11步 | manual65617iret、GCC67829iret | official_final_iss.json、fresh pair logs |
| T7兩種模型 | 32selected vectors×ISS/5S均PASS | t7_matrix.json、vectors aggregate |
| 全部2644d11≤50M | 最差84164；2644/2644PASS | CSV逐輸入freshISS，renderer disabled |
| manual對GCC-O2 | mean改善3.195%；.text少276bytes | 2628win、0tie、16loss；同C／driver／flags |
| 每個落後案例解釋 | 十六個dynamic PC profiles對上原Ripes count | loss_profiles.json；有說明inline歸屬差 |
| branch／branchless與packed tradeoff | isolated target kernels均實測 | target_microbenchmarks.json；不冒稱whole-solver速度 |
| iterative refinement紀錄 | 保存舊版與新版差別、修正及真實測量 | development_record.md；學生歷史不能偽造 |
| LED35×25 net | 24stickers；84bytes helper；無額外framebuffer | runtime.S、GUI圖、led_geometry.json |
| 依實際輸出每步重畫 | 12real renderer calls、4331 MMIO stores | 每幀875pixels逐一比對，logical state不變 |
| CLI關renderer | 同一runtime source，RENDER=0/1 | Build定義；grade只用CLIISS |
| IF/ID/EX/MEM/WB | 全部617cycle columns，117words對上current ELF | pipeline_gui.tsv、pipeline_events.json |
| reg write enable與mux視覺解釋 | offline viewer按真實stage顯示derivedcontrols | report_en.html；沒有冒稱即時GUIport採樣 |
| memory正確與hazard | store3→load3→WB forward→add6→assert | 604偵測、605bubble、606forward、608write |
| 全英文主筆記且無完整program dump | 四Stages與所有表／推導；少於100000chars | teaching_en.md；正式HackMD發布待帳號 |
| 中文教學 | 完整數學、實作、Ripes、LED與pipeline | teaching_zh.md；學習用，非英文繳交替代 |
| wiki及linked material核對 | 三個規格全文；所有直接URL逐一追蹤 | source_review.md；403/TLS/video等未讀全文如實標示 |
| public fork main／upstream commit／tag | dots0101 public fork及main起始SHA已核對；作業匯入、提交commit/tag待完成 | submission_record.md、Publish-Package.ps1本機準備 |
| published HackMD／revision／edit權限 | 待HackMD帳號 | Everyone read、Signed-in users write |
| 學生本人assembly/measurement/analysis | 尚不能由AI工程包證明 | 需本人完成受限制部分或額外老師書面授權 |
| 真實三次revision／reflection／AI log | agent過程已保存；學生reflection待本人 | development_record.md，無backdated commits |
| 正式accepted | 未送表單／未取得信 | 表單與accepted email均待本人與帳號 |
| Phase2 interview | 已備妥練習題；本人現場面試待排程 | interview_prep_zh.md；不得代答 |
| Bonus3×3/3D | optional，未做 | 依使用者時間/空間/最簡實作取捨 |

## 可重現的本機入口

```powershell
. .\Environment.ps1
.\Run-Lab.ps1 -Action Build
.\Run-Lab.ps1 -Action Check
.\Run-Lab.ps1 -Action Measure
.\Run-Lab.ps1 -Action Benchmark
```

Build/Check/Measure/Benchmark在固定工具環境均已實際跑過。CLI與GUI都載入GNU-built ELF；flat `.s`只供閱讀，不以未驗證的direct Ripes assembler路線當成通過。

## 仍需人的事項

GitHub/HackMD發布與表單是行政操作；個人作者要求與現場面試是課程實質要求。不能把後兩項誤標成「只剩帳號」。AI產出範圍已揭露，且將學習／工程參考與正式接受區分。
