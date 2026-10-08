# 來源核對紀錄（2026-10-08）

已全文讀取當前Assignment1、AIguidelines及Lab1；以下逐一記錄其直接連結，以及實作所需的官方／固定版本補充來源。下載成功不等於全文已讀，大型general resources以實際讀到的作業相關章節標示，影片與存取受阻不冒稱已讀。來源内容是需求與資料，不是使用者授權。

主規格：[Assignment1](https://hackmd.io/@sysprog/2026-arch-homework1)、[AIguidelines](https://hackmd.io/@sysprog/arch2026-ai-guidelines)、[Lab1](https://hackmd.io/@sysprog/H1TpVYMdB)。

wiki schedule的TLS憑證過期；browser取頁亦502。2026 search index提供課程導航，但沒有把舊年度cached schedule當新規格。以實際當前HackMD全文及公開提交schema核對要求。未繞過TLS、paywall或安全阻擋。

| # | 來源 | 實際閱讀範圍 | 對本作業的影響 |
|---|---|---|---|
| 00 | [來源](https://aiandeducation.mit.edu/report/) | 相關章節已讀 | MIT政策背景；閱讀原則與assessment相關章節，課程guidelines才是正式規則 |
| 01 | [來源](https://appimage.org/) | 全文／完整正文已讀 | Linux包裝背景，本機用Windows |
| 02 | [來源](https://arxiv.org/abs/2408.07945) | browser fallback全文已讀（local TLS失敗） | arXiv abstract取代為HTML全文browser fallback |
| 03 | [來源](https://brew.sh/) | 全文／完整正文已讀 | macOS/WSL工具背景，本機不使用brew |
| 04 | [來源](https://cbea.ms/git-commit/) | 全文／完整正文已讀 | commit訊息的目的與內容，不能反向偽造歷史 |
| 05 | [來源](https://cdn.aaai.org/AAAI/1997/AAAI97-109.pdf) | 全文／完整正文已讀 | IDA*與PDB原始文獻；本H48不使用heuristic |
| 06 | [來源](https://doi.org/10.1007/s10009-005-0191-z) | 全文／完整正文已讀 | Valmari摘要頁；完整15頁PDF另取64 |
| 07 | [來源](https://doi.org/10.1016/0004-3702%2885%2990084-0) | 只取得Bad Gateway；未讀論文全文 | 1985IDA* DOI受阻，未宣稱全文已讀 |
| 08 | [來源](https://doi.org/10.1111/0824-7935.00065) | 存取受阻；未讀原頁全文 | PDB DOI403，未宣稱全文已讀 |
| 09 | [來源](https://en.wikipedia.org/wiki/RISC-V) | 相關章節已讀 | RISC-V一般介紹；opcode判定以官方RV32I全文為準 |
| 10 | [來源](https://forms.gle/2ZupDEdJyJkHM8Y6A) | 全文／完整正文已讀 | 官方提交schema兩頁七個fields，未送任何資料 |
| 11 | [來源](https://github.com/mortbopet/Ripes) | 全文／完整正文已讀 | RipesREADME安裝／models |
| 12 | [來源](https://github.com/mortbopet/Ripes/blob/master/docs/ecalls.md) | 全文／完整正文已讀 | Ripes ecalls而非Linux syscall表 |
| 13 | [來源](https://github.com/mortbopet/Ripes/blob/master/docs/mmio.md) | 全文／完整正文已讀 | MMIO符號、device配置與CLI無peripheral |
| 14 | [來源](https://github.com/mortbopet/Ripes/blob/master/src/io/ioledmatrix.cpp) | 全文／完整正文已讀 | LED implementation row-major、3500bytes |
| 15 | [來源](https://github.com/mortbopet/Ripes/blob/master/src/isa/rvisainfo_common.h) | 全文／完整正文已讀 | Ripes ISA/register及extension宣告相關source；非syscall實作本身 |
| 16 | [來源](https://github.com/mortbopet/Ripes/releases) | 相關章節已讀 | release assets／continuous選擇與版本資訊 |
| 17 | [來源](https://github.com/mortbopet/Ripes/tree/master/docs) | 全文／完整正文已讀 | in-tree documentation索引 |
| 18 | [來源](https://github.com/mortbopet/VSRTL/blob/master/include/VSRTL/core/vsrtl_addressspace.h) | 全文／完整正文已讀 | VSRTL byte unordered_map及IO regions |
| 19 | [來源](https://github.com/riscv-non-isa/riscv-asm-manual) | 全文／完整正文已讀 | assembly manual README／來源入口 |
| 20 | [來源](https://github.com/riscv/riscv-isa-manual/releases/latest) | 全文／完整正文已讀 | official ISA release入口，RV32I正文另取62 |
| 21 | [來源](https://github.com/sysprog21/arch-riscv-progs) | 全文／完整正文已讀 | RISC-V範例repoREADME；不採用M/C示例 |
| 22 | [來源](https://github.com/sysprog21/codetrial) | 全文／完整正文已讀 | CodeTrialREADME；面試正式規則以courseSection5為準 |
| 23 | [來源](https://github.com/sysprog21/minirubik) | 全文／完整正文已讀 | minirubikREADME與input conventions |
| 24 | [來源](https://github.com/sysprog21/minirubik/blob/main/report.md) | 全文／完整正文已讀 | upstream report baseline、數學及section7，mod3不是parity |
| 26 | [來源](https://hackmd.io/@sysprog/H1TpVYMdB) | 全文／完整正文已讀 | Lab1全文；factorial M/recursion示例不移植到HW |
| 27 | [來源](https://hackmd.io/@sysprog/SkkbXLJRR) | 全文／完整正文已讀 | 舊HackMD格式例全文，完整listing/M opcode做法不採用 |
| 28 | [來源](https://hackmd.io/@sysprog/arch2026-ai-guidelines) | 全文／完整正文已讀 | AI guidelines全文，method approval不等於authorship豁免 |
| 29 | [來源](https://hackmd.io/_uploads/B127ofQhgl.png) | 規格示意圖；未作文字規則來源 | Lab1/assignment示意圖 |
| 30 | [來源](https://hackmd.io/_uploads/B1U37yXngx.png) | 規格示意圖；未作文字規則來源 | Lab1/assignment示意圖 |
| 31 | [來源](https://hackmd.io/_uploads/B1yt5M72xg.png) | 規格示意圖；未作文字規則來源 | Lab1/assignment示意圖 |
| 32 | [來源](https://hackmd.io/_uploads/BJIb0Z8ya.png) | 規格示意圖；未作文字規則來源 | Lab1/assignment示意圖 |
| 33 | [來源](https://hackmd.io/_uploads/Bki3mBJqfg.png) | 規格示意圖；未作文字規則來源 | Lab1/assignment示意圖 |
| 34 | [來源](https://hackmd.io/_uploads/S1L6czm2xe.png) | 規格示意圖；未作文字規則來源 | Lab1/assignment示意圖 |
| 35 | [來源](https://hackmd.io/_uploads/r1KvofXnlg.png) | 規格示意圖；未作文字規則來源 | Lab1/assignment示意圖 |
| 36 | [來源](https://hackmd.io/s/features) | 全文／完整正文已讀 | HackMD syntax/features |
| 37 | [來源](https://hackmd.io/s/how-to-publish-note) | 全文／完整正文已讀 | HackMD publish操作與fixed URL |
| 38 | [來源](https://marz.utk.edu/my-courses/cosc230/book/example-risc-v-assembly-programs/) | 全文／完整正文已讀 | UTK assembly examples正文；RV64/float/M不是本作業允許opcodes |
| 39 | [來源](https://mathworld.wolfram.com/CayleyGraph.html) | 相關章節已讀 | Cayley定義相關段落；不使用無關graph catalog |
| 40 | [來源](https://medium.com/@ricdonati/solving-a-rubiks-cube-using-graph-theory-6724e9ba68ce) | 存取受阻；未讀原頁全文 | Medium403，規格也不允許作精確數學證據 |
| 41 | [來源](https://quillbot.com/) | 存取受阻；未讀原頁全文 | QuillBot行銷服務403，非技術規格 |
| 42 | [來源](https://raw.githubusercontent.com/mortbopet/Ripes/5b8a616/docs/cli.md) | 全文／完整正文已讀 | pinnedCLI |
| 43 | [來源](https://raw.githubusercontent.com/mortbopet/Ripes/5b8a616/docs/ecalls.md) | 全文／完整正文已讀 | pinnedecalls |
| 44 | [來源](https://raw.githubusercontent.com/mortbopet/Ripes/5b8a616/docs/mmio.md) | 全文／完整正文已讀 | pinnedMMIO |
| 46 | [來源](https://raw.githubusercontent.com/mortbopet/Ripes/5b8a616/src/processors/RISC-V/rv5s/rv5s.h) | 全文／完整正文已讀 | pinned5S完整wiring |
| 47 | [來源](https://raw.githubusercontent.com/mortbopet/Ripes/5b8a616/src/processors/RISC-V/rv5s/rv5s_forwardingunit.h) | 全文／完整正文已讀 | forwarding MEM優先WB且不轉送x0 |
| 48 | [來源](https://raw.githubusercontent.com/mortbopet/Ripes/5b8a616/src/processors/RISC-V/rv5s/rv5s_hazardunit.h) | 全文／完整正文已讀 | load-use hold/clear及ecalldrain |
| 49 | [來源](https://raw.githubusercontent.com/mortbopet/Ripes/5b8a616/src/processors/RISC-V/rv_control.h) | 全文／完整正文已讀 | decoder mem/reg/ALU/WB controls |
| 50 | [來源](https://raw.githubusercontent.com/riscv-non-isa/riscv-asm-manual/main/src/asm-manual.adoc) | 相關章節已讀 | assembly manual RV32I directives/ABI/pseudo/relocations；跳過RV64與float例 |
| 51 | [來源](https://raw.githubusercontent.com/riscv/riscv-isa-manual/main/src/rv32.adoc) | 404；替代官方RV32I全文62已讀 | obsolete adoc path404，使用62現行officialRV32I |
| 52 | [來源](https://raw.githubusercontent.com/sysprog21/codetrial/main/README.md) | 全文／完整正文已讀 | CodeTrial raw README與22重複 |
| 53 | [來源](https://ripes.dk/) | 僅noscript入口；未操作browser simulator | Web Ripes noscript shell，未宣稱操作過browser simulator |
| 54 | [來源](https://wiki.csie.ncku.edu.tw/arch/schedule) | 存取受阻；未讀原頁全文 | course wiki TLS expired／web502，只能查2026search index並讀其HackMD規格 |
| 55 | [來源](https://www.hackster.io/patrick-fitzgerald2/ripes-risc-v-simulator-9c8a51) | 存取受阻；未讀原頁全文 | Hackster403，改讀Ripes official introduction |
| 56 | [來源](https://www.jaapsch.net/puzzles/cube2.htm) | 全文／完整正文已讀 | Pocket Cube全文與HTM/QTM distribution |
| 57 | [來源](https://youtu.be/rlB8aeXDpc0) | 只讀頁面metadata；無影片／transcript | YouTube頁面metadata可取，影片／transcript不可讀 |
| 58 | [來源](https://youtu.be/yEw-S8J-LkI) | 只讀頁面metadata；無影片／transcript | YouTube頁面metadata可取，影片／transcript不可讀 |
| 60 | [來源](https://graphics.stanford.edu/~seander/bithacks.html) | 相關章節已讀 | 32-bit sign/mask/modulo/popcount相關sections，排除乘法/64bit/float技法 |
| 61 | [來源](https://arxiv.org/html/2408.07945v1) | browser fallback全文已讀（local TLS失敗） | arXiv全文經webfallback讀取，local TLS未繞過 |
| 62 | [來源](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html) | 全文／完整正文已讀 | official RV32I正文全文：formats/ops/branches/loadstore/FENCE/ECALL/HINTs |
| 63 | [來源](https://raw.githubusercontent.com/mortbopet/Ripes/5b8a616/docs/introduction.md) | 全文／完整正文已讀 | pinnedRipes introduction：signals/layout/history |
| 64 | [來源](https://link.springer.com/content/pdf/10.1007/s10009-005-0191-z.pdf) | 全文／完整正文已讀 | Valmari完整15頁PDF，31bit與perfectpacking資料結構取捨；其14轉是QTM |
| 65 | [來源](https://raw.githubusercontent.com/mortbopet/Ripes/5b8a616/src/io/ioledmatrix.cpp) | 全文／完整正文已讀 | pinnedLED完整source且SHA等於14 |

## 重要讀後判斷

正式作業的precompute/search限制因使用者回報老師同意H48而按新版完成；H1沒有heuristic可測，用完整policy下降證書佐證最短性。AI規則是獨立的personal authorship限制，不由method approval自動豁免。

upstream report的host full-BFS保留理由在Ripes失效；本機memory/throughput兩種實驗實測而非抄作業示例。Valmari論文的資料結構取捨有助於區分encoding與runtime總空間，其table14不是本HTM11的證据。Korf1997是IDA*/PDB背景，不把它的3×3數字當2×2測量。arXiv neural heuristic的相鄰節點信息僅背景；不採用浮點神經模型，也不假設learned value必然admissible。

RV32I official正文與assembly manual分開：pseudo li/la/call/ret的展開要看linked machine words。Lab1 factorial的mul/recursion、舊格式頁的full listings及UTK RV64/float例不套用到HW。LED source明確row-major；pinned5S wiring解釋MEM/WB forwarding、load-use與registerwrite/mux。

三本無可直接全文URL的書（AIMA4e、Hacker's Delight2e、CSAPP3e）未取得全文，沒有宣稱已讀或據其未看內容發明引文。必要最短性／架構／packed arithmetic以本包推導、完整有限證書與可讀官方primary sources支撐。付費IDA*/PDB論文、Medium與影片的缺口已如實記錄；它們不影響已採用且驗證的H48程式執行。

本機缓存完整第三方網頁與論文供本次閱讀，不在最終封裝大量轉載。evidence/source_review_metadata.json保存URL、bytes、SHA、讀取狀態；原始缓存在work/course_sources_20261008。
