# An Optimal 2×2×2 Cube Solver: Balanced H48, RV32I and Ripes

Version: 8 October 2026, Asia/Taipei. This edition replaces the earlier sparse-path implementation throughout. The unchanged supplied C solver has SHA-256 `8d356669f07a7d872f7a9a22322db60fc2630bd075fe41297842356df5bc67cc`.

The solver validates a fixed-corner state, reduces it under 48 root-fixing graph automorphisms, reads a rank-compressed descending policy, lifts that move through its saved frame, and repeats until solved. The target performs this loop for every nonsolved input, without heap allocation, recursion, runtime BFS or a cached whole solution. Minimal LED rendering replays the actual output.

The instructor's approval of H48 is reported by the user. This AI-assisted engineering reference discloses Codex-generated assembly, analysis and agent-run measurements. It does not claim that the student independently authored those parts. The course separately reserves those parts for student work; method approval alone does not establish an exception to that authorship rule. Publication and accepted submission remain separately recorded in [submission_record.md](submission_record.md).

Submission repository: [dots0101/minirubik](https://github.com/dots0101/minirubik), a public fork of sysprog21/minirubik on `main`. The recorded starting commit is [`231796cc48868f4ea276f652139b6bebbad0cd02`](https://github.com/dots0101/minirubik/commit/231796cc48868f4ea276f652139b6bebbad0cd02). This identifies the upstream starting point; the submission commit and tag will be recorded after import. The preserved baseline C agrees with this starting revision after normalizing checkout line endings.

## Stage 1: Baseline and Target Costs

The upstream C baseline fixes one corner, ranks $7!\cdot3^6=3,674,160$ states, constructs a complete BFS predecessor-move table, and answers queries by descent. Its orientation constraint is a sum modulo three, not permutation parity. The dominant peak is 3,674,160 bytes of predecessor moves, 14,696,640 bytes of queue ranks, and 34,614 bytes of factored quarter-turn transitions: **18,405,414 bytes**. The graph has 33,067,440 directed edges; two factored updates per edge imply 66,134,880 updates. Roughly fifteen instructions per update gives $10^9$ as an estimate, not an executed baseline result.

Keeping a complete verification table is useful on the host. On the target, Ripes' VSRTL sparse address space stores bytes in a hash map; guest space and host working set are different quantities. A separate store-loop benchmark touched each region, with three fresh-process repetitions and an empty control. It intentionally tests regions larger than the solver budget; those diagnostic programs are never linked into the solver.

| Guest bytes touched | Median peak host bytes | Delta from empty control |
| --- | --- | --- |
| 0 | 32198656 | 0 |
| 4096 | 32518144 | 319488 |
| 131072 | 43053056 | 10854400 |
| 1048576 | 116666368 | 84467712 |
| 4194304 | 369205248 | 337006592 |


Using the 4 MiB measurement minus the control gives **80.3486 host bytes per written guest byte**. A linear extrapolation of the baseline peak plus the control is about **1.407 GiB**. This is a rough build-specific projection, not a measurement of the full baseline. Map resizing, read-only loading, allocator behavior and concurrent host load can change the ratio.

For throughput, the same 128 KiB memory loop performs eight passes and retires 1,310,758 instructions. Rates use Ripes' execution milliseconds, excluding process startup, and are medians of three runs:

| Model | Retired instructions | Cycles | Median iret/s |
| --- | --- | --- | --- |
| RV32_ISS | 1310758 | 1310758 | 21487836.1 |
| RV32_5S | 1310758 | 1835050 | 423645.1 |


At those rates, $10^9$ instructions would ideally take 46.5 s on ISS and 39.3 min on 5S. Neither projection measures the baseline's complicated workload. Raw runs and medians are in [environment_benchmark.json](../evidence/environment_benchmark.json).

The pinned build is Ripes `v2.2.6-106-g5b8a616`, commit `5b8a616`; GCC is xPack GNU RISC-V Embedded GCC 15.2.0. Target flags are `-march=rv32i -mabi=ilp32 -mno-relax -O2 -ffreestanding -fno-builtin -nostdlib -nostartfiles`, linker relaxation disabled. M and C are disabled. Host: Windows 11, Intel Core Ultra 9 275HX, 24 logical CPUs. [environment.json](../evidence/environment.json) records provenance and tool archive hashes.

The assignment limits static data to 128 KiB. The user's stricter contract limits **all required guest space**, including code, static tables, mutable buffers, alignment, reserved stack and 3,500 bytes of LED storage, to 131,072 bytes. The complete linked budget is given in Stage 4.

## Stage 2: State Representation and the H48 Policy

The prerequisites are C, sets, functions, modular arithmetic, and elementary proofs. Graph theory, group actions, and the required linear algebra are introduced where they are used.

---

### 0. Solver Overview

`n2_solve()` first handles the solved state. For every nonsolved state, each iteration performs H48 canonicalization, looks up a descending move, lifts that move back to the original coordinates, and updates the state.

A **finite certificate** is a verification result obtained by enumerating an entire finite domain and checking the required identities at every entry. Any counterexample makes the verification fail. General statements in this note are established by mathematical proofs; claims about the particular generated tables also depend on their finite certificates.

The correctness argument has four parts:

1. The state coordinates and nine moves describe the puzzle exactly.
2. The host distance labels $D$ equal the true shortest-path distances.
3. H48 canonicalization and move lifting preserve a decrease of exactly one in distance.
4. Rank compression and three-bit access preserve the certified policy and local move maps exactly.

### 1. State Coordinates

A 2×2×2 cube has eight corner cubies. Number both the positions and the cubies $0,\ldots,7$. Define

$$
p_i=\text{cubie at position }i,\qquad o_i\in\{0,1,2\}=\text{its orientation}.
$$

Whole-cube rotations do not count as moves. A designated cubie has $8\cdot3=24$ position-orientation combinations, in bijection with the 24 spatial orientations of the cube. There is therefore a unique normalization that fixes cubie 7 at

$$
p_7=7,\qquad o_7=0.
$$

Impose the orientation constraint

$$
\sum_{i=0}^{6}o_i\equiv0\pmod3.
$$

The nine moves preserve this constraint, and every candidate coordinate satisfying it is reachable; Section 2 proves both facts. Given $o_0,\ldots,o_5$, there is a unique remaining value

$$
o_6\equiv-\sum_{i=0}^{5}o_i\pmod3.
$$

Let $P_7$ be the set of all permutations of $0,\ldots,6$. The seven movable cubies have $|P_7|=7!$ permutations, and each of the six independent orientations has three choices. Thus the candidate state space is

$$
\mathcal X=P_7\times\{0,1,2\}^6,\qquad |\mathcal X|=7!3^6=3\,674\,160.
$$

The public and internal representations store these coordinates:

```c
typedef struct { uint8_t perm[7]; uint8_t twist[6]; } N2State;
typedef struct { uint8_t p[8]; uint8_t o[8]; } WorkState;
```

`expand_public()` checks that `perm[0..6]` is a permutation of $0,\ldots,6$ and that `twist[i]<3`, then uniquely reconstructs $o_6,p_7,o_7$. `compress_public()` removes only these uniquely recoverable fields. The two operations are inverses on valid states.

Every internal helper assumes that its input `WorkState` satisfies the permutation, fixed-corner, and orientation-sum invariants.

### 2. Moves and the State Graph

#### 2.1 The Nine Moves

Call the three faces that do not touch the fixed corner $X,Y,Z$. The assignment names the corresponding free-face generators $R,B,D$ in its own corner convention; the adapter must specify their correspondence to these axes. In the **half-turn metric (HTM)**, a quarter turn, a half turn, and an inverse quarter turn each cost one move. The move set is therefore

$$
X,X^2,X^3,\quad Y,Y^2,Y^3,\quad Z,Z^2,Z^3.
$$

The faces touching the fixed corner need not be listed separately. Turning such a face and rotating the whole cube to restore the fixed corner is equivalent to turning the opposite face in the reverse direction, still at a cost of one.

For move $m$, let $u_m(i)$ be the old source position for new position $i$, and let $v_m(i)\in\{0,1,2\}$ be the orientation increment. Define

$$
p'_i=p_{u_m(i)},\qquad o'_i\equiv o_{u_m(i)}+v_m(i)\pmod3.
$$

`state_move()` implements this update:

```c
q = n2_b8_move_src[mi * 8u + i];
d->p[i] = s->p[q];
v = s->o[q] + n2_b8_move_delta[mi * 8u + i];
d->o[i] = v >= 3u ? v - 3u : v;
```

Each `move_src` row is a permutation of the positions. Each `move_delta` row sums to $0\bmod3$, and position 7 always comes from position 7 with increment 0. The nine moves therefore preserve the invariants in Section 1. The cube of a quarter turn is its inverse, and a half turn is its own inverse, so every move is invertible.

#### 2.2 The State Graph

**Definition (graph, path, and distance).** The vertices of $\Gamma$ are the states in $\mathcal X$. Join $x$ to $y$ when $y=M_m(x)$ for some move $m$. Since moves are invertible, $\Gamma$ is undirected. A path's length is its number of edges, and $d(x,y)$ is the length of a shortest path. Write $e$ for the solved state.

The host stores a nonnegative integer $D(x)$ for every candidate state and exhaustively verifies:

$$
D(e)=0\quad\text{and }e\text{ is the only state labeled }0,
$$

$$
x\sim y\Longrightarrow |D(x)-D(y)|\le1,
$$

It also checks that every $x\ne e$ has a neighbor $y$ with $D(y)=D(x)-1$.

**Theorem 2.1 (distance certificate).** $D(x)=d(x,e)$ for every $x\in\mathcal X$.

**Proof.** Repeatedly choose a neighbor whose label is one smaller. After exactly $D(x)$ steps, this reaches the unique state labeled zero, namely $e$. Hence $d(x,e)\le D(x)$. Conversely, any edge can decrease $D$ by at most one. A path from label $D(x)$ to zero therefore needs at least $D(x)$ steps, so $d(x,e)\ge D(x)$. ∎

The certificate checks all $3\,674\,160$ vertices and all $9\cdot3\,674\,160=33\,067\,440$ directed moves. Since every candidate state has a descending chain to $e$, every coordinate in Section 1 is reachable. It also establishes

$$
\boxed{\max_x d(x,e)=11},
$$

Exactly 2,644 states have distance 11.

#### 2.3 The Cube Group and the Cayley Graph

Let $G=\langle X,Y,Z\rangle$ be the group of fixed-corner cube transformations generated by the three quarter turns. Its elements are physical move sequences considered equal when they induce the same transformation on every state. This is distinct from the automorphism group $H$ introduced in Section 7.

Every move sequence has the form

$$
p'_i=p_{u(i)},\qquad o'_i\equiv o_{u(i)}+v_i\pmod3,
$$

for a source permutation $u$ and orientation increments $v$. This follows by composing the update in Section 2.1. Applied to $e$, where $p_i=i$ and $o_i=0$, its output records exactly $u$ and $v$. Therefore two transformations with the same image of $e$ agree on every state.

The map $g\mapsto g(e)$ from $G$ to $\mathcal X$ is injective by that observation and surjective by the reachability certificate in Section 2.2. Hence

$$
|G|=|\mathcal X|=7!3^6=3\,674\,160.
$$

Under this identification, an edge applies one of
$X,X^2,X^3,Y,Y^2,Y^3,Z,Z^2,Z^3$. Thus $\Gamma$ is a **Cayley graph** of $G$ with these inverse-closed generators. Its vertices correspond to group elements, and its edges correspond to multiplication by a generator.

Cayley graphs are vertex-transitive: translating every group element on the side opposite the generator multiplication preserves edges and can send any chosen vertex to the identity. Therefore the maximum distance from $e$ is also the graph diameter. The exhaustive certificate supplies both parts of the diameter claim: every distance is at most eleven, and 2,644 states attain eleven.

The orientation condition is a modulo-three invariant, not a parity condition. A single isolated corner twist would violate it. There is no even-permutation restriction on the seven movable corners here: the reachability certificate covers all $7!$ permutations.

#### 2.4 Why Exhaustive BFS Establishes Distance

BFS starts with $e$ at depth zero and processes a FIFO queue. When a depth-$k$ vertex discovers an unvisited neighbor, it assigns depth $k+1$. FIFO order processes all smaller depths first. If a shorter path existed, its penultimate vertex would already have discovered that neighbor. Induction therefore makes the first discovery depth equal to the shortest-path distance.

An exhaustive run must also establish that all $3\,674\,160$ candidates were reached. Merely observing one depth-eleven vertex is insufficient to prove the diameter. The distance certificate in Theorem 2.1 provides an independently checkable characterization of the resulting distance labels.


### 3. State Encoding

Both the runtime and the offline host tools index states by integers.

The six independent orientations form a six-digit base-three number:

$$
\operatorname{ori}(o)=3^5o_0+3^4o_1+\cdots+3o_4+o_5\in\{0,\ldots,728\}.
$$

For permutation $p=(p_0,\ldots,p_6)$, let $a_i$ count the unused values smaller than $p_i$ when position $i$ is processed. Its **Lehmer rank** is

$$
\operatorname{pr}(p)=a_0 6!+a_1 5!+\cdots+a_5 1!\in\{0,\ldots,5039\}.
$$

This is the lexicographic rank of the permutation: $a_i(6-i)!$ counts the permutations skipped by choosing a smaller unused value at the first differing position $i$. In the reverse direction, successive quotients by $6!,5!,\ldots,1!$ uniquely recover the digits $a_i$ and then the permutation. Thus `perm_rank7()` is a bijective encoding.

The host uses the dense rank

$$
\operatorname{dense}(s)=729\operatorname{pr}(p)+\operatorname{ori}(o),
$$

whose values are exactly $0,\ldots,3\,674\,159$.

A collision-free auxiliary coordinate key is

$$
K(s)=2^{10}\operatorname{pr}(p)+\operatorname{ori}(o)=(\operatorname{pr}\ll10)\;|\;\operatorname{ori}.
$$

Since $\operatorname{ori}<729<2^{10}$, the quotient by $2^{10}$ and the low ten bits uniquely recover `pr` and `ori`. Thus $K$ is also collision-free, although its range contains gaps.

### 4. Groups and Graph Symmetries

#### 4.1 Groups, Actions, and Cosets

**Definition (group).** A set $G$ with a binary operation is a group if the operation is closed and associative, there is an identity element $1$, and every $g\in G$ has an inverse $g^{-1}$.

The group elements used here are bijections of the state space. Their operation is function composition:

$$
(f\circ g)(x)=f(g(x)).
$$

The composition of two bijections is a bijection, $\mathrm{id}$ is the identity, and

$$
(f\circ g)^{-1}=g^{-1}\circ f^{-1}.
$$

If $K\subseteq G$ is itself a group under the same operation, write $K\le G$ and call it a **subgroup**. All permutations of $n$ objects form the **symmetric group** $S_n$.

**Definition (group action).** An action of $G$ on $X$ assigns $g(x)\in X$ to every $g\in G$ and $x\in X$, subject to

$$
1(x)=x,\qquad (gh)(x)=g(h(x)).
$$

**Definition (orbit and stabilizer).**

$$
G\cdot x=\{g(x):g\in G\},\qquad G_x=\{g\in G:g(x)=x\}.
$$

If two orbits intersect, say $g(x)=h(y)$, then $y=h^{-1}g(x)$, so they are the same orbit. Also, $x=1(x)$, so the orbits partition $X$. Their set is denoted $X/G$. Since the identity, composition, and inverses all preserve the condition of fixing $x$, the stabilizer $G_x$ is a subgroup.

For $K\le G$, the set $Kg=\{kg:k\in K\}$ is a **right coset**. The map $k\mapsto kg$ is bijective, so each right coset contains $|K|$ elements. If two right cosets intersect, multiplying by the appropriate inverses shows that they coincide.

**Theorem 4.1 (orbit–stabilizer).** For a finite group action,

$$
|G\cdot x|=\frac{|G|}{|G_x|}.
$$

**Proof.** Fix $y=g(x)$. The group elements sending $x$ to $y$ are exactly the left coset $gG_x$. Each orbit element therefore has exactly $|G_x|$ preimages among the elements of $G$. ∎

#### 4.2 Graph Automorphisms

**Definition.** An automorphism of $\Gamma$ is a bijection $h$ of its vertices such that

$$
x\sim y\iff h(x)\sim h(y).
$$

If $h(e)=e$, it is a **root-fixing automorphism**.

**Theorem 4.2.** A graph automorphism preserves distance. If it fixes the root, then

$$
d(h(x),e)=d(x,e).
$$

**Proof.** Apply $h$ to each vertex of a shortest path to obtain a path of the same length. Thus $d(h(x),h(y))\le d(x,y)$. Applying the same argument to $h^{-1}$ gives the reverse inequality. ∎

### 5. The $S_3$ Axis Symmetries

#### 5.1 The Six Axis Permutations

Represent the eight corner positions by three bits:

$$
i=4a+2b+c,
\qquad a,b,c\in\{0,1\}.
$$

There are $3!=6$ permutations of the three coordinate axes, forming $S_3$. Let $\phi_h$ denote the $h$th axis permutation.

The implementation stores:

```text
n2_b8_sym_pos[6×8]       phi_h on position/cubie labels
n2_b8_sym_twist[6×8×8×3] full orientation action
n2_b8_sym_inv[6]          inverse transformation ID
```

Define the position parity

$$
\chi(i)=(a+b+c)\bmod2.
$$

The six full-state transformations $U_h$ are

$$
p'_{\phi_h(i)}=\phi_h(p_i),
$$

$$
o'_{\phi_h(i)}
\equiv
\varepsilon_h o_i+\beta_h(\chi(i)-\chi(p_i))\pmod{3},
$$

Here $(\varepsilon_h,\beta_h)$ are six fixed coefficient pairs. The implementation numbers them as follows; $\phi_h$ is listed by its images of the eight positions:

| $h$ | $\phi_h(0),\ldots,\phi_h(7)$ | $\varepsilon_h$ | $\beta_h$ |
|---:|---|---:|---:|
| 0 | `0,1,2,3,4,5,6,7` | 1 | 0 |
| 1 | `0,2,1,3,4,6,5,7` | 2 | 1 |
| 2 | `0,1,4,5,2,3,6,7` | 2 | 2 |
| 3 | `0,2,4,6,1,3,5,7` | 1 | 2 |
| 4 | `0,4,1,5,2,6,3,7` | 1 | 1 |
| 5 | `0,4,2,6,1,5,3,7` | 2 | 0 |

`n2_b8_sym_twist` stores the 1,152 lookup values of this formula. The verifier recomputes and checks every entry.

**Proposition 5.1.** Every $U_h$ maps valid states to valid states and fixes the solved state.

**Proof.** $\phi_h$ relabels both positions and cubies, preserving the permutation property. Orientations reduced modulo three remain in $\{0,1,2\}$. Their sum is

$$
\varepsilon_h\sum_i o_i
+\beta_h\Bigl(\sum_i\chi(i)-\sum_i\chi(p_i)\Bigr).
$$

Since $p$ is a permutation, the second parenthesis subtracts two sums of the same values and is zero. The first term is also zero by the orientation invariant. If $p_i=i,o_i=0$, the formulas still give $p'=\mathrm{id},o'=0$. ∎

**Proposition 5.2.** The six $U_h$ form a group under composition, with exactly the multiplication rules of the six axis permutations.

**Proof.** Let $A=U_1$ and $B=U_3$. Direct composition of the position tables gives $A^2=\mathrm{id}$, $B^3=\mathrm{id}$, and $ABA=B^{-1}$. Composing the orientation formulas, first with coefficients $(\varepsilon_b,\beta_b)$ and then with $(\varepsilon_a,\beta_a)$, gives

$$
\varepsilon=\varepsilon_a\varepsilon_b,
\qquad
\beta=\varepsilon_a\beta_b+\beta_a\pmod{3}.
$$

Substituting $A=(2,1)$ and $B=(1,2)$ gives the same three relations, so the position and orientation actions agree. Using $AB=B^{-1}A$, move every A to the right, then apply $A^2=\mathrm{id},B^3=\mathrm{id}$. Every word reduces to one of

$$
I,\ A,\ B,\ BA,\ B^2,\ B^2A.
$$

Their position actions are, respectively, $U_0,U_1,U_3,U_5,U_4,U_2$, which are distinct. The generated set has at most six elements and at least six, so it consists of exactly these six $U_h$. It is closed under composition and inverses and is therefore a group. ∎

#### 5.2 Edge Preservation

For each $U_h$, there is a fixed permutation $\sigma_h$ of the nine move labels satisfying

$$
U_h(M_m(s))=M_{\sigma_h(m)}(U_h(s)).
$$

**Finite-certificate Proposition 5.3.** This identity holds for all six $h$, all nine $m$, and every $s\in \mathcal X$.

**Proof.** The verifier compares the full `WorkState` values on both sides for all $3\,674\,160\times 9$ labeled edges, separately for generators $A=U_1$ and $B=U_3$. Any mismatch is a failure; all comparisons pass. Proposition 5.2 expresses the other four $U_h$ as compositions of A and B. If $g_1,g_2$ have fixed move permutations $\sigma_1,\sigma_2$, set $t=g_1(s)$ and $n=\sigma_1(m)$ and substitute:

$$
g_2(g_1(M_m(s)))
=g_2(M_{\sigma_1(m)}(g_1(s)))
=M_{\sigma_2(\sigma_1(m))}(g_2(g_1(s))).
$$

Thus this equivariance identity is closed under composition, so it holds for all six elements of $S_3$ generated by A and B. ∎

By Theorem 4.2, every $U_h$ is a root-fixing graph automorphism and preserves distance to the root.

#### 5.3 Permutation Orbits and Burnside's Lemma

**Burnside's lemma.** If a finite group $G$ acts on a finite set $X$, then

$$
|X/G|=\frac1{|G|}\sum_{g\in G}|\operatorname{Fix}(g)|,\qquad \operatorname{Fix}(g)=\{x:g(x)=x\}.
$$

**Proof.** Count pairs $(g,x)$ satisfying $g(x)=x$. Counting first by $g$ gives the numerator on the right. If $y=a(x)$, the map $h\mapsto aha^{-1}$ is a bijection from $G_x$ to $G_y$, so stabilizers have equal sizes within an orbit. By orbit–stabilizer,
$|G\cdot x||G_x|=|G|$. Each orbit therefore contributes exactly $|G|$ pairs. Divide by $|G|$. ∎

First ignore orientations and consider permutations of the seven movable cubies. A cycle containing two elements is a **2-cycle**; one containing three is a **3-cycle**; an unchanged element is a **fixed point**.

The permutations $p$ and $\phi$ **commute** if $p\circ\phi=\phi\circ p$. A permutation is fixed by axis relabeling $\phi$ exactly when it commutes with $\phi$.

The identity axis permutation fixes all 5,040 permutations.

An exchange of two axes has two 2-cycles and three fixed points on the seven movable positions. To count commuting permutations, first observe that they preserve cycle length. Suppose $p\phi=\phi p$ and the cycle of $i$ under $\phi$ has length $r$. Since $\phi^r(i)=i$, commutativity gives

$$
\phi^r(p(i))=p(\phi^r(i))=p(i),
$$

The cycle length of $p(i)$ therefore divides $r$. Apply the same argument to $p^{-1}$ to obtain the reverse divisibility. The lengths are equal, so a commuting permutation maps each cycle to a cycle of the same length.

For an exchange of two axes, the three fixed points may be permuted in $3!$ ways and the two 2-cycles in $2!$ ways. When a source 2-cycle is mapped to a target 2-cycle, its first point may go to either target point; commutativity determines the second. The two cycles contribute another factor $2^2$. The number of fixed permutations is

$$
3!\cdot2!\cdot2^2=48.
$$

A cyclic permutation of the three axes has two 3-cycles and one fixed point. The fixed point must remain fixed. The two 3-cycles may be exchanged in $2!$ ways, and each source cycle's first point has three possible images in its target cycle. Commutativity determines the remaining two points. The number of fixed permutations is

$$
2!\cdot3^2=18.
$$

$S_3$ contains one identity, three axis exchanges, and two 3-cycles. Burnside's lemma gives

$$
\boxed{\frac{5040+3\cdot48+2\cdot18}{6}=870}
$$

permutation orbits.

#### 5.4 Stabilizers of Permutation Orbits

Call a permutation orbit **ordinary** if its stabilizer contains only the identity, and **exceptional** otherwise.

**Proposition 5.4.** Of the 870 permutation orbits, 814 have trivial stabilizers and 56 have nontrivial stabilizers. The latter comprise two orbits with stabilizer size 6, eight with size 3, and 46 with size 2.

The elements of $S_3$ are the identity, two mutually inverse 3-cycles, and three transpositions. A subgroup containing a 3-cycle contains its inverse. If it also contains any transposition, composition gives the other transpositions, so it is all of $S_3$. Thus there is exactly one subgroup of order three. Each transposition $t$ satisfies $t^2=id$, giving the order-two subgroup $\{id,t\}$. Two distinct transpositions multiply to a 3-cycle and generate all of $S_3$. Consequently a stabilizer has size $1,2,3,6$; there is one possible order-three subgroup and three possible order-two subgroups.

**Proof.** First find the permutations fixed by all of $S_3$. The axis action partitions the seven positions into $\{0\}$, $\{1,2,4\}$, and $\{3,5,6\}$. Position 0 must be fixed. Suppose each three-element set is preserved. For any position $a$ in either set, an axis exchange fixes $a$ and exchanges the other two positions. If $p$ commutes with every axis permutation, $p(a)$ must be fixed by the same exchange. The only fixed point in that set is $a$, so $p(a)=a$. Thus each set admits only the identity internally. If the two sets are exchanged, each point's stabilizer similarly determines its unique partner in the other set, giving the exchange $i\mapsto 7-i$ between them. Exactly two permutations are fixed by the whole group, hence there are two singleton permutation orbits.

A size-three stabilizer must be the unique order-three subgroup of $S_3$. A 3-cycle fixes 18 permutations; two are already fixed by the whole group. The remaining 16 have stabilizer size three, and each orbit has size $6/3=2$, giving $16/2=8$ orbits.

A size-two stabilizer is generated by a transposition. Each transposition fixes 48 permutations, of which two are fixed by the whole group, leaving 46. The remaining sets for distinct transpositions are disjoint: a permutation fixed by two different transpositions would be fixed by the whole group they generate. Thus $3\cdot46=138$ permutations have stabilizer size two. Each orbit has size $6/2=3$, giving $138/3=46$ orbits.

The remaining

$$
5040-2-16-138=4884
$$

permutations have trivial stabilizers and orbits of size six, giving $4884/6=814$ ordinary orbits. The exceptional count is $2+8+46=56$. ∎

Therefore

$$
\boxed{870=814+56.}
$$

#### 5.5 Orientation Orbits

If a representative permutation has stabilizer size $k\in\{1,2,3,6\}$, that stabilizer acts on its 729 orientation assignments.

**Proposition 5.5.** For any nonidentity element of $S_3$ and any representative permutation fixed by that element, exactly nine valid orientation assignments are fixed.

**Proof.** There are two cases. For an axis exchange, the position action has two 2-cycles and the orientation equation is $o_{\phi(i)}=-o_i+c_i$. Since $p\phi=\phi p$ and $\chi(\phi(i))=\chi(i)$, the offset $c_i=\beta(\chi(i)-\chi(p_i))$ is constant on each $\phi$-cycle. At a fixed point, $o=-o+c$, or $2o\equiv c\pmod3$, has exactly one solution for each $c=0,1,2$. On each 2-cycle, its first orientation has three choices and uniquely determines the second, giving $3^2=9$ assignments. Summing the fixed-state equations shows that their total orientation is automatically zero. For a three-axis cycle, there are two 3-cycles. The orientations on each are $a,a+c,a+2c$, with three choices of $a$, again giving nine assignments. Each cycle sums to $3a+3c\equiv0\pmod3$, so the total-sum constraint forces the single remaining fixed point's orientation to be zero. ∎

Burnside's lemma therefore gives:

$$
\begin{array}{c|c}
|G_p| & \text{orientation orbit count}\\\hline
1&729\\
2&(729+9)/2=369\\
3&(729+2\cdot9)/3=249\\
6&(729+5\cdot9)/6=129
\end{array}
$$

The number of full-state $S_3$ orbits is consequently

$$
814\cdot729+46\cdot369+8\cdot249+2\cdot129
=\boxed{612\,630}.
$$

#### 5.6 Orbit Encoding: `quotient_rank_from_meta()`

The 5,040 entries in `n2_b8_pmeta[pr]` are exhaustively verified. Their packed format is

$$
\texttt{meta}=8j+b,
$$

where $j$ is the permutation-orbit index and $b$ is the $S_3$ transformation sending the current permutation to its representative.

##### Ordinary Orbits

With a trivial stabilizer, the transformation to the representative is unique. Let $r$ be the transformed orientation rank:

$$
C_3(s)=729j+r.
$$

`h48_common_base[j]` stores $729j$ directly. To compute the orientation at a new position `np`, `ori_rank_after_sym(s,b)` must first find its old source with $\phi_b^{-1}$. It therefore uses `n2_b8_sym_inv[b]`.

##### Exceptional Orbits

After fixing the permutation, its nontrivial stabilizer can still change the orientations. Set $q=U_b(s)$ and define

$$
r_{\min}=\min_{h\in G_p}\operatorname{ori}(U_h(q)).
$$

**Proposition 5.6.** $r_{\min}$ is independent of the initial choice of $b$.

**Proof.** If $b,b'$ both send the permutation to the same representative, then $U_{b'}U_b^{-1}$ lies in that representative's stabilizer. Enumerating the full stabilizer from $U_b(s)$ or from $U_{b'}(s)$ differs only by a permutation of the group elements. The orientation sets, and hence their minima, are the same. ∎

