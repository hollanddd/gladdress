import unittest
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from address_parser import AddressParser

class AddressParserTest(unittest.TestCase):
    ap = None
    
    def setUp(self):
        self.ap = AddressParser()
    
    def test_load_zip_codes(self):
        self.assertTrue(self.ap.zip_codes.has_key('00210'))
        self.assertEqual('Portsmouth', self.ap.zip_codes['00211']['city_name'])
        self.assertEqual('AK', self.ap.zip_codes['99950']['state'])
    
    def test_load_suffixes(self):
        self.assertEqual('ALY', self.ap.suffixes['ALLEY'])
    
    def test_load_cities(self):
        self.assertTrue('wisconsin rapids' in self.ap.cities)
    
    def test_load_state_abbreviations(self):
        self.assertEqual('WI', self.ap.states['Wisconsin'])
    

if __name__ == '__main__':
    unittest.main()