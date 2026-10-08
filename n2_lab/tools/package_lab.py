"""Create and verify a local delivery ZIP. Does not publish or submit anything."""
import argparse, hashlib, json, re, zipfile
from pathlib import Path
from build import ROOT
from audit_delivery import main as audit

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def selected():
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if '__pycache__' in rel.parts or rel.parts[0] == 'toolchains':
            continue
        if len(rel.parts) > 1 and rel.parts[:2] in (('build', 'host'), ('build', 'case_measurements')):
            continue
        if rel.parts[0] == 'build' and re.fullmatch(r'vector_\d+\.elf', path.name):
            continue
        if path.name == 'teaching_en_for_hackmd.md':
            continue
        yield path

def package(destination):
    destination = Path(destination).resolve()
    assert destination.suffix == '.zip' and not destination.is_relative_to(ROOT.resolve())
    audit()
    sizes = json.loads((ROOT / 'evidence/isa_and_size.json').read_text())
    evidence = json.loads((ROOT / 'evidence/delivery_audit.json').read_text())
    manifest = dict(date='2026-10-08', title='Balanced H48 complete local engineering delivery', source_archive_sha256=json.loads((ROOT/'evidence/integration.json').read_text())['input_archive_sha256'], reference_c_sha256=sha(ROOT / 'reference/n2_solver.c'), elf_sha256={k:v['sha256'] for k,v in sizes.items()}, guest_gui_bytes=evidence['gui_total_bytes'], worst_d11_retired=evidence['worst_iss_retired'], english_characters_crlf=evidence['documentation_counts']['teaching_en.md']['characters_crlf'], tests='PASS; see delivery_audit.json and individual raw evidence', formal_submission='NOT SUBMITTED / no accepted email', method_approval='User reports instructor approval of H48; not treated as an AI authorship exemption', human_or_external_steps=evidence['personal_or_external_steps'], gui_refresh='Native refresh rejected after earlier Escape stop; existing genuine GUI images/trace plus current CLI and independent renderer/word checks retained', archive_exclusions=['Local toolchain installations (pinned portable Ripes archive included)', 'Python caches', 'Host test executables and scratch patched ELF copies', 'Example HackMD link-conversion note'], reproducibility='Prebuilt ELF + pinned Ripes ZIP for demonstration; sources and scripts for rebuilding and checking. See docs/delivery_zh.md.')
    (ROOT / 'evidence/delivery_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    hashes = ROOT / 'SHA256SUMS.txt'
    hashes.write_text(''.join(sha(p)+'  '+p.relative_to(ROOT).as_posix()+'\n' for p in selected() if p != hashes), encoding='utf-8')
    files = list(selected())
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for file in files:
            archive.write(file, ROOT.name + '/' + file.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        assert len(archive.infolist()) == len(files)
        for file in files:
            name = ROOT.name + '/' + file.relative_to(ROOT).as_posix()
            assert hashlib.sha256(archive.read(name)).hexdigest() == sha(file), name
        assert all(not n.startswith('/') and '..' not in Path(n).parts for n in archive.namelist())
    result = dict(status='PASS', archive=str(destination), bytes=destination.stat().st_size, members=len(files), sha256=sha(destination), scope='ZIP CRC and SHA-256 equality for every selected current file; safe relative members')
    destination.with_suffix('.zip.sha256').write_text(result['sha256']+'  '+destination.name+'\n')
    destination.with_suffix('.verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', required=True)
    package(parser.parse_args().output)
