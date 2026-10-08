"""Render offline engineering companions from current Markdown and GUI trace.

No browser automation, remote scripts or solver memory are required.
The Markdown files remain the full mathematical deliverables.
"""
from pathlib import Path
import html,json,re
from build import ROOT

STYLE='''body{margin:0;background:#eef3f6;color:#172839;font:16px/1.65 system-ui,sans-serif}main{max-width:1160px;margin:auto;padding:32px 40px;background:white}h1{font-size:34px;line-height:1.2}h2{margin-top:44px;border-top:1px solid #ccd9e2;padding-top:20px}a{color:#135d95}code{background:#edf3f7;padding:2px 4px}pre{white-space:pre-wrap;background:#142d42;color:#edf6fc;padding:16px;overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:8px;border:1px solid #d3dfe7;text-align:left;vertical-align:top}th{background:#edf3f7}.scroll{overflow:auto}.cards,.stages{display:grid;gap:10px;grid-template-columns:repeat(5,minmax(0,1fr))}.stage{padding:12px;border:1px solid #ccdce5;background:#f4f8fb;overflow-wrap:anywhere}.stage b{color:#15577e}.stage pre{font-size:12px;padding:8px;margin:6px 0}.muted{font-size:14px;color:#596c7c}.note{padding:14px;background:#fff4d9;border-left:4px solid #bd923c}button{padding:7px 12px;margin:4px;border:1px solid #9bb2c2;background:white;border-radius:4px;cursor:pointer}input[type=range]{width:60%;vertical-align:middle}img{max-width:100%;height:auto}canvas{width:350px;max-width:100%;height:auto;background:#000;image-rendering:pixelated}nav{display:flex;flex-wrap:wrap;gap:18px}.bubble{color:#7e8992}.signal{font:13px/1.5 Consolas,monospace;white-space:pre-wrap}.hazard{background:#fff0d2}.math-source{white-space:pre-wrap;font-family:Consolas,monospace}@media(max-width:800px){main{padding:18px}.stages{grid-template-columns:1fr 1fr}h1{font-size:27px}}@media print{body{background:white}main{padding:0}button,input{display:none}.stages{break-inside:avoid}pre{background:#f2f2f2;color:black}.scroll{overflow:visible}}'''

def inline(s):
    s=html.escape(s)
    s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
    s=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',s)
    s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',lambda m:'<a href="'+m[2]+'">'+m[1]+'</a>',s)
    return s

def markdown(s):
    lines=s.splitlines();out=[];i=0
    while i<len(lines):
        line=lines[i]
        if not line.strip():i+=1;continue
        if line.startswith('```'):
            j=i+1
            while j<len(lines) and not lines[j].startswith('```'):j+=1
            out.append('<pre><code>'+html.escape('\n'.join(lines[i+1:j]))+'</code></pre>');i=j+1;continue
        if re.match(r'^#{1,6} ',line):
            n=len(line.split(' ')[0]);out.append(f'<h{n}>'+inline(line[n+1:])+f'</h{n}>');i+=1;continue
        if line.startswith('| ') and i+1<len(lines) and re.match(r'^\|[ -]+\|',lines[i+1]):
            rows=[line]+lines[i+2:];actual=[line];j=i+2
            while j<len(lines) and lines[j].startswith('|'):actual.append(lines[j]);j+=1
            out.append('<div class="scroll"><table>')
            for k,row in enumerate(actual):
                tag='th' if k==0 else 'td'
                out.append('<tr>'+''.join(f'<{tag}>'+inline(c.strip())+f'</{tag}>' for c in row.strip('|').split('|'))+'</tr>')
            out.append('</table></div>');i=j;continue
        if line.startswith(('- ','* ')) or re.match(r'^\d+\. ',line):
            out.append('<ul>');j=i
            while j<len(lines) and (lines[j].startswith(('- ','* ')) or re.match(r'^\d+\. ',lines[j])):
                out.append('<li>'+inline(re.sub(r'^(?:[-*]|\d+\.) ', '',lines[j]))+'</li>');j+=1
            out.append('</ul>');i=j;continue
        j=i+1
        while j<len(lines) and lines[j].strip() and not lines[j].startswith(('#','```','|','- ','* ')):j+=1
        out.append('<p>'+inline(' '.join(lines[i:j]))+'</p>');i=j
    return '\n'.join(out)

