import unittest
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from address import Address, AddressParser

class AddressTest(unittest.TestCase):
    parser = None
    
    def setUp(self):
        self.parser = AddressParser()
    
    def test_checks_work_in_isolation(self):
	      addr = Address(None, self.parser)
	      addr.check_city('San Francisco')
	      self.assertEqual('San Francisco', addr.city)
  	
    def test_zip_integer(self):
	      addr = Address(None, self.parser)
	      addr.check_zip(12345)
	      self.assertEqual('12345', addr.zipCode)
	  
    def test_check_zip(self):
	      addr = Address(None, self.parser)
	      addr.check_zip('12345')
	      self.assertEqual('12345', addr.zipCode)
	  
    def test_malibu(self):
        # expected failure as parser only breaks into components
	      addr = Address('205 1105 14 90210', self.parser)
	      self.assertEqual('90210', addr.zipCode)
	      self.assertEqual('205', addr.house_number)
	  
    def test_no_comma_address(self):
        addr = Address('2 N. Park Street Madison WI 53703', self.parser)
        self.assertEqual('2', addr.house_number)
        self.assertEqual('N.', addr.street_prefix)
        self.assertEqual('Park', addr.street)
        self.assertEqual('St.', addr.street_suffix)
        self.assertEqual('Madison', addr.city)
        self.assertEqual('WI', addr.state)
        self.assertEqual('53703', addr.zipCode)
        self.assertEqual(None, addr.apartment)
    
    def test_basic_full_address(self):
        addr = Address('2 N. Park Street, Madison, WI 53703', self.parser)
        self.assertEqual('2', addr.house_number)
        self.assertEqual('N.', addr.street_prefix)
        self.assertEqual('Park', addr.street)
        self.assertEqual('St.', addr.street_suffix)
        self.assertEqual('Madison', addr.city)
        self.assertEqual('WI', addr.state)
        self.assertEqual('53703', addr.zipCode)
        self.assertEqual(None, addr.apartment)
    
    def test_multi_address(self):
        addr = Address('416/418 N. Carroll St.', self.parser)
        self.assertEqual('416', addr.house_number)
        self.assertEqual('N.', addr.street_prefix)
        self.assertEqual('Carroll', addr.street)
        self.assertEqual('St.', addr.street_suffix)
        self.assertEqual(None, addr.city)
        self.assertEqual(None, addr.state)
        self.assertEqual(None, addr.zipCode)
        self.assertEqual(None, addr.apartment)
    
    def test_no_suffix(self):
        addr = Address('230 Lakelawn', self.parser)
        self.assertEqual('230', addr.house_number)
        self.assertEqual(None, addr.street_prefix)
        self.assertEqual('Lakelawn', addr.street)
        self.assertEqual(None, addr.street_suffix)
        self.assertEqual(None, addr.city)
        self.assertEqual(None, addr.state)
        self.assertEqual(None, addr.zipCode)
        self.assertEqual(None, addr.apartment)
    
    def test_streets_named_after_states(self):
        addr = Address('504 W. Washington Ave.', self.parser)
        self.assertEqual('504', addr.house_number)
        self.assertEqual('W.', addr.street_prefix)
        self.assertEqual('Washington', addr.street)
        self.assertEqual('Ave.', addr.street_suffix)
        self.assertEqual(None, addr.city)
        self.assertEqual(None, addr.state)
        self.assertEqual(None, addr.zipCode)
        self.assertEqual(None, addr.apartment)
    
    def test_hash_apartment(self):
        addr = Address('407 West Doty St. #2', self.parser)
        self.assertEqual('407', addr.house_number)
        self.assertEqual('W.', addr.street_prefix)
        self.assertEqual('Doty', addr.street)
        self.assertEqual('St.', addr.street_suffix)
        self.assertEqual(None, addr.city)
        self.assertEqual(None, addr.state)
        self.assertEqual(None, addr.zipCode)
        self.assertEqual('#2', addr.apartment)
    
    def test_stray_dash_apartment(self):
        addr = Address('407 West Doty St. - #2', self.parser)
        self.assertEqual('407', addr.house_number)
        self.assertEqual('W.', addr.street_prefix)
        self.assertEqual('Doty', addr.street)
        self.assertEqual('St.', addr.street_suffix)
        self.assertEqual(None, addr.city)
        self.assertEqual(None, addr.state)
        self.assertEqual(None, addr.zipCode)
        self.assertEqual('#2', addr.apartment)
    
    def test_suffixless_street_with_city(self):
        addr = Address('431 West Johnson, Madison, WI', self.parser)
        self.assertEqual('431', addr.house_number)
        self.assertEqual('W.', addr.street_prefix)
        self.assertEqual('Johnson', addr.street)
        self.assertEqual(None, addr.street_suffix)
        self.assertEqual('Madison', addr.city)
        self.assertEqual('WI', addr.state)
        self.assertEqual(None, addr.zipCode)
        self.assertEqual(None, addr.apartment)
    
    def test_simple_address_issue_(self):
	    addr = Address('351 King St. #400, San Francisco, CA, 94158', self.parser)
	    self.assertEqual('351', addr.house_number)
	    self.assertEqual('San Francisco', addr.city)
	    self.assertEqual('#400', addr.apartment)
	

class AddressParserTest(unittest.TestCase):
    ap = None
    
    def setUp(self):
        self.ap = AddressParser()
    
    def test_load_suffixes(self):
        self.assertEqual('ALY', self.ap.suffixes['ALLEY'])
    
    def test_load_cities(self):
        self.assertTrue('wisconsin rapids' in self.ap.cities)
    
    def test_load_states(self):
        self.assertEqual('WI', self.ap.states['Wisconsin'])
    

if __name__ == '__main__':
    unittest.main()