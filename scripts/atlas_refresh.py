"""Shared validation and atomic output for atlas refreshes."""
import csv, json, math, os, tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(os.environ.get('ATLAS_OUTPUT_ROOT', ROOT))
SCHOOL_FIELDS = {'school_district':'text_mkqz1pqj','county':'text_mm3cvs9s','grades':'text_mkqzxf7q','administrator':'text_mkqz1zj0','phone':'text_mkqzf8gn','website':'text_mkqzkkg3'}
REQUIRED = set(SCHOOL_FIELDS.values()) | {'text_mkqz8vkr','text_mkqzd9jj','text_mm3cxysd','dropdown_mkqzfzs3'}
UNIT_COLUMNS = {'unitid','unitname','districtname','pinstatus','pinview','applystatus','latitude','longitude','unitbeascoutaddress','meetingaddress','meetingschedule','meetingweek','meetingday','meetingstarttime','meetingendtime','unitwebsite','strupdatedinayear','lastmodifieddate','zipcode'}
def read_json(path): return json.loads(Path(path).read_text())
def atomic_json(path, data):
 path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
 blob=json.dumps(data,indent=2,allow_nan=False)+'\n'
 fd,temp=tempfile.mkstemp(dir=path.parent,prefix='.'+path.name)
 try:
  with os.fdopen(fd,'w') as f: f.write(blob); f.flush(); os.fsync(f.fileno())
  os.replace(temp,path)
 finally:
  if os.path.exists(temp): os.unlink(temp)
def coordinates(lat,lon):
 if lat in ('',None) and lon in ('',None): return None
 try: a,b=float(lat),float(lon)
 except (ValueError,TypeError): raise ValueError('Invalid or incomplete coordinates')
 if not (math.isfinite(a) and math.isfinite(b) and -90<=a<=90 and -180<=b<=180): raise ValueError('Coordinates outside valid range')
 return [b,a]
def school_source(path, fresh=False):
 d=read_json(path)
 if d.get('sources',{}).get('schools',{}).get('id')!='18420733851': raise ValueError('Unexpected school source board')
 rows=d.get('schools')
 if not isinstance(rows,list) or not rows: raise ValueError('Empty or missing school source')
 ids=[]
 for row in rows:
  if not row.get('id') or not str(row.get('name','')).strip(): raise ValueError('Invalid school identity')
  c=row.get('column_values')
  if not isinstance(c,dict) or not REQUIRED<=c.keys() or not isinstance(row.get('group'),dict) or not row['group'].get('id'): raise ValueError('Incomplete school columns or group payload')
  ids.append(str(row['id']))
 if len(set(ids))!=len(ids): raise ValueError('Duplicate school IDs')
 stamp=datetime.fromisoformat(d['extracted_at'])
 if stamp.tzinfo is None: raise ValueError('School extraction requires timezone')
 if fresh and not timedelta(0)<=datetime.now(timezone.utc)-stamp<=timedelta(days=7): raise ValueError('School source is stale or future-dated')
 return d
def unit_source(path, fresh=False):
 path=Path(path)
 if fresh and not 0<=datetime.now(timezone.utc).timestamp()-path.stat().st_mtime<=7*86400: raise ValueError('Unit source is stale or future-dated')
 with path.open(encoding='cp1252',newline='') as f:
  reader=csv.DictReader(f)
  if not UNIT_COLUMNS<=set(reader.fieldnames or []): raise ValueError('Missing required unit columns')
  rows=list(reader)
 if not rows: raise ValueError('Empty unit source')
 ids=[]
 for r in rows:
  if None in r or any(r.get(k) is None for k in UNIT_COLUMNS): raise ValueError('Malformed or truncated unit row')
  if not r['unitid'].strip() or not r['unitname'].strip() or not r['districtname'].strip(): raise ValueError('Invalid unit identity')
  if r['pinstatus'] not in ('Active','Inactive') or r['applystatus'] not in ('Active','Inactive'): raise ValueError('Invalid unit status')
  if r['unitname'].split()[0] not in ('Pack','Troop','Crew','Post','Ship'): raise ValueError('Unknown unit program')
  if not r['unitid'].isdigit(): raise ValueError('Unit internal ID must be numeric')
  coordinates(r['latitude'],r['longitude']);ids.append(r['unitid'])
 if len(set(ids))!=len(ids): raise ValueError('Duplicate unit IDs')
 return rows
def inside(point,collection):
 def ring_hit(ring):
  x,y=point; hit=False
  for a,b in zip(ring,ring[1:]+ring[:1]):
   if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:hit=not hit
  return hit
 for f in collection['features']:
  g=f['geometry'];polys=[g['coordinates']] if g['type']=='Polygon' else g['coordinates']
  for rings in polys:
   if ring_hit(rings[0]) and not any(ring_hit(r) for r in rings[1:]):return True
 return False
