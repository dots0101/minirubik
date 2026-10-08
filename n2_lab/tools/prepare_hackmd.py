"""Convert only local Markdown links after actual fork/tag identities exist.

Writes a separate reviewable note; it never publishes or changes permissions.
"""
import argparse,re
from pathlib import Path,PurePosixPath
from urllib.parse import quote
from build import ROOT

def prepare(repo,ref,folder='n2_lab'):
    assert re.fullmatch(r'https://github.com/[A-Za-z0-9-]+/[A-Za-z0-9._-]+',repo),'Use the real public fork URL without a trailing slash.'
    assert re.fullmatch(r'[A-Za-z0-9._-]+',ref),'Use an existing submitted tag or commit SHA.'
    assert re.fullmatch(r'[A-Za-z0-9._/-]+',folder) and '..' not in folder.split('/')
    source=ROOT/'docs/teaching_en.md';body=source.read_text(encoding='utf-8')
    def change(m):
        label,path=m.groups()
        if re.match(r'\w+:',path) or path.startswith('#'):return m[0]
        target=(source.parent/path).resolve()
        assert target.is_relative_to(ROOT.resolve()) and target.is_file(),path
        relative=target.relative_to(ROOT).as_posix()
        return '['+label+']('+repo+'/blob/'+quote(ref,safe='')+'/'+quote(folder+'/'+relative,safe='/')+')'
    body=re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)',change,body)
    assert len(body.replace('\n','\r\n'))<100000
    destination=ROOT/'build/teaching_en_for_hackmd.md';destination.write_text(body,encoding='utf-8',newline='\n')
    return destination
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--repo-url',required=True);parser.add_argument('--ref',required=True);parser.add_argument('--folder',default='n2_lab');a=parser.parse_args()
    print(prepare(a.repo_url,a.ref,a.folder))
