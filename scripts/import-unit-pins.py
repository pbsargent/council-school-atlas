"""Import public unit fields after complete validation; retain known pins on coordinate loss."""
import sys,datetime
from pathlib import Path
from atlas_refresh import ROOT,OUTPUT,read_json,atomic_json,unit_source,coordinates,inside
source=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/Volumes/MacProData/Capitol Area Council Dashboard/Capitol Area Council/PinDataReport.csv')
rows=unit_source(source)
previous={u['id']:u for u in read_json(OUTPUT/'public/data/unit-pins.json')['units']}
council=read_json(OUTPUT/'public/data/CapitolAreaCouncil.geojson');units=[];warnings=[]
for r in rows:
 coords=coordinates(r['latitude'],r['longitude']);retained=False
 if coords is None and previous.get(r['unitid'],{}).get('coordinates'):
  coords=previous[r['unitid']]['coordinates'];retained=True;warnings.append({'id':r['unitid'],'reason':'Missing source coordinates; prior verified pin retained'})
 if coords and not inside(coords,council):raise ValueError(f'Unit {r["unitid"]} pin outside council boundary')
 units.append(dict(id=r['unitid'],name=r['unitname'],program=r['unitname'].split()[0],district=r['districtname'],pinStatus=r['pinstatus'],pinView=r['pinview'],applicationStatus=r['applystatus'],coordinates=coords,pinAddress=r['unitbeascoutaddress'],meetingAddress=r['meetingaddress'],meetingSchedule=r['meetingschedule'],meetingWeek=r['meetingweek'],meetingDay=r['meetingday'],meetingStart=r['meetingstarttime'],meetingEnd=r['meetingendtime'],website=r['unitwebsite'],updatedWithinYear=r['strupdatedinayear'],lastModified=r['lastmodifieddate'],coordinatesRetained=retained))
atomic_json(OUTPUT/'public/data/unit-pins.json',{'source':'Council PinDataReport.csv','sourceModifiedAt':datetime.datetime.fromtimestamp(source.stat().st_mtime,datetime.timezone.utc).isoformat(),'importedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'warnings':warnings,'units':units})
print(f'Imported {len(units)} unique units; {sum(u["coordinates"] is None for u in units)} without usable coordinates; {len(warnings)} retained pins')