JS=r'''
const stages=['IF','ID','EX','MEM','WB'];
let clock=0, timer=null;
const get=id=>document.getElementById(id);
function occupancy(c){
  const map=Object.fromEntries(stages.map(s=>[s,null]));
  for(const row of trace.rows){
    let stage=row.cells[c];let held=false;
    if(stage==='-'){held=true;let k=c-1;while(k>=0&&row.cells[k]==='-')k--;stage=row.cells[k];}
    if(stages.includes(stage))map[stage]={...row,held};
  }
  return map;
}
function controls(row,stage){
  if(!row)return 'valid=0 / bubble';
  const op=Number.parseInt(row.word,16)&127,rd=(Number.parseInt(row.word,16)>>>7)&31;
  const load=op===3,store=op===35,branch=op===99,jump=op===103||op===111,sys=op===115;
  const wr=(!store&&!branch&&!sys),wb=load?'MEMREAD':jump?'PC4':'ALURES';
  if(stage==='IF')return 'PC mux: '+(clock===7?'EX redirect':'PC+4 or EX redirect')+'\nPC enable: '+(clock===604?0:1);
  if(stage==='ID')return 'valid=1\nID/EX clear: '+(clock===604?1:0)+'\nIF/ID enable: '+(clock===604?0:1);
  if(stage==='EX')return 'ALU input 1: '+(op===55?'unused (LUI)':(op===23||op===111||branch)?'PC':'forwarded REG1')+'\nALU input 2: '+(op===51?'forwarded REG2':'IMM')+'\n'+(clock===606?'Forward A/B: WB (3)':'Forwarding: model-dependent; see wiring');
  if(stage==='MEM')return 'MemRead='+Number(load)+'\nMemWrite='+Number(store)+'\n'+(clock===604&&store?'[0x12dcc] ← 03 00 00 00':clock===605&&load?'load word = 3':'');
  return 'RegWrite='+Number(wr)+'\nrd=x'+rd+(rd===0?' (writes ignored)':'')+'\nWB mux='+ (wr?wb:'unused')+(clock===606?'\nvalue=3':clock===608?'\nvalue=6':'');
}
function renderCycle(c){
  clock=Math.max(0,Math.min(616,Number(c)));get('cycle').value=clock;get('label').textContent='Cycle '+clock+' / 616';
  const map=occupancy(clock);
  get('stages').replaceChildren();
  for(const stage of stages){
    const div=document.createElement('div');div.className='stage'+(clock===604||clock===605?' hazard':'');
    const title=document.createElement('b');title.textContent=stage;div.append(title);
    const pre=document.createElement('pre');pre.textContent=map[stage]?map[stage].pc+' '+map[stage].instruction+(map[stage].held?'\nheld (GUI “-”)':''):'bubble / empty';div.append(pre);
    const sig=document.createElement('div');sig.className='signal';sig.textContent=controls(map[stage],stage);div.append(sig);get('stages').append(div);
  }
  get('event').textContent=clock===604?'Load is in EX; consumer is in ID. Hazard detection disables PC and IF/ID and clears ID/EX for the next edge. The older store writes the four bytes for 3.':clock===605?'The trace shows held IF/ID and an EX bubble. The load accesses MEM, while the older store passes WB with RegWrite=0.':clock===606?'The load reaches WB and forwards 3 to both operands of add in EX. The sum is 6.':clock===608?'The add reaches WB and writes 6 to x28.':clock===7?'The call resolves in EX. Younger instructions are flushed; the early speculative fetch of the later bne does not retire.':'Explore every observed stage occupancy. Control descriptions are derived from the instruction and pinned model, not sampled GUI ports.';
}
function play(){if(timer){clearInterval(timer);timer=null;return;}timer=setInterval(()=>{renderCycle(clock+1);if(clock===616){clearInterval(timer);timer=null;}},150);}
function renderLed(n){
  n=Number(n);get('frameLabel').textContent='Frame '+n+' / 11'+(n?' — applied '+["R'","R2","R","D'","D2","D","B'","B2","B"][led.path[n-1]]:' — initial input');
  const ctx=get('led').getContext('2d');const pixels=led.frames[n].pixels;
  for(let i=0;i<pixels.length;i++){ctx.fillStyle='#'+pixels[i].toString(16).padStart(6,'0');ctx.fillRect((i%35)*10,Math.floor(i/35)*10,10,10);}
}
get('cycle').addEventListener('input',e=>renderCycle(e.target.value));get('frame').addEventListener('input',e=>renderLed(e.target.value));
renderCycle(604);renderLed(0);
'''

