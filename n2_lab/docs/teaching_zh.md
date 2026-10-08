# 二階魔方完整教學：Balanced H48、RV32I 與 Ripes

版本：2026-10-08（Asia/Taipei）。本教材完整保留狀態、S3、T、H48 與 lifting 的數學推導，再補上新版壓縮、RISC-V、LED、測量與 pipeline。英文繳交用教材在 [teaching_en.md](teaching_en.md)，此中文版供學習。全文不貼完整程式碼，原始碼分別放在 reference/ 與 target/。

新版先驗證輸入，再以 48 個固定 root 的圖自同構找代表狀態、讀取 rank 壓縮策略、依 frame 搬回 move，重複到已解。所有非已解輸入都跑一般迴圈，不使用 sparse 全路徑捷徑。LED 直接回放求解器實際輸出的 moves。

實際提交專案：[dots0101/minirubik](https://github.com/dots0101/minirubik)，為 sysprog21/minirubik 的 public fork，分支 `main`。起始 commit 為 [`231796cc48868f4ea276f652139b6bebbad0cd02`](https://github.com/dots0101/minirubik/commit/231796cc48868f4ea276f652139b6bebbad0cd02)；這是 upstream 起點，提交 commit 與 tag 待匯入後記錄。保留的 baseline C 與這個起始版本在統一 checkout 換行後一致。

## 階段一：原版與 Ripes 成本

原版完整 BFS 的三項主要配置為 move-per-state 3,674,160 bytes、queue 14,696,640 bytes、factored transition 34,614 bytes，peak 合計 **18,405,414 bytes**。完整圖有 33,067,440 條有向邊，每邊更新排列和方向兩個因子，共 66,134,880 次更新；每次估十五指令得到約十億，是估算，沒有在 Ripes 執行完整 baseline。

Ripes 的 sparse guest memory 以每 byte 為 key 的 host hash map 保存寫入。獨立 tight store loop 用三個 fresh-process 重複取中位數，和空程式控制組相比：

| Guest bytes touched | Median peak host bytes | Delta from empty control |
| --- | --- | --- |
| 0 | 32198656 | 0 |
| 4096 | 32518144 | 319488 |
| 131072 | 43053056 | 10854400 |
| 1048576 | 116666368 | 84467712 |
| 4194304 | 369205248 | 337006592 |


4 MiB 差值斜率為 **80.3486 host bytes / written guest byte**；以線性模型推估 baseline peak 加控制組約 **1.407 GiB**。這是指定 build 的粗估，map rehash、allocator 與 host 負載都可能影響結果，不能當成完整 baseline 實測。

另用 128 KiB、八次走訪、1,310,758 條退休指令的程式量測 throughput，取三次中位數；使用 Ripes execution milliseconds，不計啟動時間：

| Model | Retired instructions | Cycles | Median iret/s |
| --- | --- | --- | --- |
| RV32_ISS | 1310758 | 1310758 | 21487836.1 |
| RV32_5S | 1310758 | 1835050 | 423645.1 |


依此速率推估十億指令：ISS 約 46.5 秒，5S 約 39.3 分鐘。不同 workload 不保證相同速率。

環境固定 Ripes `v2.2.6-106-g5b8a616` / `5b8a616`、xPack RISC-V GCC 15.2.0、RV32I/ILP32、`-O2`、無 linker relaxation、M/C 均關閉；Windows 11、Core Ultra 9 275HX、24 logical CPUs。課程 static data 定義為 `.rodata+.data+.bss`；使用者另要求**程式、資料、buffer、padding、stack、LED 的整個必需空間**也在 128 KiB 以下，後文分別列出。

## 階段二：數學與演算法

## 0. 求解流程

`n2_solve()` 先處理已解狀態；所有非已解狀態每輪依序做 H48 正規化、查詢下降策略、將 move 搬回原座標，再更新狀態。

**有限證書**是對固定資料完整枚舉後得到的驗證結果：枚舉覆蓋整個定義域，逐項檢查待證等式，任一反例都使驗證失敗。文中的一般定理則以數學證明建立。

求解器的正確性分成四部分：

1. 狀態座標與九個 move 精確描述問題；
2. host 的 $D$ 就是真實最短距離；
3. H48 quotient 與 move lifting 保持「距離下降一」；
4. rank 壓縮與三位元 accessor 精確保留已驗證的策略與局部 move 映射。

## 1. 狀態座標

二階魔方有八個角塊。把位置與角塊都編為 $0,\ldots,7$。令

$$
p_i=\text{位置 }i\text{ 上的角塊},\qquad o_i\in\{0,1,2\}=\text{該角塊的方向}.
$$

整顆立方體的空間朝向不算 move。指定角塊的位置與方向共有 $8\cdot3=24$ 種，恰與立方體的 24 種空間朝向一一對應；因此可唯一把角塊 7 固定為

$$
p_7=7,\qquad o_7=0.
$$

本座標先取方向條件

$$
\sum_{i=0}^{6}o_i\equiv0\pmod3.
$$

九個 move 均保持這個條件，且所有滿足條件的候選座標皆可達，證明見第 2 章。任給 $o_0,\ldots,o_5$，都有唯一

$$
o_6\equiv-\sum_{i=0}^{5}o_i\pmod3.
$$

令 $P_7$ 為 $0,\ldots,6$ 的全部排列。七個活動角塊有 $|P_7|=7!$ 種排列，六個獨立方向各有三種。因此候選狀態集合

$$
\mathcal X=P_7\times\{0,1,2\}^6,\qquad |\mathcal X|=7!3^6=3\,674\,160.
$$

公開與內部表示正對應上述座標：

```c
typedef struct { uint8_t perm[7]; uint8_t twist[6]; } N2State;
typedef struct { uint8_t p[8]; uint8_t o[8]; } WorkState;
```

`expand_public()` 檢查 `perm[0..6]` 是 $0,\ldots,6$ 的排列、`twist[i]<3`，再唯一恢復 $o_6,p_7,o_7$；`compress_public()` 只刪去這些可唯一恢復的欄位。因此在合法狀態上兩者互逆。

內部 helper 皆要求輸入 `WorkState` 滿足排列、固定角與方向總和不變量。

## 2. 轉動與狀態圖

### 2.1 九種轉動（move）

固定角不接觸的三面記為 $X,Y,Z$。HTM 把 quarter-turn、half-turn、inverse-quarter-turn 都算一步，所以 move 集合為

$$
X,X^2,X^3,\quad Y,Y^2,Y^3,\quad Z,Z^2,Z^3.
$$

包含固定角的面不必另列：轉該面後再整體旋轉以恢復固定角，等價於反向轉其對面，而且成本仍為一。

對 move $m$，令 $u_m(i)$ 為新位置 $i$ 的舊來源位置，$v_m(i)\in\{0,1,2\}$ 為方向增量。定義

$$
p'_i=p_{u_m(i)},\qquad o'_i\equiv o_{u_m(i)}+v_m(i)\pmod3.
$$

`state_move()` 實作上述更新：

```c
q = n2_b8_move_src[mi * 8u + i];
d->p[i] = s->p[q];
v = s->o[q] + n2_b8_move_delta[mi * 8u + i];
d->o[i] = v >= 3u ? v - 3u : v;
```

每個 `move_src` row 是位置排列；每個 `move_delta` row 的總和為 $0\bmod3$，且位置 7 始終來自 7、增量 0。因此九個 move 保持第 1 章不變量。每個 quarter-turn 的三次方是逆、half-turn 自逆，所以九個 move 都可逆。

### 2.2 狀態圖

**定義（圖、路徑、距離）。** 令圖 $\Gamma$ 的頂點為 $\mathcal X$；若 $y=M_m(x)$，就在 $x,y$ 間連邊。因 move 可逆，$\Gamma$ 是無向圖。路徑長度是邊數；$d(x,y)$ 是最短路徑長度。已解狀態記為 $e$。

host 為每個候選狀態存一個非負整數 $D(x)$，並完整驗證：

$$
D(e)=0\quad\text{且只有 }e\text{ 為 }0,
$$

$$
x\sim y\Longrightarrow |D(x)-D(y)|\le1,
$$

以及每個 $x\ne e$ 都有鄰居 $y$ 使 $D(y)=D(x)-1$。

**定理 2.1（距離證書）。** $D(x)=d(x,e)$ 對全部 $x\in\mathcal X$ 成立。

**證明。** 反覆選 $D$ 少一的鄰居，恰 $D(x)$ 步到唯一的零點 $e$，故 $d(x,e)\le D(x)$。反之，任一步最多使 $D$ 降一；任何從 $D(x)$ 降到 0 的路至少有 $D(x)$ 步，故 $d(x,e)\ge D(x)$。∎

完整證書檢查全部 $3\,674\,160$ 個頂點與 $9\cdot3\,674\,160=33\,067\,440$ 個有向 move。因每個候選狀態都有下降鏈到 $e$，第 1 章的全部座標都確實可達；並且

$$
\boxed{\max_x d(x,e)=11},
$$

其中距離 11 的狀態有 2,644 個。

## 3. 狀態編碼

執行期程式（runtime）與離線工具（host）都以整數索引狀態。

六個獨立方向直接視為六位三進位數：

$$
\operatorname{ori}(o)=3^5o_0+3^4o_1+\cdots+3o_4+o_5\in\{0,\ldots,728\}.
$$

對排列 $p=(p_0,\ldots,p_6)$，令 $a_i$ 為位置 $i$ 時尚未使用且小於 $p_i$ 的元素數。Lehmer rank 為

$$
\operatorname{pr}(p)=a_0 6!+a_1 5!+\cdots+a_5 1!\in\{0,\ldots,5039\}.
$$

這是排列的字典序編號：$a_i(6-i)!$ 恰計算在第 $i$ 個位置第一次變小時略過的排列數。反向依 $6!,5!,\ldots,1!$ 逐次取商，便唯一恢復各 $a_i$ 與原排列。因此 `perm_rank7()` 是一一編碼。

host 使用密集 rank

$$
\operatorname{dense}(s)=729\operatorname{pr}(p)+\operatorname{ori}(o),
$$

其值恰為 $0,\ldots,3\,674\,159$。

可用的無碰撞輔助座標使用

$$
K(s)=2^{10}\operatorname{pr}(p)+\operatorname{ori}(o)=(\operatorname{pr}\ll10)\;|\;\operatorname{ori}.
$$

因 $\operatorname{ori}<729<2^{10}$，商與低十位可唯一恢復 `pr` 與 `ori`，所以 $K$ 也無碰撞；它只是不密集。

## 4. 群與圖的對稱

### 4.1 群、群作用與陪集

**定義（群）。** 集合 $G$ 配上一個二元運算。若運算在 $G$ 上封閉且滿足結合律，存在單位元 $1$，且每個 $g\in G$ 都有逆元 $g^{-1}$，則 $G$ 為群。

本題的群元素都是狀態集合上的雙射，運算是函數合成

$$
(f\circ g)(x)=f(g(x)).
$$

雙射的合成仍是雙射，$\mathrm{id}$ 是單位元，而且

$$
(f\circ g)^{-1}=g^{-1}\circ f^{-1}.
$$

若 $K\subseteq G$ 對同一運算本身也成群，寫 $K\le G$，稱子群。$n$ 個物件的全部排列形成對稱群 $S_n$。

**定義（群作用）。** 群 $G$ 作用在集合 $X$ 上，是指定每個 $g\in G,x\in X$ 的 $g(x)\in X$，並滿足

$$
1(x)=x,\qquad (gh)(x)=g(h(x)).
$$

**定義（orbit、stabilizer）。**

$$
G\cdot x=\{g(x):g\in G\},\qquad G_x=\{g\in G:g(x)=x\}.
$$

若兩個 orbit 相交，設 $g(x)=h(y)$，則 $y=h^{-1}g(x)$，故兩者其實是同一 orbit；又 $x=1(x)$，所以 orbits 分割 $X$。所有 orbit 的集合記為 $X/G$。由單位元、合成與取逆都保持 $x$ 可知 $G_x$ 是子群。

若 $K\le G$，集合 $Kg=\{kg:k\in K\}$ 稱右陪集。映射 $k\mapsto kg$ 是雙射，所以每個右陪集有 $|K|$ 個元素；兩個右陪集若相交，乘上適當逆元即得兩者相同。

**定理 4.1（orbit--stabilizer）。** 對有限群作用，

$$
|G\cdot x|=\frac{|G|}{|G_x|}.
$$

**證明。** 固定 $y=g(x)$。把 $x$ 送到 $y$ 的群元素恰為左陪集 $gG_x$，所以每個 orbit 元素恰有 $|G_x|$ 個群元素映到它。∎

### 4.2 圖自同構

**定義。** 圖 $\Gamma$ 的自同構是頂點雙射 $h$，且

$$
x\sim y\iff h(x)\sim h(y).
$$

若 $h(e)=e$，稱固定根自同構。

**定理 4.2.** 圖自同構保持距離；固定根時

$$
d(h(x),e)=d(x,e).
$$

**證明。** 對最短路徑逐點套 $h$，得到同長路徑，所以 $d(h(x),h(y))\le d(x,y)$；對 $h^{-1}$ 重做即得反向不等式。∎

## 5. $S_3$ 軸對稱

### 5.1 六個軸置換

八個角位置可用三個 bit 表示：

$$
i=4a+2b+c,
\qquad a,b,c\in\{0,1\}.
$$

交換三條座標軸共有 $3!=6$ 種，形成 $S_3$。令 $\phi_h$ 是第 $h$ 個軸置換。

程式資料：

```text
n2_b8_sym_pos[6×8]       φ_h 對位置／角塊編號的作用
n2_b8_sym_twist[6×8×8×3] 對方向的完整作用
n2_b8_sym_inv[6]          逆變換編號
```

定義位置 parity

$$
\chi(i)=(a+b+c)\bmod2.
$$

六個完整狀態變換 $U_h$ 可寫成

$$
p'_{\phi_h(i)}=\phi_h(p_i),
$$

$$
o'_{\phi_h(i)}
\equiv
\varepsilon_h o_i+\beta_h(\chi(i)-\chi(p_i))\pmod{3},
$$

其中 $(\varepsilon_h,\beta_h)$ 為六個固定常數對；程式編號如下，$\phi_h$ 以八個位置的像列出：

| $h$ | $\phi_h(0),\ldots,\phi_h(7)$ | $\varepsilon_h$ | $\beta_h$ |
|---:|---|---:|---:|
| 0 | `0,1,2,3,4,5,6,7` | 1 | 0 |
| 1 | `0,2,1,3,4,6,5,7` | 2 | 1 |
| 2 | `0,1,4,5,2,3,6,7` | 2 | 2 |
| 3 | `0,2,4,6,1,3,5,7` | 1 | 2 |
| 4 | `0,4,1,5,2,6,3,7` | 1 | 1 |
| 5 | `0,4,2,6,1,5,3,7` | 2 | 0 |

`n2_b8_sym_twist` 是此公式的 1152 個查表值；驗證器逐格重算並確認完全相同。

**命題 5.1。** 每個 $U_h$ 將合法狀態映成合法狀態，且固定 solved 狀態。

**證明。** $\phi_h$ 同時重標位置與角塊，故排列性保持。方向取模三仍在 $\{0,1,2\}$。方向總和為

$$
\varepsilon_h\sum_i o_i
+\beta_h\Bigl(\sum_i\chi(i)-\sum_i\chi(p_i)\Bigr).
$$

$p$ 是排列，所以第二括號是同一批數重排後相減，為零；第一項原本亦為零。若 $p_i=i,o_i=0$，兩式仍給 $p'=\mathrm{id},o'=0$。∎

**命題 5.2。** 六個 $U_h$ 在合成下構成六元素群，而且其乘法規則與三條軸的六種排列完全一致。

**證明。** 令 $A=U_1$、$B=U_3$。由位置表直接合成可得 $A^2=\mathrm{id}$、$B^3=\mathrm{id}$，且 $ABA=B^{-1}$。方向公式合成時，若先做係數 $(\varepsilon_b,\beta_b)$、再做 $(\varepsilon_a,\beta_a)$，新係數為

$$
\varepsilon=\varepsilon_a\varepsilon_b,
\qquad
\beta=\varepsilon_a\beta_b+\beta_a\pmod{3}.
$$

把 $A=(2,1)$、$B=(1,2)$ 代入，也得到同三個關係，所以位置與方向部分一致。由 $AB=B^{-1}A$，任何 A、B 字串都可把 A 推到最右側，再用 $A^2=\mathrm{id},B^3=\mathrm{id}$ 化成下列六種形式

$$
I,\ A,\ B,\ BA,\ B^2,\ B^2A.
$$

它們的位置作用依序正是 $U_0,U_1,U_3,U_5,U_4,U_2$，六者互不相同。因此生成集合至多六個且至少六個，恰為這六個 $U_h$；合成與取逆都留在其中，所以構成群。∎

### 5.2 保邊性

對每個 $U_h$，有一個固定的九 move 置換 $\sigma_h$ 使

$$
U_h(M_m(s))=M_{\sigma_h(m)}(U_h(s)).
$$

**有限證書命題 5.3。** 上式對六個 $h$、九個 $m$、全部 $s\in \mathcal X$ 成立。

**證明。** 驗證器直接對兩個生成元 $A=U_1$、$B=U_3$ 的全部 $3\,674\,160\times 9$ 條有標籤邊比較等式兩側；任一完整 `WorkState` 不等即失敗，結果全通過。其餘四個 $U_h$ 由命題 5.2 的 A、B 合成得到。若 $g_1,g_2$ 的 move 置換分別為固定的 $\sigma_1,\sigma_2$，則令 $t=g_1(s)$、$n=\sigma_1(m)$，直接代入

$$
g_2(g_1(M_m(s)))
=g_2(M_{\sigma_1(m)}(g_1(s)))
=M_{\sigma_2(\sigma_1(m))}(g_2(g_1(s))).
$$

故等變性對合成封閉，因此由 A、B 生成的六個 $S_3$ 元素全都成立。∎

由定理 4.2，每個 $U_h$ 是固定根圖自同構，故保持到根距離。

### 5.3 排列軌道與 Burnside 引理

**Burnside 引理。** 有限群 $G$ 作用在有限集合 $X$ 時，

$$
|X/G|=\frac1{|G|}\sum_{g\in G}|\operatorname{Fix}(g)|,\qquad \operatorname{Fix}(g)=\{x:g(x)=x\}.
$$

**證明。** 計數所有滿足 $g(x)=x$ 的 pair $(g,x)$。先固定 $g$，得到右式分子。若 $y=a(x)$，則 $h\mapsto aha^{-1}$ 把 $G_x$ 雙射到 $G_y$，故同一 orbit 的 stabilizer 等大。再由 orbit--stabilizer，
$|G\cdot x||G_x|=|G|$，所以每個 orbit 恰貢獻 $|G|$ 個 pair。除以 $|G|$ 即得。∎

先忽略方向，只看七元素排列。置換中的兩元素循環稱 **2-cycle**，三元素循環稱 **3-cycle**，不動元素稱 **fixed point**。

若 $p\circ\phi=\phi\circ p$，稱 $p$ 與 $\phi$ 可交換。排列被軸重標 $\phi$ 固定，恰等價於 $p$ 與 $\phi$ 可交換。

恆等軸置換固定全部 5040 個排列。

一個兩軸交換在七個活動位置上具有「兩個 2-cycle + 三個 **fixed point（不動點）**」。先證明一個必要事實：若 $p\phi =\phi p$，而 $i$ 在 $\phi$ 下的最小循環長度為 $r$，則 $p(i)$ 的循環長度也恰為 $r$。因 $\phi ^r(i)=i$，交換性給

$$
\phi^r(p(i))=p(\phi^r(i))=p(i),
$$

所以 $p(i)$ 的循環長度整除 $r$；再對 $p^{-1}$ 用同一論證，得到 $r$ 也整除 $p(i)$ 的循環長度，因此兩者相等。故與 $\phi$ 可交換的排列必把同長 cycle 映到同長 cycle。

對兩軸交換而言，三個 fixed point 可任意互換，有 $3!$ 種；兩個 2-cycle 可互換，有 $2!$ 種；每個來源 2-cycle 映到目標 2-cycle 時，第一點可選目標 cycle 的兩個起點之一，第二點便由交換性唯一決定，因此再乘 $2^2$。固定排列數為

$$
3!\cdot2!\cdot2^2=48.
$$

一個三軸循環具有「兩個 3-cycle + 一個 fixed point」。fixed point 必送到 fixed point；兩個 3-cycle 可互換，有 $2!$ 種；每個來源 3-cycle 的第一點可送到目標 cycle 的三個起點之一，其餘兩點由交換性唯一決定。因此固定排列數為

$$
2!\cdot3^2=18.
$$

$S_3$ 中有一個恆等、三個兩軸交換、兩個 3-cycle。Burnside 給

$$
\boxed{\frac{5040+3\cdot48+2\cdot18}{6}=870}
$$

個排列軌道。

### 5.4 排列軌道的穩定子

若一個排列的穩定子只有恆等，稱此排列 orbit 為普通類；否則稱特殊類。

**命題 5.4。** 870 個排列 orbit 中，814 個 stabilizer 平凡，56 個非平凡；後者進一步分成：stabilizer 大小 6 的 2 類、大小 3 的 8 類、大小 2 的 46 類。

先列出 stabilizer 的可能性。$S_3$ 的元素是恆等、一對互逆的 3-cycle、三個 transposition。含 3-cycle 的子群必含其逆；若再含任一 transposition，與該 3-cycle 合成便得到另外兩個 transposition，因此是整個 $S_3$。故唯一的三元素子群由兩個 3-cycle 與恆等組成。另一方面，每個 transposition $t$ 滿足 $t^2=id$，所以 $\{id,t\}$ 是二元素子群；兩個不同 transposition 的乘積是 3-cycle，因而也生成整個 $S_3$。所以 stabilizer 大小只可能是 $1,2,3,6$；大小 3 的只有一個，大小 2 的有三個。

**證明。** 先找被整個 $S_3$ 固定的排列。軸置換在七個活動位置上把位置分成三個 orbit：$\{0\}$、$\{1,2,4\}$、$\{3,5,6\}$。位置 0 必固定。若後兩個三元素集合各自保持不變，取其中任一位置 $a$；存在一個兩軸交換固定 $a$ 而交換該三元素集合中的另兩點。若排列 $p$ 與所有軸置換可交換，$p(a)$ 也必被同一交換固定；該集合中唯一被固定者就是 $a$，故逐點 $p(a)=a$，所以每組內只能是恆等。若兩組互換，同樣以「某點的 stabilizer」決定其在另一組的唯一對應點，得到唯一的互換 $i\mapsto 7-i$。故恰有 2 個排列被全群固定，也就是 2 個大小 1 的排列 orbit。

大小 3 的 stabilizer 只能是 $S_3$ 中唯一的三元素子群。某個 3-cycle 固定 18 個排列，其中 2 個已被全群固定，剩 16 個恰有大小 3 stabilizer。每 orbit 大小 $6/3=2$，所以有 $16/2=8$ 類。

大小 2 的 stabilizer 由某個 transposition 生成。每個 transposition 固定 48 個排列，扣掉全群固定的 2 個，剩 46 個。三種 transposition 的這些剩餘集合互不相交：若一排列同時被兩個不同 transposition 固定，兩者生成整個 $S_3$，它就應屬於前面那 2 個。故共有 $3\cdot 46=138$ 個排列的 stabilizer 大小 2；每 orbit 大小 $6/2=3$，所以有 $138/3=46$ 類。

其餘排列數

$$
5040-2-16-138=4884
$$

stabilizer 平凡，每 orbit 大小 6，故有 $4884/6=814$ 類。非平凡類合計 $2+8+46=56$。∎

因此

$$
\boxed{870=814+56.}
$$

### 5.5 方向軌道

若排列代表的穩定子大小為 $k\in \{1,2,3,6\}$，它作用在 729 個方向序列上。

**命題 5.5。** 對任意非恆等 $S_3$ 元素，以及被它固定的排列代表，固定的合法方向序列恰有 9 個。

**證明。** 分兩種元素型態。若是兩軸交換，位置作用含兩個 2-cycle。方向式可寫成 $o_{\phi (i)}=-o_i+c_i$。因固定排列滿足 $p\phi =\phi p$，而 $\chi (\phi (i))=\chi (i)$，所以 $c_i=\beta (\chi (i)-\chi (p_i))$ 在同一 $\phi$-cycle 上相同。在 fixed point 上方程為 $o=-o+c$，即 $2o\equiv c\pmod3$，對 $c=0,1,2$ 各有唯一解；每個 2-cycle 可自由選第一格的 3 種方向，第二格隨即唯一決定，兩個 cycle 共 $3^2=9$ 種。把全部固定方程相加可得總方向和自動為 0。若是三軸循環，位置作用含兩個 3-cycle；每個 cycle 上方向為 $a,a+c,a+2c$，首值 $a$ 有 3 種，兩個 cycle 共 9 種；每個 3-cycle 的三個方向和為 $3a+3c\equiv0\pmod3$，所以總和條件迫使唯一 fixed point 的方向為 0。∎

Burnside 因而給：

$$
\begin{array}{c|c}
|G_p| & \text{方向軌道數}\\\hline
1&729\\
2&(729+9)/2=369\\
3&(729+2\cdot9)/3=249\\
6&(729+5\cdot9)/6=129
\end{array}
$$

所以完整 $S_3$ 狀態 orbit 數為

$$
814\cdot729+46\cdot369+8\cdot249+2\cdot129
=\boxed{612\,630}.
$$

### 5.6 軌道編碼：`quotient_rank_from_meta()`

`n2_b8_pmeta[pr]` 的 5040 筆經完整枚舉驗證；其打包格式為：

$$
\texttt{meta}=8j+b,
$$

其中 $j$ 是排列 orbit 編號，$b$ 是把目前排列送到代表的 $S_3$ 變換。

#### 普通類

穩定子平凡時，送到代表的變換唯一；取變換後方向 rank $r$：

$$
C_3(s)=729j+r.
$$

`h48_common_base[j]` 直接存 $729j$。`ori_rank_after_sym(s,b)` 若要計算變換後新位置 `np` 的方向，必須先用 $\phi_b^{-1}$ 找回其舊來源位置；因此程式使用 `n2_b8_sym_inv[b]`，不是正向位置表。

#### 特殊類

排列固定後仍可由非平凡穩定子改變方向。令 $q=U_b(s)$，定義

$$
r_{\min}=\min_{h\in G_p}\operatorname{ori}(U_h(q)).
$$

**命題 5.6。** $r_{\min}$ 與最初選哪個 $b$ 無關。

**證明。** 若 $b,b'$ 都把排列送到同一代表，則 $U_{b'}U_b^{-1}$ 屬於代表排列的穩定子。從 $U_b(s)$ 枚舉整個穩定子與從 $U_{b'}(s)$ 枚舉整個穩定子只差群元素的重新排列，故得到相同方向集合與相同最小值。∎

**定義 5.7（bitset）。** 用一串 bits 表示有限集合：第 $r$ 個 bit 為 1 表示 $r$ 被選中，為 0 表示未選中。

代表方向不是 $0\ldots728$ 的連續區間，因此以 bitset 標記哪些 rank 是最小代表，再以

$$
\rho(r)=|\{j<r:B_j=1\}|
$$

壓成連續索引。

**命題 5.8。** 若代表 rank 依大小為 $r_0<r_1<\ldots<r_{t-1}$，則 $\rho(r_j)=j$；因此 $\rho$ 在代表集合上是一一對應到 $0,\ldots,t-1$。

**證明。** $r_j$ 前面恰有 $j$ 個代表 bit 為 1，所以定義中的計數正是 $j$。∎

`mask_rank()` 正計算此 $\rho$。

**定義 5.9（方向作用型態，action pattern）。** 對固定排列代表，穩定子在 729 個方向 rank 上造成的軌道分割方式，稱為此代表的方向作用型態。

56 個特殊排列 orbit 的方向作用經完整枚舉只有 13 種；`exception_action()`、`stabilizer_mask()` 與 13 組 bitset 均由同一枚舉驗證。

**定理 5.10。** `quotient_rank_from_meta()` 產生的 $C_3$ 滿足

$$
C_3(s)=C_3(t)\iff S_3\cdot s=S_3\cdot t.
$$

**證明。** 若兩狀態同一 $S_3$ orbit，它們的排列必落在同一排列 orbit。普通類中，把排列送到唯一代表後的方向因此相同；特殊類中，兩個結果只差代表排列的 stabilizer 元素，而命題 5.6 與 stabilizer-minimum 定義保證取到同一 $r_{\min}$ 與同一 $\rho(r_{\min})$。故 key 相同。反之，若 key 相同，基址區間先保證兩者使用同一排列代表；普通類的方向 rank 相同即得到同一完整代表，特殊類的相同 $\rho$ 對應同一 stabilizer 方向 orbit，因此兩者可由某個 $S_3$ 元素互相轉換。∎

各類基址取前綴和，因此 $C_3$ 連續覆蓋 $0,\ldots,612629$。

## 6. 自同構 $T$

$S_3$ 將 3,674,160 個狀態壓成 612,630 類；程式再使用另一個固定根圖自同構 $T$。

### 6.1 座標分解

找到角塊 6 所在活動位置 $j\in \{0,\ldots,6\}$ 與方向 $t\in \{0,1,2\}$，令

$$
q=3j+t\in\{0,\ldots,20\}.
$$

刪除該位置後，剩六個角塊 $0,\ldots,5$ 形成排列 $x\in S_6$；依第 4.1 節，$S_6$ 就是六元素的全部排列（在合成下亦為群）。再取剩餘方向中的五個自由值 $y=(y_0,\ldots,y_4)$；第六個由方向總和唯一恢復。

**命題 6.1（T 座標唯一性）。** 原 `WorkState` 與三元資料 $(q,x,y)$ 一一對應。

**證明。** 從合法排列中角塊 6 只出現一次，所以唯一得到位置 $j$ 與方向 $t$，故 $q=3j+t$ 唯一；刪掉該位置後依位置順序唯一讀出 $x,y$。反向時，$q$ 的除三商、餘數唯一恢復 $j,t$；把角塊 6 與六元素排列放回，再放回五個方向，最後由第 1 章的方向總和條件唯一恢復剩餘方向。兩方向互逆。∎

**定義 6.2（$\mathbb F_3$ 與仿射式）。**
令 $\mathbb F_3=\{0,1,2\}$，加、減、乘皆取模三，形成三元素域。此域上的五維向量記為 $\mathbb F_3^5$，矩陣運算定義如下。

對 $5\times5$ 矩陣 $A$ 與向量 $y$，

$$
(Ay)_i=\sum_{j=0}^{4}A_{ij}y_j\pmod3.
$$

映射 $y\mapsto Ay+b$ 稱仿射映射。兩個仿射映射合成為

$$
B(Ay+b)+c=(BA)y+(Bb+c).
$$

因此有雙射

$$
\mathcal X\longleftrightarrow\{0,\ldots,20\}\times S_6\times\mathbb F_3^5.
$$

T 的 orientation 部分因而可用 21 組固定仿射式描述。

### 6.2 $T$ 的定義與實作

對每個 $q$，T 由固定資料定義：

$$
q'=f(q),
$$

$$
x'_i=\tau(x_{R_q(i)}),
$$

$$
y'=A_qy+b_q,
$$

其中 $\tau$ 是交換 $(0,1),(2,3),(4,5)$ 的標籤置換。

程式資料：

```text
h48_t_dst[21]       q → q'
h48_t_perm_R[21×6] R_q
h48_t_ori_ctl[21]   A_q,b_q 的稀疏編碼
```

每個 orientation 輸出座標只有兩種形式：

$$
c+y_0+y_1+y_2+y_3+y_4,
$$

或

$$
c+2y_s.
$$

所以 `compact_T()` 不需一般矩陣乘法，只需小量加法、shift 與 `mod3_small()`。

### 6.3 $T$ 的對合性

**定義（對合）。**  
若 $T\circ T=\mathrm{id}$，稱 $T$ 為對合。

驗證器逐列確認固定 21 組表滿足：若 $q'=f(q)$，則

$$
f(q')=q,
$$

$$
R_{q'}\circ R_q=\mathrm{id},
$$

$$
A_{q'}A_q=I,
$$

$$
A_{q'}b_q+b_{q'}=0.
$$

**定理 6.3。** $T^2=\mathrm{id}$。

**證明。** 第一式恢復 $q$。對排列部分，固定表的第二式連同 $\tau^2=\mathrm{id}$ 使兩次來源重排與兩次標籤交換相消，故恢復 $x$。方向由第 6.1 節的仿射合成公式變成

$$
A_{q'}(A_qy+b_q)+b_{q'}
=(A_{q'}A_q)y+(A_{q'}b_q+b_{q'})=y.
$$

故三部分都恢復。∎

### 6.4 $T$ 的保邊性與局部 move 映射

對每個狀態 $s$，存在九 move 的一個排列 $\sigma_T(s)$ 使

$$
T(M_m(s))
=M_{\sigma_T(s)(m)}(T(s)).
$$

$\sigma_T(s)$ 隨狀態改變。`t_sigma_code(s)` 先找角塊 6 的位置，令其方向為 $t$，再算 `pr=perm_rank7(s->p)`，以

$$
idx=3\,pr+t\in\{0,\ldots,15119\}
$$

索引 `h48_sigma_pr_3bit`；六種 code 用三個 bit 表示，15,120 筆共 5,670 bytes，再加一個零值 guard byte，總長 5,671 bytes。跨 byte 的讀取證明見第 10 節。

**有限證書命題 6.4。** 上式對全部 $s\in \mathcal X$ 與九個 $m$ 成立，且 $T(e)=e$。

**證明方式。** 以密集 rank 枚舉全部狀態，逐一比較等式兩側的完整 `WorkState`；根另作直接檢查。完整檢查通過。∎

定理 6.3 給雙射，命題 6.4 給保邊與固定根，所以 $T$ 是固定根圖自同構。

T 的局部 move 映射須在當次狀態計算。

## 7. H48 正規化（canonicalization）

### 7.1 生成群

**定義 7.1（生成群）。**  
給群中的若干元素，所有由它們及其逆元素有限次合成所得元素，構成它們的生成群，記為 $\langle\cdots\rangle$。

令 $A=U_1$、$B=U_3$；$A,B$ 生成前章的 $S_3$。再定義

$$
H=\langle A,B,T\rangle.
$$

$A,B,T$ 都是固定根圖自同構，所以 $H$ 的每個元素也都是。由六個 $S_3$ 作用的有限合成表可直接核對 $A^2=\mathrm{id}$、$B^3=\mathrm{id}$；定理 6.3 給 $T^2=\mathrm{id}$。因此

$$
A^{-1}=A,
\qquad B^{-1}=B^2,
\qquad T^{-1}=T.
$$

所以雖然生成群定義容許生成元的逆，實際上只用正向字母 $A,B,T$ 的有限字串就已能表示全部生成元素。

### 7.2 48 個群元素

由第 3 章的 dense rank 雙射，`dense` 有唯一反函數；記為 $\operatorname{unrank}(v)$，也就是把密集編號 $v$ 唯一解回狀態。

對任一變換 $h$，用密集 rank 建立完整函數表

$$
L_h[v]=\operatorname{dense}(h(\operatorname{unrank}(v))).
$$

因 $dense/unrank$ 一一對應，兩個 $L_h$ 逐格相同當且僅當兩變換對全部狀態相同。

完整生成得到 48 個互不相同函數，而且對每個函數再接 A、B、T 仍落在這 48 個中。

**定理 7.2。** $|H|=48$。

**證明。** 48 個完整函數互異且皆由生成字串得到，所以 $|H|\ge48$。此集合包含恆等，且任一元素再合成 $A,B,T$ 仍在集合內；對生成字串長度歸納，所有生成字串都落在這 48 個函數中，故 $|H|\le48$。∎

### 7.3 八個 $S_3$ 右陪集

$S_3$ 是 $H$ 的六元素子群。由第 4.1 節的陪集分割性，右陪集 $S_3g$ 各有 6 個元素且彼此不交，所以 $H$ 恰被

$$
48/6=8
$$

個右陪集分割。

代表字**由左到右記錄執行順序**。例如 $A\,T$ 表示先做 A、再做 T，對應函數合成 $T\circ A$。

程式選八個代表字：

```text
R0 = I
R1 = T
R2 = A T
R3 = B T
R4 = T A T
R5 = T B T
R6 = A T B T
R7 = T A T B T
```

完整函數比較確認 $S_3R_i$ 共給 48 個互不相同元素，因此正好覆蓋 $H$。

`h48_len[]` 與 `h48_word[][]` 分別儲存代表字的長度與操作序列。

### 7.4 $H$ 的軌道與編碼

**定義 7.3（canonicalization）。** 對有限 orbit 選定一個全順序，取其唯一最小元素為 **canonical representative**；把任意元素送到該代表的程序稱 **canonicalization**。

第 5.6 節已為每個 $S_3$ orbit 選定代表，並以密集 $C_3$ 編號。H 層按這個編號排序，在八個候選中選最小 $C_3$；`perm_sym/stab_sym` 記錄把候選送到其 $S_3$ 代表的變換。

對 $S_3$ orbit 已有密集 key $C_3(s)\in \{0,\ldots,612629\}$。定義

$$
C_H(s)=\min_{0\le i<8}C_3(R_i(s)).
$$

**定理 7.4。**

$$
C_H(s)=C_H(t)
\iff
H\cdot s=H\cdot t.
$$

**證明。** 因 $H$ 是八個右陪集 $S_3R_i$ 的不交聯集，而乘積 $hR_i$ 對 $s$ 的作用是 $h(R_i(s))$，故 $H\cdot s$ 正是八個集合 $S_3\cdot R_i(s)$ 的聯集。故同 $H$ orbit 的狀態枚舉同一批 $S_3$ orbits，最小 $C_3$ 相同。反之，若最小值相同，由定理 5.10，某 $R_i(s)$ 與某 $R_j(t)$ 位於同一 $S_3$ orbit；相應 $S_3$ 元素與兩個代表皆在 H，故 $s,t$ 同 $H$ orbit。∎

**有限證書命題 7.5。** $H$ 在 $\mathcal X$ 上恰有 77,802 個 orbit。

**證明方式。** 對每個密集狀態列舉 48 個 H 像並取最小密集 rank；只在狀態本身等於該最小值時記一個 orbit，得到 77,802。獨立地計算 48 個群元素的固定點總數並套 Burnside 引理，也得到同一數字。∎

因此

$$
\boxed{|\mathcal X/H|=77\,802}.
$$

### 7.5 排列軌道的預先篩選

$S_3$ key 的資料布局是：每個排列 orbit 佔一段連續方向區間，整段依排列 orbit 編號遞增排列。因此若候選 $i$ 的排列 orbit 編號比候選 $j$ 大，則 $i$ 的任何完整 $S_3$ key 都大於 $j$ 的任何 key。

**命題 7.6。** 先在八個候選中找最小 permutation-orbit 編號，再只對這些候選計算完整 $S_3$ key，與對八個全算再取最小等價。

**證明。** 較晚排列 orbit 的最小 key 仍大於較早 orbit 的最大 key，所以不可能成為全域最小。∎

### 7.6 軌道編碼與變換記錄（frame）

`H48Canon`：

```c
typedef struct {
    uint32_t key;
    uint8_t rep;
    uint8_t perm_sym;
    uint8_t stab_sym;
} H48Canon;
```

$key=C_H(s)$ 只回答「是哪個 $H$ orbit」。另外三欄記錄本次將 $s$ 送到 canonical representative 的具體變換：

$$
g=U_{\texttt{stab\_sym}}
\circ U_{\texttt{perm\_sym}}
\circ R_{\texttt{rep}}.
$$

稱 `(rep,perm_sym,stab_sym)` 為 frame。frame 只記錄稍後搬回 canonical move 所需的變換。

## 8. 下降策略與完美雜湊

### 8.1 下降策略

**定義 8.1（策略）。**  
策略 $\pi$ 對每個非根狀態選一個 move。

若

$$
D(M_{\pi(x)}(x))=D(x)-1,
$$

稱為下降策略。

**定理 8.2。** 從距離 $d$ 的狀態反覆執行下降策略，恰 $d$ 步到根，且所得解最短。

**證明。** 由歸納，走 $k$ 步後距離為 $d-k$。到 $k=d$ 時距離 0，只能是根；之前距離仍正。距離定義排除任何少於 $d$ 步的解。∎

離線只為每個非根 H canonical representative 保存一個下降 move；runtime 先 canonicalize，再查此 move。

### 8.2 完美雜湊

**定義 8.3（雜湊與碰撞）。**  
雜湊函數把鍵映到有限的**槽位（slot）**。不同鍵映到同一槽位稱碰撞。為了分組計算，本程式先把鍵映到一個**桶（bucket）**，每個桶再查一個整數**位移（displacement）**決定最後槽位。若在指定有限鍵集合上沒有碰撞，稱該集合上的完美雜湊。

合法 H key 共有 77,802 個。`policy_lookup()` 的三十二位無號算術是

$$
x=k\oplus(k\gg13)\oplus(k\ll7),\qquad b=x\ \&\ (2^{14}-1),
$$

$$
y_0=k\oplus(k\gg7)\oplus(k\ll9),\qquad y=y_0\oplus(y_0\gg5),
$$

$$
a=(y\gg2)\ \&\ (2^{17}-1),\qquad
slot=(a+disp[b])\bmod2^{17}.
$$

其中 $\oplus$ 是逐 bit XOR，`&` 是逐 bit AND，`<<,>>` 是左右移；所有中間量按 `uint32_t` 保留低 32 bits。這些混合公式本身沒有一般定理保證無碰撞；「完美」是對目前 77,802 個合法 H key 的有限證書性質。

$2^17=131072$ 個 slot 每個只需 4-bit move，因此

```text
h48_policy_disp      16,384 bytes
h48_policy_used      16,384 bytes
h48_policy_prefix     1,024 bytes
h48_policy_dense     38,901 bytes
合計                 72,693 bytes（未計對齊）
```

131,072 是 slot 的範圍，只有 77,802 個 slot 被使用。新版以 used bitmap 和 prefix popcount 將 slot 轉成 dense rank，再用 dense rank 的奇偶選取 nibble；不再為未使用的 slot 保存策略值。

**有限證書命題 8.4。** 77,802 個合法 H key 映到 77,802 個互異 slot；每個被合法 key 使用的 slot 都保存其 canonical representative 的下降 move。

**證明方式。** 完整列舉合法 H key，檢查 slot 唯一；再對全部非根原狀態實際做 canonicalization、policy lookup、move lifting，驗證所得原 move 使精確 $D$ 減一。兩類檢查皆完整通過。∎

`policy_lookup()` 因而不需保存原鍵；其前置條件是輸入必須是合法 $C_H(s)$。

## 9. 將 move 搬回原座標（edge-label lifting）

### 9.1 局部 move 映射

對固定根圖自同構 $g$ 與狀態 $s$，保邊只保證「一條邊映成一條邊」。要把 move label 搬回，還需記錄哪個 label 變成哪個 label。

**定義 9.1（局部 edge-label map）。**  
若對每個 move $m$ 有唯一 move $\sigma_g(s)(m)$ 使

$$
g(M_m(s))
=M_{\sigma_g(s)(m)}(g(s)),
$$

則 $\sigma_g(s)$ 稱 $g$ 在 $s$ 的局部 edge-label map。

九個 move 在活動位置上的 `move_src` 排列彼此不同；因 `p[0..6]` 是七個互異角塊的排列，兩個不同來源排列不可能產生相同的 `p'`。故九個鄰居互異。$g$ 又是保邊雙射，所以每條 incident edge 的像有唯一 move label；因此 $\sigma_g(s)$ 是九元素排列，故可逆。

$S_3$ 的 $\sigma$ 只依變換本身；T 的 $\sigma_T(s)$ 依狀態。

### 9.2 代表狀態與原狀態的 move

假設 canonicalization 得

$$
c=g(s),
$$

而 policy 在 $c$ 選 move $a$。原狀態應選

$$
\boxed{m=\sigma_g(s)^{-1}(a).}
$$

**定理 9.2。** 若 $a$ 在 $c$ 上下降一層，則上式的 $m$ 在 $s$ 上也下降一層。

**證明。** 由定義，$g(M_m(s))=M_a(c)$。定理 2.1 給 $D(x)=d(x,e)$；定理 4.2 又給固定根自同構保持到根距離，所以 $D(g(x))=D(x)$。因此

$$
D(M_m(s))
=D(g(M_m(s)))
=D(M_a(c))
=D(c)-1
=D(s)-1.
$$

∎

### 9.3 映射合成與中間狀態

若先做 $g_1$ 再做 `g_2`，令 $s_1=g_1(s)$。則

$$
\sigma_{g_2\circ g_1}(s)
=
\sigma_{g_2}(s_1)\circ\sigma_{g_1}(s).
$$

**證明。**

$$
\begin{aligned}
g_2g_1(M_m(s))
&=g_2(M_{\sigma_{g_1}(s)(m)}(g_1(s)))\\
&=M_{\sigma_{g_2}(s_1)(\sigma_{g_1}(s)(m))}(g_2g_1(s)).
\end{aligned}
$$

比較定義即得。∎

T 的 code 必須在當次的中間狀態計算。

### 9.4 逆序搬回：`lift_policy_move()`

代表字 $R_i$ 最長包含 5 個操作。程式正向走代表字；每遇 T，就在當前 `cur` 呼叫 `t_sigma_code(cur)`，把局部 code 存入 `codes[]`。取得最後一個 code 後已不再需要狀態，因此省略最後一次狀態變換。

frame 的最後兩個 $S_3$ 變換先逆掉，再逆序走代表字：

```c
m = move_pullback[h->stab_sym][canonical_move];
m = move_pullback[h->perm_sym][m];
while (length != 0u)
    m = move_pullback[codes[--length]][m];
```

逆序來自第 4.1 節的合成反函數公式：合成的反函數順序相反。

**命題 9.3。** 只 pull back 被 policy 選中的一個 move，與先建立完整九元素 label permutation 再取該 move 的逆像相同。

**證明。** 函數合成在單一輸入 $a$ 的值可逐層計算；求 $f(g(a))$ 不需要先求其餘八個輸入。每層使用相同局部逆映射與相同順序，故結果相同。∎


## 10. Rank 壓縮與三位元讀取

完美雜湊先得到 $i\in[0,131072)$。令 $U[i]$ 表示該 slot 是否屬於合法 H key，並定義 $r(i)=\sum_{j<i}U[j]$。對 used slot 而言，這是從遞增 slot 到 $[0,77802)$ 的一一對應，因此把原本值依順序放入 dense array 後，查詢語意完全相同。任意整數 key 不在 accessor 的前置條件內。

每 512 bit（16 個 word）保存一次 prefix。取 $w=i\gg5$、$b=i\gg9$、$t=i\mathbin{\&}31$；rank 是 prefix[b]，加上本 block 已完成 word 的 popcount，再加目前 word 低 $t$ bit 的 popcount。最多掃十五個完整 word；$t=0$ 時直接加零，避免 shift 32。策略 byte 位址用 $r\gg1$，位移用 $4(r\mathbin{\&}1)$，最後 `&15`。**奇偶取自 dense rank，而不是 slot。**

T sigma 的第 $j$ 筆使用 $z=3j$，byte offset $q=z\gg3$，bit offset $t=z\mathbin{\&}7$。以兩個 unsigned byte 組成 $B[q]+256B[q+1]$，右移 $t$ 後 `&7`，恰好得到第 $j$ 筆的三個 bit。最後一筆從 byte 5669 的 bit 5 開始；byte 5670 的零值 guard 使統一讀取第二個 byte 仍合法，無須非對齊半字讀取。

`verify_packed.c` 使用獨立保留的 unpacked reference，檢查所有 15,120 筆 sigma、八種 bit offset、所有 dense policy 奇偶項、used bitmap 和 prefix。通過不代表任意不合法 key 也能查詢。

## 11. 一般下降迴圈的正確性

新版移除 sparse 路徑表。所有非已解輸入都執行 H48 正規化、查詢策略、依 frame 搬回 move、套用 move 的同一流程；距離一及十一也沒有捷徑。第一次重用已計算的排列 metadata 只省運算，不改策略。

令初始真實距離為 $d$。輸出 $k$ 步後維持 $D(s_k)=d-k$，而已輸出的 move prefix 確實將輸入變成 $s_k$。固定 root 的圖自同構保持距離，代表狀態的策略下降一，正確 frame lifting 將它變成原座標的一條下降邊。套用並輸出這一步後，不變量仍成立。到 $k=d$ 時距離為零且狀態已解；由直徑十一，十一個 byte 的 move buffer 足夠。任何解至少長 $d$，所以此解最短。

host 的完整 BFS 表只供驗證，不連結到 target。target 保存 H48 軌道上的下降策略，每次自行正規化與搬回 move。使用者已回覆老師同意此方法，記錄為「使用者回報取得同意」；尚未提供書面紀錄網址。這項方法同意不自動涵蓋課程的 AI 產出與個人作者要求。

## 12. 介面與證明依賴

`mod3_small` 的輸入限制為 $0..12$；排列排名要求合法排列；內部變換要求合法 WorkState 且輸出不覆蓋輸入。metadata、frame 必須對應同一個當前狀態，T 的局部映射也必須在正確的中間狀態取得。策略查詢要求合法 canonical H key。

公開 API 驗證七個排列 byte、六個獨立 twist，再展開成內部狀態。它拒絕重複、範圍錯誤、無效 move 及必要參數的 null。可選 statistics 可為 null，或只有 byte 對齊。move buffer 容量十一，另有長度 byte。證明鏈為：座標與 move → 真實 BFS 距離 → 固定 root 的 H48 → 策略下降 → packed accessor 等價 → frame lifting → 迴圈不變量與最短解。

## 13. 最優性範圍

保證的是 HTM 最短 move 數。六種固定長度 sigma 至少需要三個 bit，九種 move 加 root sentinel 至少需要四個 bit；這些局部下界不代表整個程式空間或指令數已達全域最小。H 有 48 個元素，也不代表每個 orbit 大小都是 48；stabilizer 使 orbit 數為 77,802。

## 14. 重新執行的完整驗證

10 月 8 日重新對全部 3,674,160 個合法狀態求解與回放，bad call、bad length、bad replay 均為零；該次 campaign wall time 為 7.4406 秒。獨立距離證書檢查 33,067,440 條有向邊、唯一零距離 root、相鄰距離差至多一與每個非 root 都有下降鄰居，得到 HTM 直徑十一、距離十一共 2,644 個。

H48 檢查得到 48 元素、八個六元素陪集、77,802 軌道，並驗證所有 3,674,159 非 root 經正規化、查詢和 lifting 都下降一。21 組 T affine 恆等式與全部資料表 accessor 也通過。新版沒有 runtime heuristic，所以 H1 記為不適用，改以 exact policy descent 說明；不能將它寫成已執行 heuristic admissibility 測試。

## 階段三：新版 C 與空間／時間權衡

最新提供的 `reference/n2_solver.c` 原樣保留，SHA-256 為 `8d356669f07a7d872f7a9a22322db60fc2630bd075fe41297842356df5bc67cc`。全部 generated tables 先驗證再連結。排列 metadata 省去每輪六次完整排列正規化；穩定子 bit mask 做方向 orbit rank；八個右陪集代表取代 48 個完整變換；排列 class 的預先篩選避免不必要的方向處理。正確性建立在前文 orbit／保邊證書，不假设每個 orbit 等大。

rank policy 相較原 81,920 bytes 減少 9,227 bytes，但增加最多十五個 word 的 popcount。T sigma 三位元相較 7,560 bytes 減少 1,889 bytes。移除 sparse key/code 陣列就減少 21,224 bytes，另有舊 decoder 也移除。這些是 payload 比較；不是整個記憶體總量。

每張連結表的 bytes 如下（symbol 名稱故意保留英文以對照程式）：

| Linked table symbol | Payload bytes |
| --- | --- |
| n2_b8_sym_inv | 6 |
| h48_t_dst | 21 |
| n2_b8_exc_aid | 28 |
| n2_b8_sym_pos | 48 |
| n2_b8_move_delta | 72 |
| n2_b8_move_src | 72 |
| h48_t_ori_ctl | 84 |
| h48_t_perm_R | 126 |
| h48_exc_base | 224 |
| h48_policy_prefix | 1024 |
| n2_b8_sym_twist | 1152 |
| n2_b8_action_mask | 1196 |
| h48_common_base | 3256 |
| h48_sigma_pr_3bit | 5671 |
| n2_b8_pmeta | 10080 |
| h48_policy_disp | 16384 |
| h48_policy_used | 16384 |
| h48_policy_dense | 38901 |
| Total named generated tables | 94729 |


總 named payload 是 **94,729 bytes**。`.rodata` 還有訊息與 helper 常數；`.text`、`.bss`、padding、stack、MMIO 均另計。

RV32I 無乘除餘数指令。索引用 shift/add，例如 $3j=2j+j$、$35y=32y+2y+y$；renderer 直接讓 row pointer 加 140 bytes，免掉逐 pixel 乘法。排列 rank 用小型 popcount 表，word rank 用 SWAR `popcount32`，都只含 shift、mask、add。載入使用 unsigned byte；三位元 sigma 用兩次 byte load 避免非對齊 halfword。

target isolated kernel 用相同 driver、checksum 比較模三分支與無分支，以及 dense nibble 和 byte：

| Isolated kernel | .text | Table bytes | ISS iret | 5S iret | 5S cycles |
| --- | --- | --- | --- | --- | --- |
| mod3_branch | 104 | 0 | 54009 | 54008 | 78014 |
| mod3_branchless | 104 | 0 | 57009 | 57008 | 75014 |
| dense_packed | 104 | 38901 | 1011437 | 1011436 | 1167044 |
| dense_byte | 88 | 77802 | 700229 | 700228 | 933638 |


模三測試讓 0..4 每個值重複一千次：有分支 ISS 少 3,000 條指令，無分支 5S 少 3,000 cycles。這只是 kernel 結果；整個 solver helper 的 $0..12$ 範圍另有證明，沒有宣稱直接換掉後整體會快相同比例。

packed policy 每筆多四條退休指令，換得 38,901 bytes。若把 GUI policy 展成 byte，總空間約 143,313 bytes，尚未考慮 code/padding 改變就超出 131,072。host 16M 次 random access、五次中位數為 packed 0.016 s、byte 0.015 s；毫秒 timer 太粗，不作強烈 native 速度結論。最簡實作的意思是控制完整資源需求，並接受有量測支持的 bounded lookup 成本。

## 階段四：RV32I、LED 與完整 pipeline 教學

### 原始碼、ABI 與輸入

`target/solver_rv32.S` 是核心，`target/runtime.S` 是 driver／LED，`target/rv32.ld` 是連結與 stack 配置。使用 GNU-built ELF 才是經驗證的 Ripes 路徑；flat `.s` 供檢查，沒有宣稱 GUI 直接組譯它也通過。

`n2_solve` 的 a0–a3 為 state、moves、count、optional stats 指標，a0 回傳成功值。callee-saved registers 恢復，stack 以十六 bytes 對齊。manual 最大 call path 是 driver 32 + solve 80 + canonicalizer 192 + quotient 64 + mask rank 32 = **400 bytes**；GCC 是 **512 bytes**。使用 linked call graph 得到保守界限且拒絕 recursion。d11 core 實測 high water 368，加 driver 為 400。`sp` 指向連續保留區的頂端；renderer 是 leaf，在求解結束後執行，沒有和深層求解 stack 同時疊加。

14 字元輸入為七個 1-based permutation digits 加七個 1-based orientation digits，後面 NUL。七個 twist 都先驗證 sum modulo 3，才捨棄 dependent twist。upstream 的 index 0..6 對應 candidate `[3,1,5,2,0,4,6]`，position 和 cubie labels 用同一映射。move 0/1/2 是 R'/R2/R，3/4/5 是 D'/D2/D，6/7/8 是 B'/B2/B。半轉在 HTM 算一步。

要換輸入，改 runtime 的 `input_string` 並將 `EXPECTED` 設為 oracle 距離；不知道距離可用 255，只驗證回放和十一界限。封裝預設 `21345671111111`，EXPECTED=11。benchmark 對相同 ELF 的 input/expected bytes 做固定位置 patch，不為不同 case 改演算法。

### 完整記憶體統計

| Program | .text | .rodata | .bss | Reserved stack | Padding | Loaded span | Span + LED |
| --- | --- | --- | --- | --- | --- | --- | --- |
| solver_cli | 4776 | 95240 | 40 | 400 | 8 | 100464 | 103964 |
| gcc_reference | 5052 | 95264 | 40 | 512 | 12 | 100880 | 104380 |
| solver_gui | 5136 | 95324 | 40 | 400 | 12 | 100912 | 104412 |
| vectors | 4704 | 95708 | 40 | 400 | 12 | 100864 | 104364 |
| pipeline_demo | 468 | 72696 | 4 | 32 | 0 | 73200 | 76700 |


全部 `.data=0`。課程 static data：CLI **95,280**、GUI **95,364 bytes**。JSON 舊欄位 `static_data` 包含所有 allocated non-executable sections，也包括 `.stack`；看課程定義時應使用 `course_static_data`。你要求的 GUI 整體總量為 **104,412 bytes**，含 LED 的 3,500 bytes，距 128 KiB 剩 **26,660 bytes**。加的是實際配置 span 與 MMIO，不把 RAM 到 `0xf0000000` 間未配置的地址洞當記憶體；simulator host overhead 也另列，不混入 guest budget。

`.bss` 40 bytes = input13 + moves11 + replay13 + count1 + padding2。LED helper 僅 84 bytes = sticker slots24 + corner colors24 + RGB24 + offsets12。沒有第二張 framebuffer、每幀 snapshot、frame counter 或 busy wait。400-byte stack、所有 alignment、code 和表都已納入。linker assertion 與 build 檢查會阻止未來超出完整上限。

### 所有最深層案例與效能結論

| Implementation | Cases | Minimum iret | Mean iret | Maximum iret |
| --- | --- | --- | --- | --- |
| solver_cli | 2644 | 61829 | 67174.832 | 84164 |
| gcc_reference | 2644 | 64028 | 69392.088 | 84114 |


2,644 個 d11 全部在 Ripes ISS 內驗證長度及實際回放，renderer 關閉，每個案例都是 fresh process；指令數含 parse、solve、replay、print、exit。最差 84,164 是五千萬的 **0.168328%**。平均比 GCC 少 **3.195%**，2,628 次贏、0 次平、16 次輸；manual `.text` 4,776、GCC 5,052，少 276 bytes。兩邊最大值不一定來自同一個輸入。

官方 vector 另列：manual ISS **65,617**、GCC **67,829**；實際十一解為 `B' R D R B2 R B D2 B D R`。GUI 開 LED 的 5S 為 **89,444 iret／113,245 cycles**，PASS 與 exit0。不同 processor／renderer 配置不要直接用 GUI 數字當課程 threshold。

較慢的十六個輸入全部公開：

| Dense rank | Input | Manual iret | GCC iret | Manual excess |
| --- | --- | --- | --- | --- |
| 136082 | 74165231131313 | 83300 | 83103 | 197 |
| 272169 | 36725412111212 | 83311 | 83117 | 194 |
| 136100 | 74165233131311 | 82793 | 82669 | 124 |
| 272170 | 36725412121211 | 82778 | 82662 | 116 |
| 136127 | 74165233132313 | 80739 | 80642 | 97 |
| 272161 | 36725411121212 | 82496 | 82399 | 97 |
| 135614 | 74165233131113 | 82577 | 82490 | 87 |
| 272176 | 36725412121232 | 80646 | 80572 | 74 |
| 136098 | 74165233111313 | 82402 | 82333 | 69 |
| 272332 | 36725412321212 | 83055 | 82986 | 69 |
| 272139 | 36725411313131 | 84164 | 84114 | 50 |
| 136103 | 74165233131323 | 80445 | 80406 | 39 |
| 271927 | 36725412121112 | 82136 | 82107 | 29 |
| 135705 | 74165231212121 | 83974 | 83952 | 22 |
| 272224 | 36725412123212 | 82752 | 82734 | 18 |
| 136181 | 74165233231313 | 82792 | 82775 | 17 |


後面的 dynamic profile 已逐一量化十六個逆轉，按 linked symbol 區間記錄並核對 Ripes 全程指令數。這些輸入的 transform 在 manual 花較多指令，其他 routine 抵銷大部分差距；GCC inline 使 source-level 歸屬不能直接等同。完整 CSV 和 profile 同時保留贏與輸的證據。

host 全域 H3、表完整性 H2、packed H4 均通過。沒有 heuristic，所以 H1 不適用；accepted exact-policy 使用全域下降證書。target T5/T6 通過，T7 對三種必需案例及擴充到 32 個 selected vectors 同時跑 ISS 和 forwarding/hazard detection 5S。獨立 local RV32 interpreter 另外檢查 6,859 API calls、invalid/null、byte-aligned stats、callee-saved registers、全部 d11 及 1,281 個 stratified inputs；它是補強證據，不能冒稱 Ripes。

### LED 的最簡資料流

I/O 加一個 LED Matrix，Width=35、Height=25。程式使用 `LED_MATRIX_0_BASE/WIDTH/HEIGHT` 符號，GNU ELF 綁定觀察到的 base `0xf0000000`。地址 $base+4(35y+x)$ 放 `0x00RRGGBB`；實際是 row-major，UI 說明中的 column-major 有誤。

U/L/F/R/B/D 起點分別 `(9,0)/(0,7)/(9,7)/(18,7)/(27,7)/(9,14)`。sticker4×3、face8×6，中間一行／列分隔，底部剩五行。RGB 為白 FFFFFF、橘 FF8000、綠 00D060、紅 FF2020、藍 2080FF、黃 FFFF00。角塊三張 sticker 的排列由 twist 控制；dependent 第七個 twist 每 frame 算一次，第八固定角為零。

啟動時 `led_clear` 清除 875 words 一次。每 frame `render_cube` 看24 stickers，每張用四個 unrolled stores ×三行；row pointer 每行加140。求解後先畫初始狀態，再以輸出 move buffer 呼叫 `n2_apply_move`，每步畫一次，十一解共十二幀。沒有儲存預錄動畫；畫圖不改 logical state；最後求解狀態檢查成功才印 PASS。

`led_geometry.json` 用獨立 geometric transform 檢查216種 distinguished-sticker 轉動，並檢查實際 RV32 執行十二幀的像素範圍、顏色數與終態六面同色。`gui_complete.jpg` 和 `led_final_detail.jpg` 是實際 Ripes 圖。Fast Run 會讓中間畫面很短，但每步 MMIO store 與獨立驗證都存在。

### IF、ID、EX、MEM、WB

IF 依 PC 讀四 bytes instruction，計算 PC+4，PC mux 選一般前進或 EX redirect；IF/ID 保存 instruction、PC、valid。ID decode rs1/rs2/rd、立即數和 controls，讀 register file，ID/EX 保存 operands 與 controls。EX 先 forwarding，再經 ALU mux 選 PC/REG1 與 IMM/REG2，做算術、有效地址或 branch compare／target。MEM 按控制 load/store，把地址、資料、結果傳往 MEM/WB。WB 依 mux 選 ALURES、MEMREAD 或 PC4，在 RegWrite=1 時寫 rd；x0 永遠是零。valid、enable、clear 區別真正指令、暫停與 bubble。

| 指令 | ALU 輸入／工作 | MemRead / MemWrite | RegWrite / WB mux | PC mux |
|---|---|---|---|---|
| add、logic、shift、compare | forwarded operands 或立即數 | 0 / 0 | 1 / ALURES | PC+4 |
| auipc | PC + upper immediate | 0 / 0 | 1 / ALURES | PC+4 |
| lui | upper immediate，rs1 不使用 | 0 / 0 | 1 / ALURES | PC+4 |
| lbu/lhu/lw | rs1+offset | 1 / 0 | 1 / MEMREAD | PC+4 |
| sb/sh/sw | rs1+offset；forwarded rs2 作 store data | 0 / 1 | 0 / 不使用 | PC+4 |
| branch | PC+B-immediate；另有 operand comparator | 0 / 0 | 0 / 不使用 | taken 選 target |
| jal/jalr | PC 或 forwarded rs1 加立即數 | 0 / 0 | 1 / PC4；x0 忽略 | EX redirect、清掉 younger stages |
| ecall | 等先前 register writes 完成 | 0 / 0 | 0 | a7=93、a0=status 結束 |

forwarding 優先選符合且 enabled 的 MEM destination，其次 WB；x0 不產生 dependency。ALU 結果可直接供下一個 EX。load 結果來不及供緊接的 EX consumer，因此 load-use hazard 讓 PC 和 IF/ID hold 一 cycle，clear ID/EX 插入 bubble，較老 MEM/WB 仍前進。下一 cycle 用 WB forwarding 得到 load value。taken branch/jump 在 EX resolve，清掉更年輕的錯路指令；ecall 要等先前 writes 排空，才讀到正確 a0/a7。

### 真實 policy lookup 的 pipeline 放大實驗

`pipeline_demo.S` 呼叫從 production 精確抽出的 `policy_lookup` 和 `popcount32`，抽取時記錄 source SHA。輸入 H key 89011，是六步例子的代表 key，讀到代表 move3；完整 solver 的 frame `(4,2,0)` 會把它搬成 candidate move6。demo 只隔離 lookup 與 memory dependency，沒有宣稱自己跑了完整 canonicalizer。

接著 `sw a0,0(t1)` 把3的四 bytes 寫入 `pipeline_result`，`lw t2,0(t1)` 讀回3，`add t3,t2,t2` 得到6，assert後以exit0結束。store 的 MemWrite=1、RegWrite=0；load 的 MemRead=1、WB mux=MEMREAD；add 的 RegWrite=1、WB mux=ALURES。相依 load-use 插入一 cycle bubble，之後轉送3，解釋重疊執行下結果仍正確。

實際 Ripes 5S 計數 **514 iret、616 cycles**。記錄前 Edit → Settings → Max. pipeline diagram cycles 設1000，使用 Auto clock 或逐次 Clock；Fast Run 不保留這個 history。`pipeline_gui.tsv` 直接由 GUI Copy 匯出，`report_en.html` 的互動 viewer 以真實 trace 顯示每一 cycle 的五階段。詳細 hazard cycle 及圖另列在 pipeline evidence；旧59-cycle示範已淘汰。控制表來自 pinned Ripes wiring，不能只由總 elapsed time 猜 signal。

### 重現步驟與繳交紀錄

封裝目錄以 PowerShell 執行：

```powershell
.\Environment.ps1
.\Run-Lab.ps1 -Action Build
.\Run-Lab.ps1 -Action Check
.\Run-Lab.ps1 -Action Measure
.\Run-Lab.ps1 -Action Benchmark
.\Run-Lab.ps1 -Action Gui
```

Environment 會找固定版本並核對 archive hash；可設 N2_PYTHON、N2_RV_GCC、N2_RIPES，host tests 另需 native GCC/G++。Check 包含所有 host oracle、Ripes vectors、LED、ISA 和 stack；Measure 跑雙方全部 d11；Benchmark 跑環境及 isolated kernels。GUI 選RV32I的5S、關M/C、以Executable ELF載入 `build/solver_gui.elf`。

`requirements_audit.md` 是最新要求對照，`source_review.md` 區別全文、部分與受阻連結，`development_record.md` 記錄真实修改與AI範圍，`submission_record.md` 保存公開fork、HackMD revision、tag、接受信與面試狀態。這些 external 記錄沒有證據就不填「完成」。老師同意H48已納入；課程另要求assembly、measurement、analysis為學生本人，這份AI工程參考不冒充個人作業。英文版可供自行理解、重作及核實後按老師同意範圍使用。

### 實際 load-use 週期與控制訊號

GUI trace 有 0 到 616 共 617 欄；初始欄是 cycle 0，因此 clock count 為 616。117 個指令 row 均已解碼並對上目前 ELF 同一個 PC 的 instruction word，重新跑 CLI 也確認 5S 為 514 iret、616 cycles、exit0。

| Cycle | IF | ID | EX | MEM | WB | Held |
| --- | --- | --- | --- | --- | --- | --- |
| 603 | 0x1030 add x28 x7 x7 | 0x102c lw x7 0 x6 | 0x1028 sw x10 0 x6 | 0x1024 addi x6 x6 -596 | 0x1020 auipc x6 0x12 | — |
| 604 | 0x1034 addi x29 x0 6 | 0x1030 add x28 x7 x7 | 0x102c lw x7 0 x6 | 0x1028 sw x10 0 x6 | 0x1024 addi x6 x6 -596 | — |
| 605 | 0x1034 addi x29 x0 6 [held] | 0x1030 add x28 x7 x7 [held] | bubble / empty | 0x102c lw x7 0 x6 | 0x1028 sw x10 0 x6 | 0x1030 add x28 x7 x7; 0x1034 addi x29 x0 6 |
| 606 | 0x1038 bne x28 x29 16 | 0x1034 addi x29 x0 6 | 0x1030 add x28 x7 x7 | bubble / empty | 0x102c lw x7 0 x6 | — |
| 607 | 0x103c addi x10 x0 0 | 0x1038 bne x28 x29 16 | 0x1034 addi x29 x0 6 | 0x1030 add x28 x7 x7 | bubble / empty | — |
| 608 | 0x1040 addi x17 x0 93 | 0x103c addi x10 x0 0 | 0x1038 bne x28 x29 16 | 0x1034 addi x29 x0 6 | 0x1030 add x28 x7 x7 | — |
| 609 | 0x1044 ecall | 0x1040 addi x17 x0 93 | 0x103c addi x10 x0 0 | 0x1038 bne x28 x29 16 | 0x1034 addi x29 x0 6 | — |


**604**：lw 在 EX、相依 add 在 ID。hazard unit 比對 rs1/rs2 與 EX load destination，將 hazardFEEnable=0、hazardIDEXClear=1，準備下一個 edge 的暫停與 bubble。**605**：IF/ID 以「-」顯示 held，EX 是 bubble，lw 到 MEM；此時 EX 不再有 load，前端可恢復。**606**：lw 到 WB，其值 3 同時 forwarding 到 add 的兩個 EX operands；結果 6 在 **608** 到 WB。

0x1028 的 sw 在 604 的 MEM 將 `03 00 00 00` 寫入 0x12dcc，MemWrite=1、RegWrite=0；到 605 雖佔 WB stage，仍不寫 register。0x102c 的 lw 為 MemRead=1、RegWrite=1、rd=x7、WB mux=MEMREAD。0x1030 的 add 為 RegWrite=1、rd=x28、WB mux=ALURES。add 用 forwarding 的有效值，不是先前 ID 讀到的舊 register 值，程式 assert 結果六後 exit0。

0x101c 的 bne 起初曾被 speculative fetch，隨前面的 call redirect 清除；真正執行是在 IF598、ID599、EX600、MEM601、WB602。static row 可包含多次 dynamic 經過；是否退休還要看 valid/clear。

互動 HTML 的五階段位置来自真實 GUI export；控制值則依 instruction 與 pinned Ripes wiring 解釋，沒有冒稱是即時讀取 GUI ports。既有截圖保存真實完成畫面。後續 native UI refresh 因先前 Esc stop 被 automatic approval review 拒絕，沒有捏造新的 port 截圖。

### 十六個落後案例的實際 profile

獨立 RV32 interpreter 對每個落後輸入跑完整 manual 和 GCC 程式，記錄執行 PC；到 exit 的 instruction count 加上 pinned ISS 實測固定的一個 finalization 差，全部對上原 Ripes 數字。以下按 linked symbol 區間歸屬；compiler inline 會改變工作屬於哪個 symbol，不把區間直接當成完全同構的 source-level call。

| Dense rank | Manual compact_T | GCC compact_T | Manual symmetry_apply | GCC symmetry_apply | Whole-program excess |
| --- | --- | --- | --- | --- | --- |
| 135614 | 26942 | 22893 | 15136 | 13640 | 87 |
| 135705 | 27455 | 23319 | 15480 | 13950 | 22 |
| 136082 | 27162 | 23065 | 15480 | 13950 | 197 |
| 136098 | 27153 | 23066 | 14792 | 13330 | 69 |
| 136100 | 27116 | 23036 | 15136 | 13640 | 124 |
| 136103 | 25637 | 21785 | 14792 | 13330 | 39 |
| 136127 | 25881 | 21976 | 14792 | 13330 | 97 |
| 136181 | 26979 | 22928 | 15136 | 13640 | 17 |
| 271927 | 26911 | 22867 | 14792 | 13330 | 29 |
| 272139 | 27615 | 23450 | 15480 | 13950 | 50 |
| 272161 | 27212 | 23107 | 14792 | 13330 | 97 |
| 272169 | 27208 | 23108 | 15480 | 13950 | 194 |
| 272170 | 27070 | 23000 | 15136 | 13640 | 116 |
| 272176 | 25832 | 21943 | 14792 | 13330 | 74 |
| 272224 | 26989 | 22934 | 15136 | 13640 | 18 |
| 272332 | 27193 | 23096 | 15136 | 13640 | 69 |


dense135614：manual compact_T 為26,942、GCC22,893，symmetry_apply為15,136對13,640。排名、canonicalization、replay 等節省抵銷大部分額外 transform 成本，但全程仍多87。每個落後輸入都有同樣的細項，完整其他區間見 loss_profiles.json。保留十六個小幅落後是目前取捨；平均指令、code size 與最差門檻仍達標。

### 真正執行 renderer 的驗證

除了216個 distinguished-sticker 幾何檢查，獨立 RV32 interpreter 實際執行目前 GUI ELF，每次 render_cube 返回後將875個 pixel逐一與獨立幾何期待值比較，十二幀全部一致。啟動清空875 stores，加上十二次各288 stores，總共 **4,331 次 MMIO stores**，全部 word 對齊且在3500-byte範圍內；renderer 不修改 replay logical state。離線 viewer 的像素是這次核對過的執行紀錄，不是 target 預錄動畫。

EXPECTED 用 signed lb，255變成-1。未知距離模式以 solved、depth6、depth11 在manual/GCC及ISS/5S共十二次實際跑過；此模式驗證回放與十一界限，已知距離模式仍要求長度等於oracle。unknown_input_mode.json保存紀錄。

### 真實版本演進與待完成的人工作業

10月6日舊版靠 whole-path shortcut，官方vector為4,518iret、d11平均4,517.207、最差4,565，CLI.text5364、course static128240。這是不同演算法，不能當成新版同條件效能；新版主動花更多運算以移除特殊路徑表、縮小完整空間。現在CLI.text4776、d11平均67174.832、最差84164，完整GUI104412。舊原包與紀錄保存在active deliverable以外。

本次整合、分析與測量由AI完成，沒有捏造學生的commit、三次revision或獨立實驗。技術工程可本機完成；學生本人要求的產出／額外老師授權、真實反思、公開fork/tag、HackMDrevision、表單accepted信與現場面試仍不能由這份封裝代替。詳見development_record.md及submission_record.md。

## 來源與 AI 揭露

最新版要求：[Assignment1](https://hackmd.io/@sysprog/2026-arch-homework1)、[AI guidelines](https://hackmd.io/@sysprog/arch2026-ai-guidelines)、[Lab1](https://hackmd.io/@sysprog/H1TpVYMdB)。原版：[minirubik](https://github.com/sysprog21/minirubik)與report。架構：[RV32I specification](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html)、[assembly manual](https://github.com/riscv-non-isa/riscv-asm-manual)、[Ripes pinned source](https://github.com/mortbopet/Ripes/tree/5b8a616)、VSRTL memory。數學背景：Jaap Pocket Cube、MathWorld Cayley Graph、Korf1997；H48 特定構造以本教材推導和完整有限證書為依據。

Codex做本次整合、RV32I port、翻譯、工程分析、agent-run measurement及資料來源核對。使用者做的已知選擇為balanced新版本、整體空間上限、最簡LED與回報老師同意H48。沒有捏造個人作者、學生獨立測量、歷史revision或繳交accepted。
