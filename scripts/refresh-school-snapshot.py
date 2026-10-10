"""Reconcile source identities, preserve verified pins and account for new unlocated schools."""
import sys,copy
from pathlib import Path
from atlas_refresh import ROOT,OUTPUT,read_json,atomic_json,school_source,SCHOOL_FIELDS,coordinates,inside
source=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT.parent/'monday_map_source.json'
snapshot=school_source(source);by={str(r['id']):r for r in snapshot['schools']}
geo=read_json(OUTPUT/'public/data/CapitolAreaCouncil_Schools.geojson');manifest=read_json(OUTPUT/'public/data/data-manifest.json')
oldids=set(manifest.get('school_source_ids',[]))
if not oldids:raise ValueError('Missing verified school identity baseline; seed from previously published source before reconciliation')
existing={str(f['properties']['monday_item_id']):f for f in geo['features']}
if len(existing)!=len(geo['features']):raise ValueError('Duplicate mapped school identity')
council=read_json(OUTPUT/'public/data/CapitolAreaCouncil.geojson')
lookup={}
# Read only coordinates and public school identity from the existing map export.
locationpath=ROOT.parent/'joint-scout-night-map/public/map-data.json'
if locationpath.exists():
 for s in read_json(locationpath).get('schools',[]):lookup.setdefault((str(s.get('name','')).strip().upper(),str(s.get('schoolDistrict','')).strip().upper()),[]).append(s)
features=[];warnings=[];unlocated=[]
for id,row in by.items():
 c=row['column_values'];prior=existing.get(id)
 if not prior and str(c['text_mm3cxysd'] or '').upper()!='INDEPENDENT':continue
 if not prior:
  matches=lookup.get((row['name'].strip().upper(),str(c['text_mkqz1pqj'] or '').strip().upper()),[])
  if len(matches)!=1:
   unlocated.append({'id':id,'name':row['name'],'reason':'Ambiguous school location' if matches else 'No verified location'});continue
  coords=coordinates(matches[0].get('lat'),matches[0].get('lon'))
  if not coords or not inside(coords,council):
   unlocated.append({'id':id,'name':row['name'],'reason':'No verified in-council location'});continue
  labels=[v.strip() for v in str(c['dropdown_mkqzfzs3'] or '').split(',') if v.strip() in manifest['scouting_district_names']]
  prior={'type':'Feature','id':'school-'+id,'geometry':{'type':'Point','coordinates':coords},'properties':{'monday_item_id':id,'district_type':'INDEPENDENT','scouting_district':', '.join(labels) or 'Unassigned','source':'CAC Schools snapshot with preserved mapped school coordinates'}}
 f=copy.deepcopy(prior);p=f['properties'];p['school_name']=row['name']
 for field,col in SCHOOL_FIELDS.items():p[field]=c[col]
 parts=[c['text_mkqz8vkr'],c['text_mkqzd9jj']];p['address']=', '.join(x for x in parts if isinstance(x,str) and x.strip()) or None
 p['directory_updated_at']=snapshot['extracted_at'];features.append(f)
removed=sorted(set(existing)-set(by));geo['features']=features
manifest['school_data_at']=snapshot['extracted_at'];manifest['school_source_ids']=sorted(by)
manifest['school_refresh']={'source_records':len(by),'mapped_records':len(features),'unmapped_source_records':len(by)-len(features),'new_source_ids':sorted(set(by)-oldids),'removed_source_ids':sorted(oldids-set(by)),'removed_mapped_ids':removed,'unlocated_independent_schools':unlocated,'unresolved_identities':warnings}
manifest['counts']['schools']=len(features);manifest['counts']['assigned_schools']=sum(f['properties'].get('scouting_district') not in ('',None,'Unassigned') for f in features);manifest['counts']['unassigned_schools']=len(features)-manifest['counts']['assigned_schools']
# Rebuild directory directly by identity, rather than a name join that can lose renamed schools.
directory={'extractedAt':snapshot['extracted_at'],'schools':[]}
for f in features:
 p=f['properties'];lon,lat=f['geometry']['coordinates'];s={'id':p['monday_item_id'],'lat':lat,'lon':lon,'scoutingDistrict':p.get('scouting_district')}
 for field,camel in [('school_name','name'),('school_district','schoolDistrict'),('county','county'),('grades','grades'),('administrator','administrator'),('phone','phone'),('website','website'),('address','address'),('nces_id','ncesId')]:s[camel]=p.get(field)
 directory['schools'].append(s)
atomic_json(OUTPUT/'public/data/CapitolAreaCouncil_Schools.geojson',geo);atomic_json(OUTPUT/'data/school-directory.json',directory);atomic_json(OUTPUT/'public/data/data-manifest.json',manifest)
print(manifest['school_refresh'])
