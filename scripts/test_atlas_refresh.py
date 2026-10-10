import unittest,tempfile,json,csv,subprocess,sys,os
from pathlib import Path
from atlas_refresh import school_source,unit_source,coordinates,atomic_json,REQUIRED,UNIT_COLUMNS
class RefreshTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def school(self):
  return {'sources':{'schools':{'id':'18420733851'}},'extracted_at':'2026-10-10T05:03:20-05:00','schools':[{'id':'1','name':'School','group':{'id':'g'},'column_values':dict.fromkeys(REQUIRED,None)}]}
 def test_missing_payload_rejected_but_real_nulls_kept(self):
  p=self.root/'source.json';d=self.school();atomic_json(p,d);self.assertIsNone(school_source(p)['schools'][0]['column_values']['text_mkqz1pqj']);del d['schools'][0]['column_values']['text_mkqz1pqj'];atomic_json(p,d)
  with self.assertRaises(ValueError):school_source(p)
 def test_duplicate_school_identity_rejected(self):
  d=self.school();d['schools']*=2;p=self.root/'s.json';atomic_json(p,d)
  with self.assertRaises(ValueError):school_source(p)
 def test_coordinate_corruption_is_not_silently_blank(self):
  self.assertIsNone(coordinates('',''))
  for lat,lon in [('NaN','-97'),('30',''),('91','-97')]:
   with self.assertRaises(ValueError):coordinates(lat,lon)
 def test_duplicate_and_truncated_unit_rows_rejected(self):
  row=dict.fromkeys(UNIT_COLUMNS,'');row.update(unitid='1',unitname='Pack 1',districtname='District',pinstatus='Active',applystatus='Active')
  p=self.root/'u.csv'
  with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=sorted(UNIT_COLUMNS));w.writeheader();w.writerow(row);w.writerow(row)
  with self.assertRaises(ValueError):unit_source(p)
  p.write_text('unitid,unitname\n1,Pack 1\n')
  with self.assertRaises(ValueError):unit_source(p)
 def test_failed_atomic_write_preserves_previous_file(self):
  p=self.root/'old.json';atomic_json(p,{'ok':1})
  with self.assertRaises(ValueError):atomic_json(p,{'bad':float('nan')})
  self.assertEqual(json.loads(p.read_text()),{'ok':1})
 def test_reconciliation_removes_deleted_ids_preserves_geometry_and_accounts_for_additions(self):
  stage=self.root/'stage';(stage/'public/data').mkdir(parents=True);(stage/'data').mkdir()
  feature=lambda id: {'type':'Feature','geometry':{'type':'Point','coordinates':[-97.7,30.3]},'properties':{'monday_item_id':id,'school_name':'Prior name','school_district':'District','scouting_district':'Armadillo'}}
  atomic_json(stage/'public/data/CapitolAreaCouncil_Schools.geojson',{'type':'FeatureCollection','features':[feature('1'),feature('2')]})
  atomic_json(stage/'public/data/CapitolAreaCouncil.geojson',{'type':'FeatureCollection','features':[{'geometry':{'type':'Polygon','coordinates':[[[-100,28],[-95,28],[-95,33],[-100,33],[-100,28]]]}}]})
  atomic_json(stage/'public/data/data-manifest.json',{'school_source_ids':['1','2'],'scouting_district_names':['Armadillo'],'counts':{}})
  source=self.school();source['schools'][0]['name']='Renamed school';new=json.loads(json.dumps(source['schools'][0]));new.update(id='3',name='New unlocated school');new['column_values']['text_mm3cxysd']='INDEPENDENT';source['schools'].append(new)
  path=self.root/'source.json';atomic_json(path,source)
  subprocess.run([sys.executable,str(Path(__file__).parent/'refresh-school-snapshot.py'),str(path)],env={**os.environ,'ATLAS_OUTPUT_ROOT':str(stage)},check=True,stdout=subprocess.DEVNULL)
  result=json.loads((stage/'public/data/CapitolAreaCouncil_Schools.geojson').read_text())['features']
  self.assertEqual(len(result),1);self.assertEqual(result[0]['geometry'],feature('1')['geometry']);self.assertEqual(result[0]['properties']['school_name'],'Renamed school')
  m=json.loads((stage/'public/data/data-manifest.json').read_text())['school_refresh'];self.assertEqual(m['removed_mapped_ids'],['2']);self.assertEqual(m['new_source_ids'],['3']);self.assertEqual(m['unlocated_independent_schools'][0]['id'],'3')
if __name__=='__main__':unittest.main()