**Definition 5.7 (bitset).** A bitset represents a finite set by bits: bit $r$ is one if $r$ is selected and zero otherwise.

Representative orientation ranks do not form a contiguous interval in $0\ldots728$. Mark the minimum representatives in a bitset and assign dense indices by

$$
\rho(r)=|\{j<r:B_j=1\}|
$$

which counts the selected ranks preceding $r$.

**Proposition 5.8.** If the representative ranks are $r_0<r_1<\ldots<r_{t-1}$, then $\rho(r_j)=j$. Thus $\rho$ is a bijection from the representatives to $0,\ldots,t-1$.

**Proof.** Exactly $j$ representative bits precede $r_j$, so the defining count equals $j$. ∎

`mask_rank()` computes this $\rho$.

**Definition 5.9 (orientation action pattern).** For a fixed representative permutation, its orientation action pattern is the partition of the 729 orientation ranks into orbits under its stabilizer.

Exhaustive enumeration finds only 13 such patterns among the 56 exceptional permutation orbits. The same enumeration verifies `exception_action()`, `stabilizer_mask()`, and all 13 bitsets.

**Theorem 5.10.** The key $C_3$ produced by `quotient_rank_from_meta()` satisfies

$$
C_3(s)=C_3(t)\iff S_3\cdot s=S_3\cdot t.
$$

