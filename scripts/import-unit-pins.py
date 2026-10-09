"""Import only public-facing unit fields; never copy contact details."""
import csv,json,datetime,sys
from pathlib import Path
source=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/Volumes/MacProData/Capitol Area Council Dashboard/Capitol Area Council/PinDataReport.csv')
with source.open(encoding='cp1252',newline='') as f: rows=list(csv.DictReader(f))
units=[]
for r in rows:
 coords=None
 try:
  lat,lon=float(r['latitude']),float(r['longitude'])
  if -90<=lat<=90 and -180<=lon<=180: coords=[lon,lat]
 except ValueError: pass
 units.append(dict(id=r['unitid'],name=r['unitname'],program=r['unitname'].split()[0],district=r['districtname'],pinStatus=r['pinstatus'],pinView=r['pinview'],applicationStatus=r['applystatus'],coordinates=coords,pinAddress=r['unitbeascoutaddress'],meetingAddress=r['meetingaddress'],meetingSchedule=r['meetingschedule'],meetingWeek=r['meetingweek'],meetingDay=r['meetingday'],meetingStart=r['meetingstarttime'],meetingEnd=r['meetingendtime'],website=r['unitwebsite'],updatedWithinYear=r['strupdatedinayear'],lastModified=r['lastmodifieddate']))
output=Path(__file__).resolve().parents[1]/'public/data/unit-pins.json'
output.write_text(json.dumps({'source':'Council PinDataReport.csv','importedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'units':units},indent=2)+'\n')
print(f'Imported {len(units)} units; {sum(u["coordinates"] is None for u in units)} without usable coordinates')