def document(title,body,script='',lang='en'):
    return '<!doctype html><html lang="'+lang+'"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>'+STYLE+'</style></head><body><main>'+body+'</main><script>'+script+'</script></body></html>'

def main():
    doc=ROOT/'docs';ev=ROOT/'evidence'
    trace=json.loads((ev/'pipeline_events.json').read_text());led=json.loads((ev/'led_geometry.json').read_text())
    for row in led['frames']:
        assert len(row['pixels'])==875
    en=(doc/'teaching_en.md').read_text(encoding='utf-8')
    stage4=en[en.index('## Stage 4:'):en.index('## References and Provenance') if '## References and Provenance' in en else len(en)]
    body='''<h1>Balanced H48: RV32I and pipeline laboratory</h1><p>Engineering companion · 8 October 2026, GMT+8</p><nav><a href="teaching_en.md">Full English teaching notes</a><a href="teaching_zh.md">完整中文教學</a><a href="requirements_audit.md">Requirements audit</a><a href="submission_record.md">Submission record</a></nav>
<p class="note">All 2,644 deepest states pass; maximum 84,164 retired instructions. Complete GUI guest space is 104,412 bytes including stack and LED. Method approval is reported by the user. This AI-assisted engineering package does not establish student authorship or formal course acceptance.</p>
<h2>Observed pipeline, cycles 0–616</h2><p>The stages below come from the real Ripes GUI export, checked against all 117 current instruction words. The displayed controls are decoded explanations based on the pinned model. They are not live port measurements.</p>
<button onclick="renderCycle(clock-1)">Previous</button><button onclick="renderCycle(clock+1)">Next</button><button onclick="play()">Play / pause</button><button onclick="renderCycle(604)">Load-use</button><input id="cycle" type="range" min="0" max="616" value="604" aria-label="Pipeline cycle"><span id="label"></span><div id="stages" class="stages"></div><p id="event" class="note"></p>
<p class="muted">At cycle 604 the hazard controls prepare the edge that creates the cycle-605 EX bubble. The consumer resumes in EX at 606 with WB forwarding. “-” is a held stage, not a retired NOP. Total clock count is 616; the diagram includes the initial cycle-0 column.</p>
<h2>Every actual replay frame</h2><p>These pixels were recorded from an independent RV32 interpreter executing the production renderer and move buffer. This is a replay viewer, not a GUI screenshot or a second framebuffer in the solver.</p><input id="frame" type="range" min="0" max="11" value="0" aria-label="LED replay frame"><span id="frameLabel"></span><p><canvas id="led" width="350" height="250"></canvas></p>
<h2>Saved Ripes GUI evidence</h2><figure><img src="../evidence/gui_complete.jpg" alt="Actual Ripes solver run, PASS and completion counters"><figcaption>Actual balanced-version GUI run. The later signed EXPECTED load fix changes only unknown-distance mode; known distance 11 follows the same path. Fresh current-ELF CLI checks are recorded separately.</figcaption></figure><figure><img src="../evidence/pipeline_complete.jpg" alt="Actual pipeline run completed in Ripes"><figcaption>Actual Ripes pipeline completion. Current instruction image agrees with the saved trace; fresh CLI confirms 514 retired / 616 cycles.</figcaption></figure>'''+markdown(stage4)
    script='const trace='+json.dumps(trace,separators=(',',':'))+';\nconst led='+json.dumps(led,separators=(',',':'))+';\n'+JS
    (doc/'report_en.html').write_text(document('Balanced H48 RV32I laboratory',body,script),encoding='utf-8')
    zh=(doc/'requirements_audit.md').read_text(encoding='utf-8')+'\n'+(doc/'submission_record.md').read_text(encoding='utf-8')
    (doc/'completion_zh.html').write_text(document('作業本機技術完成狀態','<h1>本機技術完成狀態</h1><p><a href="teaching_zh.md">中文版完整教學</a> · <a href="report_en.html">互動 pipeline／LED 教材</a></p>'+markdown(zh),lang='zh-Hant'),encoding='utf-8')
    # Save the exact browser script separately for a local, browser-free JS check.
    (ROOT/'build/report_script.js').write_text(script,encoding='utf-8')
    print('Generated current offline English / Chinese HTML companions')
if __name__=='__main__':main()