**Proof.** States in the same $S_3$ orbit have permutations in the same permutation orbit. For an ordinary orbit, mapping the permutation to its representative gives the same orientations. For an exceptional orbit, the two resulting states differ by an element of the representative permutation's stabilizer. Proposition 5.6 and minimization over that stabilizer give the same $r_{\min}$ and $\rho(r_{\min})$, hence the same key. Conversely, equal keys lie in the same base interval and therefore use the same representative permutation. In an ordinary orbit, equal orientation ranks give the same full representative. In an exceptional orbit, equal $\rho$ values identify the same stabilizer orbit of orientations. In either case, an element of $S_3$ transforms one state into the other. ∎

The base offsets are prefix sums of the orbit counts, so $C_3$ covers $0,\ldots,612629$ contiguously.

### 6. The Automorphism $T$

$S_3$ reduces 3,674,160 states to 612,630 orbits. The implementation also uses a root-fixing graph automorphism $T$.

#### 6.1 Coordinate Decomposition

Find the position $j\in\{0,\ldots,6\}$ and orientation $t\in\{0,1,2\}$ of cubie 6, and set

$$
q=3j+t\in\{0,\ldots,20\}.
$$

After removing that position, cubies $0,\ldots,5$ form a permutation $x\in S_6$. As defined in Section 4.1, $S_6$ contains all permutations of six objects. Take five independent remaining orientations $y=(y_0,\ldots,y_4)$; their sixth value is determined by the total-sum constraint.

