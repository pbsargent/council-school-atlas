"""Refresh atlas school details by verified Monday item identity, preserving geometry."""
import json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=Path(sys.argv[1]) if len(sys.argv)>1 else root.parent/'monday_map_source.json'
snapshot=json.loads(source.read_text())
assert snapshot['sources']['schools']['id']=='18420733851'
rows=snapshot['schools']
assert all(isinstance(r.get('column_values'),dict) and r.get('group') for r in rows), 'Incomplete column/group payload'
assert all(r.get('id') and r.get('name') for r in rows)
assert len({r['id'] for r in rows})==len(rows), 'Duplicate source identities'
by={r['id']:r for r in rows}
path=root/'public/data/CapitolAreaCouncil_Schools.geojson';geo=json.loads(path.read_text());warnings=[]
fields={'school_district':'text_mkqz1pqj','county':'text_mm3cvs9s','grades':'text_mkqzxf7q','administrator':'text_mkqz1zj0','phone':'text_mkqzf8gn','website':'text_mkqzkkg3'}
for f in geo['features']:
 p=f['properties'];r=by.get(str(p['monday_item_id']))
 if not r:
  warnings.append(p['school_name']);continue
 c=r['column_values'];p['school_name']=r['name']
 for field,col in fields.items():
  assert col in c, f'Missing column {col}'
  p[field]=c[col] # Preserve real nulls.
 parts=[c.get('text_mkqz8vkr'),c.get('text_mkqzd9jj')]
 p['address']=', '.join(x for x in parts if isinstance(x,str) and x.strip()) or None
 p['directory_updated_at']=snapshot['extracted_at']
path.write_text(json.dumps(geo)+'\n')
# Synchronize the sanitized rebuild directory by verified mapped identities.
directory=json.loads((root/'data/school-directory.json').read_text())
def key(name,district):return (str(name or '').strip().upper(),str(district or '').strip().upper())
features={key(f['properties']['school_name'],f['properties']['school_district']):f for f in geo['features']}
for s in directory['schools']:
 f=features.get(key(s.get('name'),s.get('schoolDistrict')))
 if not f:continue
 p=f['properties']
 for field,camel in [('school_name','name'),('school_district','schoolDistrict'),('county','county'),('grades','grades'),('administrator','administrator'),('phone','phone'),('website','website'),('address','address')]:s[camel]=p.get(field)
directory['extractedAt']=snapshot['extracted_at'];(root/'data/school-directory.json').write_text(json.dumps(directory,indent=2)+'\n')
manifestpath=root/'public/data/data-manifest.json';m=json.loads(manifestpath.read_text());m['school_data_at']=snapshot['extracted_at'];m['school_refresh']={'source_records':len(rows),'mapped_records':len(geo['features']),'unresolved_identities':warnings};manifestpath.write_text(json.dumps(m,indent=2)+'\n')
print(json.dumps(m['school_refresh']))
