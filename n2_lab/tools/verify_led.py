"""Independent geometric sticker check for all 9 moves, plus actual replay frames."""
import hashlib,json,re
from pathlib import Path
from build import ROOT
COLORS=[[5,3,4],[5,2,3],[0,4,3],[0,3,2],[5,4,1],[5,1,2],[0,1,4],[0,2,1]]
NORMAL=[(0,1,0),(-1,0,0),(0,0,1),(1,0,0),(0,0,-1),(0,-1,0)]
POS=[(-1 if i&4 else 1,1 if i&2 else -1,1 if i&1 else -1) for i in range(8)]
SLOTS=[6,2,7,3,14,23,20,13,15,19,21,9,11,18,17,8,10,22,16,12,5,1,4,0]
ORIGINS=[(9,0),(0,7),(9,7),(18,7),(27,7),(9,14)]
def nums(name):
    text=(ROOT/'reference/n2_core_data.c').read_text()
    body=re.search(r'\b'+name+r'\s*(?:\[[^]]*\])+\s*=\s*\{(.*?)\};',text,re.S)[1]
    return [int(x,0) for x in re.findall(r'0x[\da-fA-F]+|\d+',body)]
SRC=nums('n2_b8_move_src');DELTA=nums('n2_b8_move_delta')
def turn(p,o,m):return [p[SRC[m*8+i]] for i in range(8)],[(o[SRC[m*8+i]]+DELTA[m*8+i])%3 for i in range(8)]
def rotate(v,axis):
    x,y,z=v
    return [(x,-z,y),(-z,y,x),(y,-x,z)][axis]
def main():
    # Give every sticker a distinct ID. This detects errors that six repeated colors hide.
    for m in range(9):
        axis=m//3;sign=[1,-1,-1][axis];expected={}
        for c in range(8):
            for s in range(3):
                p=POS[c];n=NORMAL[COLORS[c][s]]
                if p[axis]==sign:
                    for _ in range(m%3+1):p=rotate(p,axis);n=rotate(n,axis)
                dest=POS.index(p);slot=COLORS[dest].index(NORMAL.index(n));expected[dest,slot]=3*c+s
        p,o=turn(list(range(8)),[0]*8,m)
        for dest in range(8):
            for slot in range(3):assert expected[dest,slot]==3*p[dest]+(slot+o[dest])%3,(m,dest,slot)
    # Exact emitted path from the actual RV32 run, independently replayed with cubie tables.
    import csv
    rows=list(csv.DictReader((ROOT/'evidence/rv32_abi_d11.csv').open()))
    row=next(x for x in rows if x['state']=='192456');path=list(map(int,row['path']))
    p=list(range(8));p[3],p[1]=p[1],p[3];o=[0]*8;frames=[]
    for frame in range(12):
        facelets=[COLORS[p[x&7]][((x>>3)+o[x&7])%3] for x in SLOTS]
        assert [facelets.count(c) for c in range(6)]==[4]*6
        pixels=[0]*875
        rgb=[0xffffff,0xff8000,0x00d060,0xff2020,0x2080ff,0xffff00]
        for i,color in enumerate(facelets):
            ox,oy=ORIGINS[i//4];ox+=(i&1)*4;oy+=((i&2)>>1)*3
            for y in range(oy,oy+3):
                for x in range(ox,ox+4):assert 0<=x<35 and 0<=y<25;pixels[y*35+x]=rgb[color]
        frames.append(dict(frame=frame,perm=p,twist=o,facelets=facelets,pixels=pixels))
        if frame<11:p,o=turn(p,o,path[frame])
    assert p==list(range(8)) and o==[0]*8
    assert frames[-1]['facelets']==sum(([c]*4 for c in range(6)),[])
    # Observe the actual linked renderer. Geometry above remains an independent
    # expected image, so a production address/color/stride error cannot pass by
    # merely generating the same high-level replay in Python.
    from rv32_trace import CPU,symbols
    elf=(ROOT/'build/solver_gui.elf').read_bytes();fn=symbols(elf);cpu=CPU(elf)
    mmio=[];active=None;observed=[];memory_base=0xf0000000
    def write(a,n,v):
        if a>=memory_base:
            assert n==4 and a%4==0 and memory_base<=a<memory_base+3500,(hex(a),n)
            mmio.append((a,v))
    cpu.write_hook=write
    while cpu.exit is None:
        if cpu.pc==fn['render_cube']:
            assert active is None
            active=(cpu.r[1],len(mmio),bytes(cpu.load(fn['replay_state']+i,1) for i in range(13)))
        if active and cpu.pc==active[0]:
            index=len(observed);assert index<12
            pixels=[cpu.load(memory_base+4*i,4) for i in range(875)]
            assert pixels==frames[index]['pixels'],('renderer frame mismatch',index)
            assert len(mmio)-active[1]==288
            assert active[2]==bytes(cpu.load(fn['replay_state']+i,1) for i in range(13))
            observed.append(dict(frame=index,stores=288,pixel_sha256=hashlib.sha256(b''.join(v.to_bytes(4,'little') for v in pixels)).hexdigest()))
            active=None
        cpu.step()
    assert cpu.exit==0 and 'PASS cases=1' in cpu.output and len(observed)==12
    assert len(mmio)==875+12*288
    assert mmio[:875]==[(memory_base+4*i,0) for i in range(875)]
    payload=dict(distinct_stickers_checked=9*24,all_9_physical_rotations_pass=True,path=path,frames=frames,
                 execution_scope='Independent host RV32I interpreter executes current production ELF; every MMIO word is compared with geometric expectations.',
                 elf_sha256=hashlib.sha256(elf).hexdigest(),actual_iret=cpu.iret,actual_output=cpu.output,
                 initial_clear_stores=875,total_mmio_stores=len(mmio),observed_frames=observed)
    (ROOT/'evidence/led_geometry.json').write_text(json.dumps(payload,indent=2)+'\n')
    print('PASS 216 distinct-sticker transformations; 12 actual ELF renderer frames; 4331 in-bounds MMIO stores; unchanged logical states; solved faces')
if __name__=='__main__':main()