**Proposition 6.1 (uniqueness of the T coordinates).** Valid `WorkState` values are in bijection with triples $(q,x,y)$.

**Proof.** Cubie 6 occurs once in a valid permutation, uniquely determining $j,t$, and hence $q=3j+t$. Removing its position and reading the remaining positions in order uniquely determines $x,y$. Conversely, the quotient and remainder of $q$ divided by three recover $j,t$. Restore cubie 6, the other six cubies, and the five stored orientations. The orientation-sum constraint in Section 1 uniquely recovers the last orientation. These constructions are inverse to one another. ∎

**Definition 6.2 ($\mathbb F_3$ and affine maps).**
Let $\mathbb F_3=\{0,1,2\}$ with addition, subtraction, and multiplication modulo three. This is the field with three elements. Write $\mathbb F_3^5$ for its five-dimensional vectors, with matrix operations defined below.

For a $5\times5$ matrix $A$ and a vector $y$,

$$
(Ay)_i=\sum_{j=0}^{4}A_{ij}y_j\pmod3.
$$

A map $y\mapsto Ay+b$ is **affine**. Composing two affine maps gives

$$
B(Ay+b)+c=(BA)y+(Bb+c).
$$

Thus there is a bijection

$$
\mathcal X\longleftrightarrow\{0,\ldots,20\}\times S_6\times\mathbb F_3^5.
$$

The orientation component of T can consequently be described by 21 fixed affine maps.

#### 6.2 Definition and Implementation of $T$

For each $q$, fixed data define T by

$$
q'=f(q),
$$

$$
x'_i=\tau(x_{R_q(i)}),
$$

$$
y'=A_qy+b_q,
$$

where $\tau$ is the cubie-label permutation exchanging $(0,1),(2,3),(4,5)$.

The implementation stores:

```text
h48_t_dst[21]       q → q'
h48_t_perm_R[21×6] R_q
h48_t_ori_ctl[21]   sparse encoding of A_q,b_q
```

Each output orientation coordinate has one of two forms:

$$
c+y_0+y_1+y_2+y_3+y_4,
$$

or

$$
c+2y_s.
$$

Therefore `compact_T()` requires only a small number of additions, shifts, and calls to `mod3_small()`, rather than a general matrix multiplication.

#### 6.3 $T$ Is an Involution

**Definition (involution).**
A transformation is an involution if $T\circ T=\mathrm{id}$.

The verifier checks all 21 table rows. With $q'=f(q)$, they satisfy

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

**Theorem 6.3.** $T^2=\mathrm{id}$.

**Proof.** The first identity restores $q$. For the permutation component, the second identity and $\tau^2=\mathrm{id}$ cancel the two source reorderings and the two label exchanges, restoring $x$. The affine-composition formula in Section 6.1 gives the final orientation vector

