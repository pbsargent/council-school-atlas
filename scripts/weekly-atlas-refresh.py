"""Count gate and transactional preparation. Publishing stays an explicitly verified step."""
import argparse,datetime,fcntl,json,os,shutil,subprocess,sys,urllib.request
from pathlib import Path
from atlas_refresh import ROOT,read_json,school_source,unit_source,atomic_json
parser=argparse.ArgumentParser();parser.add_argument('action',choices=['check','prepare','verify']);parser.add_argument('--school-source',type=Path,default=ROOT.parent/'monday_map_source.json');parser.add_argument('--unit-source',type=Path,default=Path('/Volumes/MacProData/Capitol Area Council Dashboard/Capitol Area Council/PinDataReport.csv'));args=parser.parse_args()
state=ROOT/'.atlas-refresh';state.mkdir(exist_ok=True)
def live(name):
 url='https://pbsargent.github.io/council-school-atlas/data/'+name+'?verify='+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')
 with urllib.request.urlopen(url,timeout=30) as f:return json.load(f)
with (state/'refresh.lock').open('w') as lock:
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:raise SystemExit('Another atlas refresh is running')
 published=live('data-manifest.json');published_units=live('unit-pins.json')
 if args.action=='verify':
  local=read_json(ROOT/'public/data/data-manifest.json');units=read_json(ROOT/'public/data/unit-pins.json')
  if published!=local or published_units!=units:raise SystemExit('Live data does not match local candidate; baseline has NOT advanced')
  atomic_json(state/'last-verified-publication.json',{'verifiedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'schoolCount':published['school_refresh']['source_records'],'unitCount':len(published_units['units']),'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()});print('Live published data matches candidate exactly');raise SystemExit(0)
 schools=school_source(args.school_source,fresh=True);rows=unit_source(args.unit_source,fresh=True)
 before={'schools':published['school_refresh']['source_records'],'units':len(published_units['units'])};after={'schools':len(schools['schools']),'units':len(rows)}
 if len({u['id'] for u in published_units['units']})!=before['units']:raise SystemExit('Invalid published unit baseline')
 result={'before':before,'after':after,'refreshNeeded':before!=after};print(json.dumps(result))
 if args.action=='check' or not result['refreshNeeded']:raise SystemExit(0)
 if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise SystemExit('Working tree has changes; reconcile before preparing refresh')
 # Always stage against deployed baselines, including the verified full identity inventory.
 if not published.get('school_source_ids'):raise SystemExit('Published school identity inventory is unavailable')
 stage=state/'candidate'
 if stage.exists():shutil.rmtree(stage)
 for name in ['public/data','data']:
  shutil.copytree(ROOT/name,stage/name)
 atomic_json(stage/'public/data/data-manifest.json',published);atomic_json(stage/'public/data/unit-pins.json',published_units)
 env={**os.environ,'ATLAS_OUTPUT_ROOT':str(stage)}
 subprocess.run([sys.executable,str(ROOT/'scripts/refresh-school-snapshot.py'),str(args.school_source)],env=env,check=True)
 subprocess.run([sys.executable,str(ROOT/'scripts/import-unit-pins.py'),str(args.unit_source)],env=env,check=True)
 names=['public/data/data-manifest.json','public/data/unit-pins.json','public/data/CapitolAreaCouncil_Schools.geojson','data/school-directory.json']
 backups={name:(ROOT/name).read_bytes() for name in names}
 try:
  for name in names:atomic_json(ROOT/name,read_json(stage/name))
 except BaseException:
  for name,blob in backups.items():(ROOT/name).write_bytes(blob)
  raise
 atomic_json(state/'candidate-summary.json',result)
 print('Candidate prepared; validate both builds and tests before committing. Run verify after deployment. Published baseline remains authoritative.')
