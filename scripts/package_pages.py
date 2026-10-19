"""Copy a verified Data report build into the static GitHub Pages tree."""
from pathlib import Path
import hashlib, json, shutil

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'reports/ixn-qqq-voo'
DIST=APP/'dist'
DOCS=ROOT/'docs'
DEST=DOCS/'reports/ixn-qqq-voo-2026-10-19'
OFFLINE=APP/'.data-app-offline/exports/ixn-qqq-voo-2026-10-19.html'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((DIST/'data-app-build.json').read_text())
for key in ['html','snapshot']:
    p=DIST/manifest[key]['path']
    if sha(p)!=manifest[key]['sha256']: raise ValueError(f'Verified build mismatch: {p.name}')
snapshot=json.loads((DIST/manifest['snapshot']['path']).read_text())
if snapshot.get('buildStatus')!='complete': raise ValueError('Report authoring is incomplete')
if not OFFLINE.is_file(): raise FileNotFoundError('Export the verified offline HTML first')
DEST.mkdir(parents=True,exist_ok=True)
for p in DIST.iterdir():
    if p.is_file(): shutil.copy2(p,DEST/p.name)
(DOCS/'downloads').mkdir(parents=True,exist_ok=True)
shutil.copy2(OFFLINE,DOCS/'downloads'/OFFLINE.name)
(DOCS/'.nojekyll').touch()
release={'researchAsOf':'2026-10-19','appId':snapshot['id'],'htmlSha256':manifest['html']['sha256'],
         'snapshotSha256':manifest['snapshot']['sha256'],'offlineSha256':sha(OFFLINE),
         'queries':len(snapshot['queries']),'reviewedRows':sum(len(q['rows']) for q in snapshot['queries'].values())}
(DOCS/'release-manifest.json').write_text(json.dumps(release,indent=2)+'\n')
print(json.dumps(release))