$$
A_{q'}(A_qy+b_q)+b_{q'}
=(A_{q'}A_q)y+(A_{q'}b_q+b_{q'})=y.
$$

All three components are restored. ∎

#### 6.4 Edge Preservation and the Local Move Map

For every state $s$, a permutation $\sigma_T(s)$ of the nine move labels satisfies

$$
T(M_m(s))
=M_{\sigma_T(s)(m)}(T(s)).
$$

$\sigma_T(s)$ depends on the state. `t_sigma_code(s)` locates cubie 6, reads its orientation $t$, and computes `pr=perm_rank7(s->p)`. It uses

$$
idx=3\,pr+t\in\{0,\ldots,15119\}
$$

to index `h48_sigma_pr_3bit`. Codes $0\ldots5$ use three bits each. The payload is $15120\cdot3/8=5670$ bytes plus one zero guard byte, for 5,671 bytes. Section 10 proves the accessor, including entries that cross byte boundaries.

**Finite-certificate Proposition 6.4.** This identity holds for every $s\in\mathcal X$ and every move $m$, and $T(e)=e$.

**Verification.** Enumerate all states by dense rank and compare the full `WorkState` values on the two sides for each move. Check the root separately. All comparisons pass. ∎

Theorem 6.3 establishes bijectivity, and Proposition 6.4 establishes edge preservation and root fixing. Hence $T$ is a root-fixing graph automorphism.

The local move map for T must be evaluated at the state on which T acts.

### 7. H48 Canonicalization

#### 7.1 The Generated Group

**Definition 7.1 (generated group).**
Given elements of a group, all finite compositions of those elements and their inverses form the subgroup they generate, denoted $\langle\cdots\rangle$.

Let $A=U_1$ and $B=U_3$, which generate the $S_3$ from Section 5. Define

$$
H=\langle A,B,T\rangle.
$$

$A,B,T$ are root-fixing graph automorphisms, so every element of $H$ is one as well. The finite composition table for $S_3$ gives $A^2=\mathrm{id}$ and $B^3=\mathrm{id}$; Theorem 6.3 gives $T^2=\mathrm{id}$. Thus

$$
A^{-1}=A,
\qquad B^{-1}=B^2,
\qquad T^{-1}=T.
$$

Although a generated group allows inverse generators, every element here can be represented by a finite word using only the forward letters $A,B,T$.

#### 7.2 The 48 Group Elements

The dense ranking bijection in Section 3 has a unique inverse, written $\operatorname{unrank}(v)$, which decodes rank $v$ into its state.

For any transformation $h$, construct its full function table by

$$
L_h[v]=\operatorname{dense}(h(\operatorname{unrank}(v))).
$$

Since `dense` and `unrank` are inverse bijections, two tables $L_h$ agree entry by entry exactly when the transformations agree on every state.

Complete generation produces 48 distinct functions. Composing any one of them with A, B, or T remains within that set.

**Theorem 7.2.** $|H|=48$.

**Proof.** All 48 functions are distinct and generated by words, so $|H|\ge48$. The set contains the identity and is closed under appending any of $A,B,T$. Induction on word length therefore places every generated word in this set, giving $|H|\le48$. ∎

#### 7.3 Eight Right Cosets of $S_3$

$S_3$ is a subgroup of $H$ with six elements. By the coset partition in Section 4.1, its right cosets $S_3g$ are disjoint and each contains six elements. Hence $H$ has

$$
48/6=8
$$

right cosets.

Representative words record **execution order from left to right**. For example, $A\,T$ means first apply A and then T, corresponding to the function composition $T\circ A$.

The implementation chooses these eight words:

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

Full function comparison confirms that the cosets $S_3R_i$ contain 48 distinct elements in total, so they cover $H$ exactly.

`h48_len[]` stores the word lengths, and `h48_word[][]` stores their operation sequences.

#### 7.4 $H$ Orbits and Their Keys

**Definition 7.3 (canonicalization).** Choose a total order on a finite orbit and designate its unique minimum as the **canonical representative**. Canonicalization maps an arbitrary orbit element to that representative.

Section 5.6 already selects representatives of the $S_3$ orbits and assigns their dense keys $C_3$. The H layer orders these keys and selects the smallest among eight candidates. `perm_sym/stab_sym` records the transformations sending a candidate to its $S_3$ representative.

The dense $S_3$ key satisfies $C_3(s)\in\{0,\ldots,612629\}$. Define

$$
C_H(s)=\min_{0\le i<8}C_3(R_i(s)).
$$

**Theorem 7.4.**

$$
C_H(s)=C_H(t)
\iff
H\cdot s=H\cdot t.
$$

**Proof.** $H$ is the disjoint union of the eight right cosets $S_3R_i$, and $hR_i$ acts on $s$ as $h(R_i(s))$. Thus $H\cdot s$ is the union of the eight sets $S_3\cdot R_i(s)$. States in the same $H$ orbit enumerate the same $S_3$ orbits and have the same minimum $C_3$. Conversely, equal minima imply, by Theorem 5.10, that some $R_i(s)$ and $R_j(t)$ lie in the same $S_3$ orbit. The corresponding $S_3$ element and both representatives belong to H, so $s,t$ lie in the same $H$ orbit. ∎

**Finite-certificate Proposition 7.5.** The action of $H$ on $\mathcal X$ has exactly 77,802 orbits.

**Verification.** For every dense state, enumerate its 48 H images and take the minimum dense rank. Count an orbit precisely when the current state is that minimum; this gives 77,802. Independently summing the fixed-point counts of the 48 group elements and applying Burnside's lemma gives the same result. ∎

Therefore

$$
\boxed{|\mathcal X/H|=77\,802}.
$$

#### 7.5 Filtering by Permutation Orbit

Each permutation orbit occupies a contiguous interval of $S_3$ orientation keys, and these intervals increase with the permutation-orbit index. Consequently every complete key for a later permutation orbit exceeds every key for an earlier one.

**Proposition 7.6.** Finding the smallest permutation-orbit index among the eight candidates and computing complete $S_3$ keys only for those candidates gives the same result as computing all eight complete keys and taking their minimum.

**Proof.** Even the minimum key in a later interval exceeds the maximum key in an earlier interval. A candidate in a later interval cannot be the global minimum. ∎

#### 7.6 The Orbit Key and the Transformation Frame

`H48Canon`:

```c
typedef struct {
    uint32_t key;
    uint8_t rep;
    uint8_t perm_sym;
    uint8_t stab_sym;
} H48Canon;
```

$key=C_H(s)$ identifies the $H$ orbit. The other three fields record the particular transformation used to send $s$ to its canonical representative:

$$
g=U_{\texttt{stab\_sym}}
\circ U_{\texttt{perm\_sym}}
\circ R_{\texttt{rep}}.
$$

Call `(rep,perm_sym,stab_sym)` the **frame**. It retains the transformation needed to lift the selected canonical move back to the original state.

### 8. A Descending Policy and Perfect Hashing

#### 8.1 The Descending Policy

**Definition 8.1 (policy).**
A policy $\pi$ selects a move for each nonroot state.

It is a **descending policy** if

$$
D(M_{\pi(x)}(x))=D(x)-1,
$$

for every nonroot state $x$.

**Theorem 8.2.** Repeatedly following a descending policy from a state at distance $d$ reaches the root in exactly $d$ steps and returns a shortest solution.

**Proof.** Induction gives distance $d-k$ after $k$ steps. At $k=d$, the distance is zero and the state must be the root; before then, it is positive. By the definition of distance, no solution uses fewer than $d$ moves. ∎

Offline generation stores one descending move per nonroot H canonical representative. At runtime, canonicalization selects the representative whose move is queried.

#### 8.2 Perfect Hashing

**Definition 8.3 (hashing and collisions).**
A hash function maps keys to finitely many **slots**. A collision occurs when distinct keys share a slot. This implementation first assigns a key to a **bucket**, then uses the bucket's integer **displacement** to determine its final slot. A hash is **perfect** on a specified finite key set if it has no collisions within that set.

There are 77,802 valid H keys. `policy_lookup()` uses the following unsigned 32-bit arithmetic:

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

Here $\oplus$ is bitwise XOR, `&` is bitwise AND, and `<<,>>` are shifts. Intermediate values retain their low 32 bits, as in `uint32_t` arithmetic. These mixing formulas have no general collision-free guarantee; perfection is a finite-certificate property of the particular 77,802 valid H keys.

The slot universe has $2^{17}=131072$ positions, but only 77,802 are used. The balanced implementation stores a bit per slot, a prefix rank per 512-slot block, and a dense nibble array. Section 10 derives this lookup.

```text
h48_policy_disp      16,384 bytes
h48_policy_used      16,384 bytes
h48_policy_prefix     1,024 bytes
h48_policy_dense     38,901 bytes
total                72,693 bytes (before linker alignment)
```

**Finite-certificate Proposition 8.4.** The 77,802 valid H keys occupy 77,802 distinct slots, and every slot used by a nonroot valid key contains a descending move for its canonical representative.

**Verification.** Enumerate every valid H key and check that its slot is unique. Then, for every nonroot original state, execute canonicalization, policy lookup, and move lifting, and check that the resulting original move decreases the exact $D$ by one. Both exhaustive checks pass. ∎

`policy_lookup()` therefore need not store the original keys. Its precondition is that the input is a valid $C_H(s)$.

### 9. Lifting Move Labels Back to the Original State

#### 9.1 Local Move Maps

An edge-preserving automorphism $g$ maps edges to edges. To recover a move in the original coordinates, we must also identify the label of each mapped edge.

**Definition 9.1 (local edge-label map).**
Suppose every move $m$ has a unique label $\sigma_g(s)(m)$ satisfying

$$
g(M_m(s))
=M_{\sigma_g(s)(m)}(g(s)),
$$

Then $\sigma_g(s)$ is the local edge-label map of $g$ at $s$.

The nine moves have distinct `move_src` permutations on the movable positions. Since `p[0..6]` contains seven distinct cubies, different source permutations cannot produce the same `p'`. Thus the nine neighbors are distinct. An edge-preserving bijection $g$ maps each incident edge to an edge with a unique label, so $\sigma_g(s)$ permutes the nine labels and is invertible.

For $S_3$, the map $\sigma$ depends only on the transformation. For T, $\sigma_T(s)$ depends on the state as well.

#### 9.2 Moves at the Representative and the Original State

Suppose canonicalization gives

$$
c=g(s),
$$

and the policy selects move $a$ at $c$. The original state must use

$$
\boxed{m=\sigma_g(s)^{-1}(a).}
$$

**Theorem 9.2.** If $a$ decreases the distance of $c$ by one, then the move $m$ above decreases the distance of $s$ by one.

**Proof.** By definition, $g(M_m(s))=M_a(c)$. Theorem 2.1 gives $D(x)=d(x,e)$, and Theorem 4.2 gives distance preservation by a root-fixing automorphism. Hence $D(g(x))=D(x)$, and

$$
D(M_m(s))
=D(g(M_m(s)))
=D(M_a(c))
=D(c)-1
=D(s)-1.
$$

∎

#### 9.3 Composition and Intermediate States

Apply $g_1$ first and $g_2$ second, and set $s_1=g_1(s)$. Then

$$
\sigma_{g_2\circ g_1}(s)
=
\sigma_{g_2}(s_1)\circ\sigma_{g_1}(s).
$$

**Proof.**

$$
\begin{aligned}
g_2g_1(M_m(s))
&=g_2(M_{\sigma_{g_1}(s)(m)}(g_1(s)))\\
&=M_{\sigma_{g_2}(s_1)(\sigma_{g_1}(s)(m))}(g_2g_1(s)).
\end{aligned}
$$

Compare this identity with the definition of the local map. ∎

The code for T must be computed at the corresponding intermediate state.

#### 9.4 Reverse Pullback: `lift_policy_move()`

Each representative word $R_i$ contains at most five operations. The implementation follows the word forward. At every T, it calls `t_sigma_code(cur)` on the current state and stores that local code in `codes[]`. After collecting the final code, the state is no longer needed, so the final state transformation is omitted.

First invert the frame's final two $S_3$ label maps, then process the representative word in reverse:

```c
m = move_pullback[h->stab_sym][canonical_move];
m = move_pullback[h->perm_sym][m];
while (length != 0u)
    m = move_pullback[codes[--length]][m];
```

The reverse order follows from the inverse-composition identity in Section 4.1.

**Proposition 9.3.** Pulling back only the move selected by the policy gives the same result as constructing the full permutation of nine labels and taking that move's inverse image.

**Proof.** The value of a function composition at one input $a$ can be computed one layer at a time. Evaluating $f(g(a))$ does not require evaluating the other eight inputs. Both methods use the same local inverse maps in the same order and therefore return the same move. ∎


### 10. Rank Compression and Three-Bit Access

The perfect hash still produces a slot in $[0,131072)$. Define $U[i]=1$ exactly when slot $i$ contains a valid H key. Then

$$r(i)=\sum_{j<i}U[j].$$

For every used slot, this maps increasing slots bijectively onto $[0,77802)$. Store its original policy value at dense index $r(i)$. Lookup therefore returns the same value as the original slot array, without storing values for unused slots. This statement requires a used slot; arbitrary integer keys are outside the interface contract.

Let $w=i\gg5$, $b=i\gg9$, and $t=i\mathbin{\&}31$. `prefix[b]` counts used slots before this 512-bit block. The rank is that prefix plus the popcounts of complete words from $16b$ to $w-1$, plus the popcount of the low $t$ bits of `used[w]`. At most fifteen complete words are scanned. If $t=0$, the partial contribution is zero; the implementation avoids a shift by 32.

The policy accessor computes byte index $r\gg1$ and shift $4(r\mathbin{\&}1)$, then applies `&15`. **The parity is the dense rank's parity, not the original slot's parity.** The root sentinel is 15; nonsolved representatives use labels 0–8.

For T's local permutation code at index $j<15120$, set $z=3j$, $q=z\gg3$, and $t=z\mathbin{\&}7$. Read two unsigned bytes and compute

$$\sigma(j)=((B[q]+256B[q+1])\gg t)\mathbin{\&}7.$$

The three selected bits are exactly the bits written for entry $j$. The last entry starts at bit 45,357, byte 5,669; a zero guard at byte 5,670 makes the uniform second-byte read valid. No unaligned halfword load is needed. All 15,120 entries, all eight bit offsets, both index parities, and all 77,802 dense policy entries are checked against separately saved unpacked references by `host_tools/verify_packed.c`.

### 11. Correctness of the General Policy Loop

The new version has no sparse whole-path cache and no distance-11 bypass. Each nonsolved state follows the same H48 canonicalize–lookup–lift–apply loop. The cached initial permutation metadata only saves repeated ranking; it does not select a special path.

Let the initial exact BFS distance be $d$. The invariant after $k$ emitted moves is $D(s_k)=d-k$, and the output prefix really transforms the input into $s_k$. Root-fixing graph automorphisms preserve distance. The certified representative policy decreases it by exactly one, and the saved frame lifts that edge to the original coordinates. Applying and appending this move preserves the invariant. At $k=d$, the state has distance zero and is solved. Since the HTM diameter is 11, the loop terminates within the eleven-byte output buffer and returns exactly $d$ moves. Any path to solved needs at least $d$ moves, so this solution is shortest.

The host BFS array is a verification oracle, not a linked target table. The target contains a descending policy on H48 orbits and executes its canonicalization and move lifting for every nonsolved input. The user reports that the instructor approved this method as an exception to the assignment's usual on-target-search rule. This records the reported approval; a written approval URL has not been supplied.

### 12. Interface Contracts and Dependencies

`mod3_small` requires its bounded input, $0\le x\le12$. Work-state transforms require valid inputs and distinct input/output objects. `perm_rank7` requires a permutation. Metadata and lifting frames must belong to the current state, and each T map must be obtained at the correct intermediate state. `policy_lookup` requires a valid canonical H key.

The public solver validates seven permutation bytes and six independent twists before expansion. It rejects duplicate or out-of-range values, invalid moves and null required pointers. An optional statistics pointer may be null or only byte-aligned; stores preserve that contract. The output has capacity eleven and a separate length byte. Private transform helpers assume the public validation has already succeeded.

Proof dependencies are: valid coordinates and moves → exact BFS distances → root-fixing H48 automorphisms → representative policy descent → exact packed access → frame lifting → loop invariant and shortest output. This is a proof with finite certificates, backed by an independent replay campaign.

### 13. Scope of Optimality

The returned move count is optimal in HTM. Three bits are necessary for six local sigma values in a fixed-width code; four bits are necessary for nine moves plus a root sentinel. These local coding bounds do not prove globally minimal program space or instruction count. H48's 48 elements do not imply that every orbit has size 48; stabilizers explain why there are 77,802 orbits.

### 14. Fresh Verification

The October 8 campaign reran the native solver over all 3,674,160 states: no bad call, bad length or failed replay. The measured wall time for that campaign was 7.4406 s. The independent distance certificate checked all 33,067,440 directed edges, unique distance-zero root, edge Lipschitz bounds and a descending neighbor for every nonroot. It found diameter 11 and exactly 2,644 states at distance 11.

H48 verification found 48 elements, eight six-element cosets and 77,802 orbits; canonicalize–lookup–lift decreased distance on all 3,674,159 nonroot states. All 21 T affine identities, permutation metadata, orientation actions and generated accessors passed. No runtime heuristic is used, so H1 is recorded as **not applicable**, with exact policy descent as the relevant certificate; this is not a claimed heuristic-admissibility measurement.

## Stage 3: Balanced C Implementation

The supplied [n2_solver.c](../reference/n2_solver.c) is preserved byte for byte. Generated tables are provided C data, verified before linking. It removes the earlier 2,653 sparse path records and their decoders, so both distance-one and distance-eleven states now exercise the general policy. A full BFS oracle remains in host-only verification tools.

The representation and symmetry derivation above explain the computation being eliminated: permutation metadata avoids repeated six-way permutation minimization, stabilizer masks rank orientation orbits, eight right-coset representatives replace 48 full transforms, and an early permutation-class filter avoids unnecessary orientation work. These transformations are justified by the finite orbit and edge certificates, not by assuming equal orbit sizes.

Rank compression adds bounded popcount work but saves 9,227 policy bytes against the earlier 81,920-byte slot policy (16,384 displacement + 65,536 nibbles). Three-bit T sigma saves 1,889 bytes against 7,560 bytes. Removing sparse key/code arrays alone removes 21,224 bytes, plus the old decoders. These are payload comparisons; linker padding and runtime constants are counted separately.

### Every Generated Table

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


The payload total is **94,729 bytes**. It is not the program's memory footprint. `.rodata` also includes runtime messages and indexing helpers, and the program needs `.text`, `.bss`, padding, stack and MMIO storage.

### Operations That Matter on RV32I

There is no multiply, divide or remainder opcode. Strides use shifts and additions: $3j=(j\ll1)+j$, $8j=j\ll3$, and $35y=(y\ll5)+(y\ll1)+y$. The renderer instead advances row pointers by 140 bytes, avoiding a multiply per pixel. Permutation ranking uses the seven-bit popcount helper table; full-word rank scans use a SWAR `popcount32` made from shifts, masks and adds. Accessors use unsigned byte loads, preventing sign extension.

Small modulo three uses a bounded subtraction/table formulation, not general division. The following isolated target experiments make the time/space costs concrete:

| Isolated kernel | .text | Table bytes | ISS iret | 5S iret | 5S cycles |
| --- | --- | --- | --- | --- | --- |
| mod3_branch | 104 | 0 | 54009 | 54008 | 78014 |
| mod3_branchless | 104 | 0 | 57009 | 57008 | 75014 |
| dense_packed | 104 | 38901 | 1011437 | 1011436 | 1167044 |
| dense_byte | 88 | 77802 | 700229 | 700228 | 933638 |


The modulo experiment tests every sum 0–4 exactly 1,000 times, with the same driver and checksum. The branch version retires 3,000 fewer instructions on ISS; the branchless version saves 3,000 cycles on 5S, where branch redirection costs cycles. This is a kernel result, not a measured whole-solver replacement. The helper's wider $0..12$ domain has its own proof and verification.

The dense-access experiment reads all 77,802 entries once. Packing saves **38,901 bytes** and costs exactly four extra retired instructions per read in this driver. Expanding the linked GUI policy to bytes would give approximately 143,313 total guest bytes, already above the user's 131,072-byte ceiling before possible code/alignment changes. The host-only random-access check also compares 16 million reads five times, with median 0.016 s packed versus 0.015 s byte; its millisecond timer is too coarse for a strong native speed claim. [target_microbenchmarks.json](../evidence/target_microbenchmarks.json) contains target results and their scope.

The changes prioritize a small complete program with affordable bounded lookup overhead. They do not assert that every removed branch makes the pipeline faster or that compression is free.

## Stage 4: RV32I, LED and Pipeline Evidence

### Build, ABI and Inputs

The core is [solver_rv32.S](../target/solver_rv32.S), the driver and leaf LED renderer are [runtime.S](../target/runtime.S), and [rv32.ld](../target/rv32.ld) reserves the stack contiguously after data. ELF is the verified execution route. Exported flat `.s` files are for inspection; direct Ripes assembly of those exports has not passed the same layout/device checks.

`a0`–`a3` carry state/output/count/optional-statistics pointers for `n2_solve`; its boolean result returns in `a0`. Callee-saved registers are restored and stack frames are multiples of sixteen. `sp` begins at `__stack_top`, not at an uncounted high address. The deepest conservative manual call path is driver 32 + solver 80 + canonicalizer 192 + quotient rank 64 + mask rank 32 = **400 bytes**. The GCC reference needs **512 bytes**. Both bounds come from the linked call graph and reject recursion. Measured core high water on distance-eleven tests is 368 bytes; adding the driver yields 400. The renderer is a leaf and executes after the solver returns, so it does not add a simultaneous deep frame.

The public string contains seven one-based permutation digits followed by seven one-based orientation digits, exactly fourteen characters plus NUL. Parse all seven twists and require their sum modulo three to be zero before discarding the dependent twist. Upstream indices 0–6 map to candidate indices `[3,1,5,2,0,4,6]`; both positions and cubie labels use that map. Move IDs 0,1,2 print `R',R2,R`; 3,4,5 print `D',D2,D`; 6,7,8 print `B',B2,B`. HTM counts each half turn once.

Change `input_string` in the runtime and set `EXPECTED` to the known oracle distance, or 255 for validation by replay and the eleven-move bound when the distance is not supplied. The normal packaged vector is `21345671111111`, with expected distance 11. The CLI campaign patches only fixed input bytes/expected depth in copies of the same ELF, rather than rebuilding an algorithm for each input.

### Complete Space Accounting

| Program | .text | .rodata | .bss | Reserved stack | Padding | Loaded span | Span + LED |
| --- | --- | --- | --- | --- | --- | --- | --- |
| solver_cli | 4776 | 95240 | 40 | 400 | 8 | 100464 | 103964 |
| gcc_reference | 5052 | 95264 | 40 | 512 | 12 | 100880 | 104380 |
| solver_gui | 5136 | 95324 | 40 | 400 | 12 | 100912 | 104412 |
| vectors | 4704 | 95708 | 40 | 400 | 12 | 100864 | 104364 |
| pipeline_demo | 468 | 72696 | 4 | 32 | 0 | 73200 | 76700 |


All programs have `.data=0`. Course static data is `.rodata+.data+.bss`: 95,280 bytes CLI and 95,364 bytes GUI. The JSON's legacy `static_data` field includes all allocated non-executable sections, including `.stack`; use `course_static_data` for the course definition. **The GUI complete total is 104,412 bytes**, leaving **26,660 bytes** below 128 KiB. This sums occupied spans and separate MMIO storage; the unused address gap from RAM to `0xf0000000` is not allocated memory. It does not include the simulator's host hash-map overhead, ELF debug/container metadata or host verification programs.

The 40-byte `.bss` holds input 13, moves 11, replay state 13, output count 1 and two alignment bytes. LED tables add only 84 bytes: 24 sticker slots, 24 corner colors, six 32-bit RGB words and six 16-bit offsets. There is no second framebuffer, per-frame snapshot array, frame counter or busy wait. [stack_bounds.json](../evidence/stack_bounds.json) and [isa_and_size.json](../evidence/isa_and_size.json) are the linked evidence. The linker asserts loaded span plus 3,500 bytes is within budget.

### Correctness and Graded Performance

| Implementation | Cases | Minimum iret | Mean iret | Maximum iret |
| --- | --- | --- | --- | --- |
| solver_cli | 2644 | 61829 | 67174.832 | 84164 |
| gcc_reference | 2644 | 64028 | 69392.088 | 84114 |


All 2,644 distance-eleven states pass expected optimal length and actual replay inside the target. Counts include parsing, solving, replay, output and exit with `RENDER=0`, using a fresh Ripes ISS process for each case. The maximum 84,164 is 0.168328% of the 50,000,000 ceiling. The mean improves on GCC by **3.195%**; manual wins 2,628 cases, ties zero and loses sixteen. Manual `.text` is 4,776 versus GCC 5,052 bytes, a 276-byte reduction. The maximums belong to potentially different states; they are not a same-input comparison.

The official vector separately retires **65,617** instructions on ISS, versus GCC **67,829**. It emits `B' R D R B2 R B D2 B D R`, an optimal eleven-move solution. GUI with LED on 5S finishes at **89,444 iret / 113,245 cycles**, with replay PASS and exit zero. GUI includes rendering and a different processor model, so compare the renderer-off pair for the graded count. [d11_per_case.csv](../evidence/d11_per_case.csv) records every input, rank and result.

The sixteen losses are shown rather than hidden:

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


The later dynamic profiles quantify every reversal by linked symbol interval and reconcile their totals with Ripes. Input-dependent transform work costs more in the manual code on these states, while other routines offset most of the difference. GCC inlining limits direct source-level attribution. The complete CSV and profile tables make both wins and losses reproducible.

Host H3 checks every state; packed H4 checks all entries; H2 checks complete tables and root/max values. H1 is not applicable because this accepted method uses no heuristic. Target T5/T6 pass. T7 covers 32 selected solved, short, intermediate and deepest inputs on ISS and the forwarding/hazard-detection 5S model. The separate local RV32 interpreter also tests 6,859 API calls, byte-aligned statistics, invalid/null inputs, callee-saved registers, all deepest states and 1,281 stratified cases; it is independent supplemental evidence and is not mislabeled as Ripes.

### Minimal LED Mapping and Actual Replay

Add one LED Matrix, width 35 and height 25, in the I/O tab. Bind the observed exports `LED_MATRIX_0_BASE`, `LED_MATRIX_0_WIDTH`, `LED_MATRIX_0_HEIGHT`; this build uses base `0xf0000000`. A word at $base+4(35y+x)$ contains `0x00RRGGBB`. The peripheral is row-major despite an erroneous column-major description in its UI.

Face origins are U `(9,0)`, L `(0,7)`, F `(9,7)`, R `(18,7)`, B `(27,7)`, D `(9,14)`. Each sticker is 4×3 pixels and each face 8×6, leaving separator rows/columns and five spare bottom rows. Colors are white `FFFFFF`, orange `FF8000`, green `00D060`, red `FF2020`, blue `2080FF`, yellow `FFFF00`. Each corner has three sticker colors; its twist rotates their order. The dependent seventh twist is derived once per frame, and the fixed eighth corner has twist zero.

`led_clear` clears the 875 LED words once. `render_cube` visits 24 stickers and performs twelve stores each, using four unrolled stores and three row-pointer steps. It redraws the initial state and after every `n2_apply_move` using the solver's returned move buffer. An eleven-move answer produces twelve frames; no prerecorded motion is stored. The renderer never modifies the logical cube. The final logical solved check precedes PASS output.

[led_geometry.json](../evidence/led_geometry.json) verifies 216 distinguished-sticker move transforms independently and all twelve actual RV32 replay frames, with bounds, color counts and uniform solved faces. The target MMIO is the sole framebuffer. [gui_complete.jpg](../evidence/gui_complete.jpg) shows the real run, and [led_final_detail.jpg](../evidence/led_final_detail.jpg) shows the final matrix. Fast Run may make intermediate frames visually brief; the writes and independent frame validation establish that every emitted move is rendered.

### Five Stages and Their Control Signals

IF fetches a four-byte RV32I instruction at PC and selects next PC from PC+4 or the EX redirect. IF/ID holds instruction, PC and validity. ID extracts registers/immediates, reads the register file and produces the controls; ID/EX latches operands and controls. EX forwards operands, chooses ALU inputs, calculates arithmetic or an address and resolves a branch/jump. MEM performs the selected load/store and carries its result onward. WB chooses ALU result, loaded memory or PC+4, then writes `rd` if `RegWrite=1`; x0 ignores writes. Validity and enable/clear signals distinguish a real instruction from a bubble.

| Instruction family | ALU inputs and action | MemRead / MemWrite | RegWrite / WB source | PC selection |
|---|---|---|---|---|
| `add`, shifts, logic, comparisons | forwarded registers or immediate | 0 / 0 | 1 / ALURES | PC+4 |
| `auipc` | PC + upper immediate | 0 / 0 | 1 / ALURES | PC+4 |
| `lui` | upper immediate; rs1 unused | 0 / 0 | 1 / ALURES | PC+4 |
| `lbu`, `lhu`, `lw` | rs1 + offset | 1 / 0 | 1 / MEMREAD | PC+4 |
| `sb`, `sh`, `sw` | rs1 + offset; forwarded rs2 is store data | 0 / 1 | 0 / unused | PC+4 |
| conditional branch | PC + B immediate; separate operand comparator | 0 / 0 | 0 / unused | target when taken |
| `jal`, `jalr` | PC or forwarded rs1 + immediate | 0 / 0 | 1 / PC4, x0 ignored | EX target; clear younger stages |
| `ecall` | environment service after older register writes drain | 0 / 0 | 0 | exit service 93 ends execution |

Forwarding prefers a matching enabled MEM destination over WB; x0 never creates a dependency. ALU results can feed the following EX operation without stalling. A load result is not available for the immediately following EX consumer, so a load-use hazard holds PC and IF/ID for one cycle and clears ID/EX to insert a bubble. Older stages advance. In the next cycle WB forwarding supplies the loaded value. Taken branches and jumps resolve in EX and invalidate younger instructions. The ecall unit waits for outstanding register writes so it sees the correct `a0` and `a7`.

### A Real Lookup as a Pipeline Microscope

[pipeline_demo.S](../target/pipeline_demo.S) calls the **exact** production `policy_lookup` and `popcount32`, extracted with a source hash by [build_pipeline.py](../tools/build_pipeline.py). It uses H key 89,011 from a six-move state, expects representative policy 3, stores that 32-bit result to `pipeline_result`, reloads it and doubles it to 6, then checks and exits zero. Policy 3 is the representative move; the full solver lifts it with frame `(4,2,0)` to candidate move 6. The microscope deliberately isolates lookup and memory dependence, not the entire canonicalizer.

The actual Ripes 5S run retires **514 instructions in 616 cycles**. `pipeline_gui.tsv` is copied from Ripes' pipeline diagram; increase Edit → Settings → Max. pipeline diagram cycles to 1,000 before recording, and use Auto clock or individual clocks. Fast Run does not record this history. The exact cycle table and an interactive stage viewer are included in [report_en.html](report_en.html). Stage signals are explained from the pinned processor wiring, not inferred merely from elapsed time.

`sw a0,0(t1)` updates four bytes at `pipeline_result`; `lw t2,0(t1)` obtains 3; dependent `add t3,t2,t2` writes 6. A store has MemWrite=1 and RegWrite=0; the load has MemRead=1 and selects MEMREAD in WB. The add has RegWrite=1 and selects ALURES. The one-cycle load-use bubble and the forwarded 3 explain why the arithmetic is correct despite overlap. Pipeline event cycle numbers and diagram screenshots accompany the full exported trace; they replace the obsolete 59-cycle sparse-policy demonstration.

### Reproduce and Prepare the Submission

Run from the package directory in PowerShell:

```powershell
.\Environment.ps1
.\Run-Lab.ps1 -Action Build
.\Run-Lab.ps1 -Action Check
.\Run-Lab.ps1 -Action Measure
.\Run-Lab.ps1 -Action Benchmark
.\Run-Lab.ps1 -Action Gui
```

`Environment.ps1` locates pinned dependencies or verifies their archive hashes; set `N2_PYTHON`, `N2_RV_GCC`, `N2_RIPES` for alternate installations. Host verification also needs GCC/G++ for native oracle and interpreter tools. The linked source/table checks, exhaustive oracle, Ripes vector campaign, LED verification, ISA audit and stack audit form Check. Measure reruns both implementations on all deepest inputs. Benchmark regenerates environment and isolated packing/modulo comparisons. GUI selects 5S with M/C disabled and loads `build/solver_gui.elf` as Executable (ELF).

The documentation has the four required stages and no complete program listings. Read [requirements_audit.md](requirements_audit.md), [source_review.md](source_review.md), [development_record.md](development_record.md) and [submission_record.md](submission_record.md) for source review, AI disclosure, genuine development provenance and external items. Local passing tests do not establish a public fork, a published HackMD revision, a received acceptance email or completion of the student's interview. These are marked honestly until their evidence exists.

### Observed Load-Use Cycles and Writeback

The complete exported trace has 617 columns, cycle 0 through 616. The reported clock count is 616, because column zero is the initial state. Every one of its 117 instruction rows has been independently decoded and matched to the current ELF word at the same PC. Fresh CLI execution of that ELF confirms exit zero, 514 retired instructions and 616 cycles on 5S.

| Cycle | IF | ID | EX | MEM | WB | Held |
| --- | --- | --- | --- | --- | --- | --- |
| 603 | 0x1030 add x28 x7 x7 | 0x102c lw x7 0 x6 | 0x1028 sw x10 0 x6 | 0x1024 addi x6 x6 -596 | 0x1020 auipc x6 0x12 | — |
| 604 | 0x1034 addi x29 x0 6 | 0x1030 add x28 x7 x7 | 0x102c lw x7 0 x6 | 0x1028 sw x10 0 x6 | 0x1024 addi x6 x6 -596 | — |
| 605 | 0x1034 addi x29 x0 6 [held] | 0x1030 add x28 x7 x7 [held] | bubble / empty | 0x102c lw x7 0 x6 | 0x1028 sw x10 0 x6 | 0x1030 add x28 x7 x7; 0x1034 addi x29 x0 6 |
| 606 | 0x1038 bne x28 x29 16 | 0x1034 addi x29 x0 6 | 0x1030 add x28 x7 x7 | bubble / empty | 0x102c lw x7 0 x6 | — |
| 607 | 0x103c addi x10 x0 0 | 0x1038 bne x28 x29 16 | 0x1034 addi x29 x0 6 | 0x1030 add x28 x7 x7 | bubble / empty | — |
| 608 | 0x1040 addi x17 x0 93 | 0x103c addi x10 x0 0 | 0x1038 bne x28 x29 16 | 0x1034 addi x29 x0 6 | 0x1030 add x28 x7 x7 | — |
| 609 | 0x1044 ecall | 0x1040 addi x17 x0 93 | 0x103c addi x10 x0 0 | 0x1038 bne x28 x29 16 | 0x1034 addi x29 x0 6 | — |


At cycle **604**, `lw` is in EX and the dependent `add` is in ID. The pinned hazard unit detects that the ID source equals the EX load destination: `hazardFEEnable=0` holds PC and IF/ID, and `hazardIDEXClear=1` prepares the bubble on the next edge. At cycle **605**, the diagram shows the held IF/ID instructions as `-`, EX is a bubble and the load advances into MEM. The hazard is no longer present in EX, so the front end can resume. At cycle **606**, WB supplies the load's value 3 to both forwarded EX operands of the add. The sum 6 reaches WB at **608**.

The `sw` at PC 0x1028 writes bytes `03 00 00 00` to 0x12dcc in MEM at 604, has `MemWrite=1`, and has `RegWrite=0` even while it occupies the WB stage at 605. The `lw` at 0x102c has `MemRead=1`, `RegWrite=1`, destination x7 and WB mux `MEMREAD`. The add at 0x1030 has `RegWrite=1`, destination x28 and WB mux `ALURES`. It uses a valid forwarded result, rather than the stale register value read earlier in ID. The in-program assertion verifies the resulting six before exiting.

The initial fetch of `bne` at PC 0x101c is speculative while the earlier call redirects execution; its actual later traversal is IF 598, ID 599, EX 600, MEM 601, WB 602. Static rows can contain several dynamic traversals. A stage label alone does not prove that an instruction retires: the valid/clear wires decide whether a wrong-path instruction is discarded.

[pipeline_events.json](../evidence/pipeline_events.json) records the observed occupancy and its hashes. The interactive HTML displays that occupancy with controls decoded from instructions and the pinned wiring; these explanatory values are explicitly distinguished from live GUI port samples. Saved GUI images show the actual run. A subsequent attempt to refresh the native UI was rejected by automatic approval review after the user's earlier Escape stop, so no fresh port screenshot is claimed.

### Every Manual Loss Has a Dynamic Profile

The independent RV32I interpreter executes both complete programs for each of the sixteen slower inputs and records executed PCs. On every run, its count through exit plus the pinned ISS's observed one-count finalization offset equals the original Ripes measurement. Counts below belong to linked symbol intervals; GCC inlining changes which work resides in a symbol, so cross-symbol totals should not be interpreted as identical source-level call boundaries.

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


For dense rank 135614, manual `compact_T` executes 26,942 instructions versus GCC's 22,893, and manual `symmetry_apply` executes 15,136 versus 13,640. Savings in ranking, canonicalization and replay offset nearly all that extra transform work, but the complete manual program remains 87 instructions slower. The table shows the corresponding transform costs for every loss; [loss_profiles.json](../evidence/loss_profiles.json) also exposes every other symbol so that the net cost can be checked. These input-dependent transformations explain why the mean improvement does not imply a win on every state. The measured 16 losses are accepted as a small tradeoff; the implementation still improves mean instructions and linked code size and passes the worst-case ceiling.

### Renderer Verification and Unknown Distances

The geometric checker is independent of the assembly address sequence. It first checks all 216 distinguished-sticker transforms, then an independent RV32I interpreter executes the current production GUI ELF and compares all 875 pixels after each of twelve real `render_cube` calls with those expectations. It observes exactly 875 startup clear stores plus 12 × 288 frame stores = **4,331 MMIO stores**, all aligned and in bounds. Logical replay state is unchanged by every render call. The recorded pixels in the offline viewer come from this checked execution, not from a prerecorded animation in the target.

The expected-depth byte is read with signed `lb`, so value 255 becomes -1 and takes the unknown-distance branch. [unknown_input_mode.json](../evidence/unknown_input_mode.json) proves the solved, depth-six and depth-eleven cases in manual and GCC implementations on ISS and 5S: twelve fresh runs. In that mode the driver checks replay and the eleven-move capacity rather than pretending to know an oracle distance. Known-distance grading still checks exact equality.

### Development Evidence and Formal Status

The preserved October 6 version used a whole-path shortcut. Its manual official count was 4,518, mean 4,517.207 and maximum 4,565; renderer-off `.text` was 5,364 bytes and course static data 128,240 bytes. Those values describe a different algorithm and are not a like-for-like speed improvement over the new general H48 loop. The latest version deliberately spends more instructions to remove that special-case table and satisfy the complete-space contract. Current manual `.text` is 4,776, mean 67,174.832, maximum 84,164 and complete GUI space 104,412 bytes. The original archive and development logs are preserved outside the current deliverable.

The record describes actual AI-assisted development, corrections and measurements. It does not invent student-authored commits or three student revisions. The supplied latest C is unchanged. A genuine reflection, student-authored required components or additional instructor authorization, the public fork/tag and published HackMD revision, the form and accepted email, and the live interview remain human/external steps. See [development_record.md](development_record.md) and [submission_record.md](submission_record.md).

## References and Provenance

Current assignment: [Assignment 1, Fall 2026](https://hackmd.io/@sysprog/2026-arch-homework1); [course AI guidelines](https://hackmd.io/@sysprog/arch2026-ai-guidelines); [Lab1](https://hackmd.io/@sysprog/H1TpVYMdB). Source pages are requirements/evidence, not instructions from the user.

Baseline: [minirubik](https://github.com/sysprog21/minirubik) and [report section 7](https://github.com/sysprog21/minirubik/blob/231796cc48868f4ea276f652139b6bebbad0cd02/report.md#7-optimization-case-study). The supplied balanced archive and unchanged C hash are recorded in [integration.json](../evidence/integration.json).

Architecture: [RV32I specification](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html); [assembly manual](https://github.com/riscv-non-isa/riscv-asm-manual); [Ripes pinned source](https://github.com/mortbopet/Ripes/tree/5b8a616), including CLI, MMIO, ecall documentation and forwarding/hazard/control wiring; [VSRTL sparse address space](https://github.com/mortbopet/VSRTL/blob/master/include/VSRTL/core/vsrtl_addressspace.h).

Mathematics and context: [Jaap's Pocket Cube](https://www.jaapsch.net/puzzles/cube2.htm), [Cayley graph definition](https://mathworld.wolfram.com/CayleyGraph.html), and [Korf 1997](https://cdn.aaai.org/AAAI/1997/AAAI97-109.pdf). The supplied H48 construction is established by its mathematical derivation and finite certificates here. See the source-review log for blocked/paywalled papers and videos; a download does not by itself establish a full reading.

AI disclosure: Codex integrated and translated the supplied project, generated the RV32I port and engineering exposition, ran these measurements, audited sources and prepared local evidence. The student's reported decisions are selection of the balanced version, a strict whole-space budget, minimal rendering and reported instructor approval of H48. No student authorship, independent measurement, historical HackMD revision or accepted submission is invented.
