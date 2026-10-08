"""Verify the 21 exact affine identities defining T, using integers modulo 3."""
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
src=(root/'reference/h48_t_simple_data.c').read_text()
def nums(name):
    m=re.search(r'\b'+name+r'\s*(?:\[[^]]*\])+\s*=\s*\{(.*?)\};',src,re.S)
    if not m: raise ValueError(name)
    return [int(t,0) for t in re.findall(r'0x[0-9a-fA-F]+|\d+',re.sub(r'(?<=[0-9a-fA-F])[uUlL]+\b','',m[1]))]
dst,rv,ctl=nums('h48_t_dst'),nums('h48_t_perm_R'),nums('h48_t_ori_ctl')
R=[rv[i:i+6] for i in range(0,126,6)]
A=[];b=[];qp=[]
for q in range(21):
    rows=[];bias=[]
    assert dst[q]&7 < 7 and dst[q]>>3 < 3
    qp.append(3*(dst[q]&7)+(dst[q]>>3))
    assert sorted(R[q])==list(range(6))
    for i in range(5):
        item=(ctl[q]>>(5*i))&31;si=item&7;c=item>>3
        assert si in (0,1,2,3,4,7) and 0<=c<3
        rows.append([1]*5 if si==7 else [2 if j==si else 0 for j in range(5)])
        bias.append(c)
    A.append(rows);b.append(bias)
for q in range(21):
    j=qp[q]
    assert qp[j]==q
    assert [R[q][R[j][i]] for i in range(6)]==list(range(6))
    prod=[[sum(A[j][i][k]*A[q][k][l] for k in range(5))%3 for l in range(5)] for i in range(5)]
    assert prod==[[int(i==l) for l in range(5)] for i in range(5)]
    bias=[(sum(A[j][i][k]*b[q][k] for k in range(5))+b[j][i])%3 for i in range(5)]
    assert bias==[0]*5
    print(f'q={q:2} qprime={j:2} chart_inverse=PASS permutation_inverse=PASS matrix_product=I bias=0')
print('ALL_21_AFFINE_INVOLUTION_IDENTITIES_PASS')
