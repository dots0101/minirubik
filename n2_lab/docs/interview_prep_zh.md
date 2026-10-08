# 面試與整體流程複習

這是練習材料，不是面試代答。正式Phase2由你本人進行。英文正式筆記在teaching_en.md，完整中文推導在teaching_zh.md。

先能用一句話解釋整體：14字元輸入驗證→轉固定角13byte座標→展開工作狀態→H48正規化並保存frame→完美hash加bitmap rank取dense策略nibble→依frame搬回move→套用並輸出→重複直到solved→實際回放並逐步畫LED。

| 練習題 | 應掌握的證據／答案骨架 |
|---|---|
| 為何7!×3^6？有無corner parity限制？ | 固定一角後七角任意排列；orientation sum mod3決定第七個twist；2×2沒有edge parity限制 |
| Cayley與Schreier差別？ | 固定角R/B/D群對九HTM generators是Cayley；任意六面後mod24 whole-cube rotations則為coset圖 |
| 怎麼證明直徑十一？ | BFS遍历完整domain且d11非空；完整邊證書；不能由官方單一case推論沒有更深 |
| H48可以直接除48算軌道數嗎？ | 不可；stabilizer導致orbit sizes不同；77802來自完整列舉／Burnside證據 |
| 為什麼代表策略可以搬回？ | root-fixing graph automorphism保持距離及邊；記錄frame的逆向move pullback；T局部label要對中間state |
| policy如何不用full distance array？ | host驗證oracle不linked；target保存orbit下降move，每非root一般循環；方法已取得使用者回報同意 |
| rank compressed省什麼、花什麼？ | 131072 slots→usedbitmap/prefix→77802dense nibbles；72693payload；最多十五word popcount |
| nibble看誰的奇偶？ | dense rank，不是hash slot；漏換會讀到另一move |
| T三位元跨byte如何讀？ | 3j、byte/bit offset、兩次lbu組合shift&7；最後有guard不越界 |
| RV32I怎麼做×3／×35／mod3／popcount？ | shifts/adds、rowpointer+140、bounded subtract、SWAR；不能用M或compiler mul/div helpers |
| ABI怎麼檢查？ | a0–a3、callee saved、16byte對齊；call graph manual400／GCC512；optionalstats可bytealigned |
| 128KiB怎麼算？ | userwhole104412含text/rodata/bss/padding/stack/LED；不可只看94729tables或ELF檔案大小 |
| manual一定比GCC快？ | mean改善約3.195%，2628win16loss；看所有loss profiles；不隱藏樣本 |
| LED不是預錄如何證明？ | 從actual movebuffer apply→render；十二real calls4331 MMIO stores，875pixels每幀比對 |
| sw／lw／add的五階段控制？ | sw MEM604 RegWrite0；load MEM605 WB606 MEMREAD；add EX606 WB608 ALURES；三輸出值3/3/6 |
| load-use為何不能純forward？ | 相鄰consumer EX時間太早；604detect→605bubble→606WBforward；hold IF/ID且clear ID/EX |
| branch與ecall如何正確？ | EXredirect清younger；ecall等待先前writes排空才讀a0/a7；a7值是Ripes服務不是Linux通用syscall |
| 未知distance怎么驗證？ | EXPECTED255經lb變-1；replay與≤11，不能把未知值當oracle equality |
| 去掉prefix／guard／frame會怎樣？ | prefix影響rank／boundedcost，guard防讀越界，frame丟失move回原座標；能舉實例並說不變量 |

自我练習：不看答案重建policy_rank的offset0與31、跨byte三bit、store地址base+4(35y+x)；以dense135614解釋負面效能結果；再從pipeline trace指認哪個cycle真的寫register而非只經過WB。

個人反思請由你寫：你自己決定了什麼、親自核實哪些結果、接受／拒絕哪些AI建議以及原因。不得以本练習頁冒充你的理解或開發歷史。

課程規則允许與assessor共有的語言、切換語言、白板或書面方式；可以選human-written questions而不影響排程或成績。錄音需本人同意。其他人或agent不能代替這場現場評量。
