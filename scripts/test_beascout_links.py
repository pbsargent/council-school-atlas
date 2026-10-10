import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('beascout',Path(__file__).parent/'resolve-beascout-links.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class LinkTests(unittest.TestCase):
 def setUp(self):self.url='https://beascout.scouting.org/units/5d8f6736-4bd3-47ec-8d81-095707dc2dc2';self.body='<title>Pack 0002 Capitol Area Council BSA</title>legacyUnitId:25921,'
 def test_exact_internal_identity_verified(self):self.assertIsNone(mod.verify_page(self.body,self.url,'25921','Pack 0002, Council'))
 def test_general_search_is_not_unit_link(self):self.assertIsNotNone(mod.verify_page(self.body,'https://beascout.scouting.org/search','25921','Pack 0002'))
 def test_same_number_different_internal_id_rejected(self):self.assertIsNotNone(mod.verify_page(self.body,self.url,'3333','Pack 0002'))
 def test_program_identity_contradiction_rejected(self):self.assertIsNotNone(mod.verify_page(self.body,self.url,'25921','Troop 0002'))
 def test_unknown_host_rejected(self):self.assertIsNotNone(mod.verify_page(self.body,self.url.replace('beascout.scouting.org','example.com'),'25921','Pack 0002'))
if __name__=='__main__':unittest.main()
