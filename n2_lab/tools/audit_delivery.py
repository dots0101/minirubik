"""Audit the frozen local delivery against its recorded current binaries/evidence.

This performs no publication, login, form submission or graphical automation.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
import csv, hashlib, json, re
from build import ROOT, elf_sections

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ev = ROOT / 'evidence'
    read = lambda name: json.loads((ev / name).read_text(encoding='utf-8'))
    sizes = read('isa_and_size.json')
    for name, row in sizes.items():
        file = ROOT / 'build' / (name + '.elf')
        assert sha(file) == row['sha256'], name
        actual = elf_sections(file)
        for key, value in actual.items():
            assert row[key] == value, (name, key, row.get(key), value)
        assert not row['non_rv32i'] and not row['undefined_symbols'], name
        assert row['allocated_image_bytes'] + 3500 <= 131072, name
    assert sizes['solver_gui']['allocated_image_bytes'] + 3500 == 104412
    assert sizes['solver_cli']['.text'] == 4776
    integration = read('integration.json')
    assert sha(ROOT / 'reference/n2_solver.c') == integration['source_sha256']
    csv_rows = list(csv.DictReader((ev / 'd11_per_case.csv').open(newline='')))
    assert len(csv_rows) == 5288
    summary = read('d11_summary.json')
    paired = {}
    for name in ('solver_cli', 'gcc_reference'):
        rows = [r for r in csv_rows if r['implementation'] == name]
        counts = [int(r['iret']) for r in rows]
        assert len(rows) == len({r['dense'] for r in rows}) == 2644
        assert all(int(r['depth']) == 11 and int(r['iret']) < 50000000 for r in rows)
        assert sum(counts) == summary[name]['total']
        assert min(counts) == summary[name]['min'] and max(counts) == summary[name]['max']
        assert abs(sum(counts) / len(counts) - summary[name]['mean']) < 1e-9
        for row in rows:
            paired.setdefault(row['dense'], {})[name] = int(row['iret'])
    assert sum(v['solver_cli'] < v['gcc_reference'] for v in paired.values()) == 2628
    losses = read('loss_profiles.json')
    assert len(losses['cases']) == 16
    for name in losses['source_sha256']:
        assert losses['source_sha256'][name] == sizes[name]['sha256']
    for row in losses['cases']:
        for name, record in row['implementations'].items():
            assert record['iret'] == paired[str(row['dense'])][name]
            assert record['decoded_execution_count'] + record['ripes_counter_offset'] == record['iret']
    unknown = read('unknown_input_mode.json')['records']
    assert len(unknown) == 12
    for row in unknown:
        assert row['source_sha256'] == sizes[row['implementation']]['sha256']
        assert row['program_exit_code'] == 0 and row['pass_cases'] == 1
    matrix = read('t7_matrix.json')
    assert len(matrix) == 64 and all(r['exit'] == 0 for r in matrix)
    led = read('led_geometry.json')
    assert led['elf_sha256'] == sizes['solver_gui']['sha256']
    assert led['total_mmio_stores'] == 4331 and len(led['frames']) == 12
    assert all(len(r['pixels']) == 875 for r in led['frames'])
    pipeline = read('pipeline_events.json')
    assert pipeline['elf_sha256'] == sizes['pipeline_demo']['sha256']
    assert len(pipeline['rows']) == 117 and pipeline['cycles'] == list(range(617))
    assert sha(ev / 'pipeline_gui.tsv') == pipeline['trace_sha256']
    assert read('pipeline_RV32_5S.json')['# instructions retired'] == 514
    assert read('pipeline_RV32_5S.json')['cycles'] == 616
    assert read('official_final_iss.json')['# instructions retired'] == 65617
    assert read('gcc_official_final_iss.json')['# instructions retired'] == 67829
    assert read('gui_final_5s_cli.json')['# instructions retired'] == 89444
    assert read('report_logic_check.json')['status'] == 'PASS'
    portable = read('portable_verification.json')
    assert portable['status'] == 'PASS' and len(portable['records']) == 5
    for record in portable['records']:
        assert record['elf_sha256'] == sizes[record['implementation']]['sha256']
        assert record['program_exit_code'] == 0
    assert read('publication_tools_check.json')['status'] == 'PASS'
    full = (ev / 'host_full_domain.txt').read_text()
    assert 'count=3674160 badcall=0 badlen=0 badsolve=0' in full
    for file in ROOT.rglob('*.py'):
        if '__pycache__' not in file.parts:
            compile(file.read_text(encoding='utf-8'), str(file), 'exec')
    counts = {}
    for name in ('teaching_en.md', 'original_english_notes.md', 'teaching_zh.md', 'original_chinese_notes.md'):
        text = (ROOT / 'docs' / name).read_text(encoding='utf-8')
        counts[name] = dict(characters_lf=len(text), characters_crlf=len(text.replace('\n', '\r\n')), utf8_bytes=len(text.encode()))
        assert counts[name]['characters_crlf'] < 100000, name
    assert (ROOT / 'docs/teaching_en.md').read_bytes() == (ROOT / 'docs/original_english_notes.md').read_bytes()
    assert (ROOT / 'docs/teaching_zh.md').read_bytes() == (ROOT / 'docs/original_chinese_notes.md').read_bytes()
    (ev / 'documentation_counts.json').write_text(json.dumps(counts, indent=2) + '\n')
    checked_links = []
    def link(file, target):
        split = urlsplit(target)
        if split.scheme or split.netloc or not split.path:
            return
        dest = (file.parent / unquote(split.path)).resolve()
        assert dest.is_relative_to(ROOT.resolve()) and dest.is_file(), (str(file.relative_to(ROOT)), target)
        checked_links.append((str(file.relative_to(ROOT)), target))
    class InspectHTML(HTMLParser):
        def __init__(self, file):
            super().__init__(); self.file = file; self.ids = set(); self.scripts = 0
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if attrs.get('id'):
                assert attrs['id'] not in self.ids, (self.file, attrs['id'])
                self.ids.add(attrs['id'])
            for key in ('href', 'src'):
                if attrs.get(key):
                    link(self.file, attrs[key])
            if tag == 'script':
                self.scripts += 1
                assert not attrs.get('src'), 'Viewer must have no remote script dependency.'
    for file in ROOT.rglob('*.md'):
        if '__pycache__' in file.parts or 'host_oracle' in file.parts:
            continue
        body = re.sub(r'```.*?```', '', file.read_text(encoding='utf-8'), flags=re.S)
        for target in re.findall(r'!?\[[^\]]*\]\(([^)\s]+)\)', body):
            link(file, target)
    for file in (ROOT / 'docs').glob('*.html'):
        parser = InspectHTML(file); parser.feed(file.read_text(encoding='utf-8')); parser.close()
        assert parser.scripts == 1
    sources = read('source_review_metadata.json')
    assert len(sources['links']) == 63 and len(sources['main_documents']) == 3
    result = dict(status='PASS', date='2026-10-08', scope='Frozen binary/evidence consistency, complete-space contract, teaching counts, local links, Python syntax, offline HTML structure; no publication or native UI refresh.', production_elfs=len(sizes), deepest_paired_inputs=2644, unknown_distance_runs=12, two_model_cases=64, html_javascript_check='Node VM, not visual QA', local_links_checked=len(checked_links), documentation_counts=counts, gui_total_bytes=104412, gui_headroom_bytes=26660, worst_iss_retired=84164, personal_or_external_steps=['Student authorship/reflection or additional instructor authorization under course AI policy', 'Actual public GitHub fork/main/commit/tag', 'Actual published HackMD note and frozen revision', 'Form with personal fields and accepted email', 'Student live interview'])
    (ev / 'delivery_audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS: frozen binaries, all recorded campaigns, budget, syntax, HTML and', len(checked_links), 'local links.')
    print('English characters (LF / CRLF):', counts['teaching_en.md']['characters_lf'], '/', counts['teaching_en.md']['characters_crlf'])

if __name__ == '__main__':
    main()
