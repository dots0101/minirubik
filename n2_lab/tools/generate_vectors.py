import itertools,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
F=[3,1,5,2,0,4,6]; INV=[F.index(x) for x in range(7)]
def state_from_dense(n):
    p,o=divmod(n,729); available=list(range(7)); perm=[]
    for f in (720,120,24,6,2,1,1):
        q,p=divmod(p,f);perm.append(available.pop(q))
    twists=[0]*7
    for i in range(5,-1,-1): o,twists[i]=divmod(o,3)
    twists[6]=(-sum(twists))%3
    return perm,twists
def upstream_string(p,o):
    return ''.join(str(INV[p[F[i]]]+1) for i in range(7))+''.join(str(o[F[i]]+1) for i in range(7))
def main():
    dist=(ROOT/'reference/host_oracle/full_distance.bin').read_bytes()
    records=[]; seen=set()
    for d in range(12):
        n=dist.index(d); p,o=state_from_dense(n);s=upstream_string(p,o)
        records.append(dict(input=s,depth=d,dense=n,role=f'distance-{d}'));seen.add(s)
    hard='21345671111111'
    # The official vector swaps upstream positions 0 and 1, candidate slots 3 and 1.
    perm=list(range(7));perm[3],perm[1]=perm[1],perm[3]
    pr=next(i for i,x in enumerate(itertools.permutations(range(7))) if list(x)==perm)
    assert dist[pr*729]==11
    if hard not in seen: records.append(dict(input=hard,depth=11,dense=pr*729,role='official'));seen.add(hard)
    seed=0x719a
    while len(records)<32:
        seed=(1664525*seed+1013904223)&0xffffffff;n=seed%3674160
        p,o=state_from_dense(n);s=upstream_string(p,o)
        if s in seen: continue
        records.append(dict(input=s,depth=dist[n],dense=n,role='deterministic sample'));seen.add(s)
    text=['.section .rodata','.balign 4','.globl test_vectors','test_vectors:']
    for r in records: text.append('.byte '+','.join(map(str,r['input'].encode()+bytes([0,r['depth']]))))
    (ROOT/'target/test_vectors.S').write_text('\n'.join(text)+'\n')
    (ROOT/'evidence/test_vectors.json').write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps(records[:4]));print('vectors',len(records),'official dense',pr*729)
if __name__=='__main__': main()
