import unittest
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from address_parser import AddressParser
from address import Address

class AddressTest(unittest.TestCase):
    parser = None
    
    def setUp(self):
        self.parser = AddressParser()
    
    def test_zip_integer(self):
	      addr = Address(None, self.parser)
	      addr.check_zip(12345)
	      self.assertEqual('12345', addr.zip_code)
	  
    def test_check_zip(self):
	      addr = Address(None, self.parser)
	      addr.check_zip('12345')
	      self.assertEqual('12345', addr.zip_code)
	  
    def test_cryptic_beverly_hills(self):
	      addr = Address('205 1105 14 90210', self.parser)
	      self.assertEqual('90210', addr.zip_code)
	      self.assertEqual('CA', addr.state_abbreviation)
	      self.assertEqual('Beverly Hills', addr.city_name)
	      self.assertEqual('205', addr.primary_number)
	  
    def test_no_comma_address(self):
        addr = Address('2 N. Park Street Madison WI 53703', self.parser)
        self.assertEqual('2', addr.primary_number)
        self.assertEqual('N.', addr.street_predirection)
        self.assertEqual('Park', addr.street_name)
        self.assertEqual('St.', addr.street_suffix)
        self.assertEqual('Madison', addr.city_name)
        self.assertEqual('WI', addr.state_abbreviation)
        self.assertEqual('53703', addr.zip_code)
        self.assertEqual(None, addr.secondary_designator)
    
    def test_basic_full_address(self):
        addr = Address('2 N. Park Street, Madison, WI 53703', self.parser)
        self.assertEqual('2', addr.primary_number)
        self.assertEqual('N.', addr.street_predirection)
        self.assertEqual('Park', addr.street_name)
        self.assertEqual('St.', addr.street_suffix)
        self.assertEqual('Madison', addr.city_name)
        self.assertEqual('WI', addr.state_abbreviation)
        self.assertEqual('53703', addr.zip_code)
        self.assertEqual(None, addr.secondary_designator)
    
    def test_multi_address(self):
        addr = Address('416/418 N. Carroll St.', self.parser)
        self.assertEqual('416/418', addr.primary_number)
        self.assertEqual('N.', addr.street_predirection)
        self.assertEqual('Carroll', addr.street_name)
        self.assertEqual('St.', addr.street_suffix)
        self.assertEqual(None, addr.city_name)
        self.assertEqual(None, addr.state_abbreviation)
        self.assertEqual(None, addr.zip_code)
        self.assertEqual(None, addr.secondary_designator)
    
    def test_no_suffix(self):
        addr = Address('230 Lakelawn', self.parser)
        self.assertEqual('230', addr.primary_number)
        self.assertEqual(None, addr.street_predirection)
        self.assertEqual('Lakelawn', addr.street_name)
        self.assertEqual(None, addr.street_suffix)
        self.assertEqual(None, addr.city_name)
        self.assertEqual(None, addr.state_abbreviation)
        self.assertEqual(None, addr.zip_code)
        self.assertEqual(None, addr.secondary_designator)
    
    def test_streets_named_after_state_abbreviations(self):
        addr = Address('504 W. Washington Ave.', self.parser)
        self.assertEqual('504', addr.primary_number)
        self.assertEqual('W.', addr.street_predirection)
        self.assertEqual('Washington', addr.street_name)
        self.assertEqual('Ave.', addr.street_suffix)
        self.assertEqual(None, addr.city_name)
        self.assertEqual(None, addr.state_abbreviation)
        self.assertEqual(None, addr.zip_code)
        self.assertEqual(None, addr.secondary_designator)
    
    def test_hash_secondary_designator(self):
        addr = Address('407 West Doty St. #2', self.parser)
        self.assertEqual('407', addr.primary_number)
        self.assertEqual('W.', addr.street_predirection)
        self.assertEqual('Doty', addr.street_name)
        self.assertEqual('St.', addr.street_suffix)
        self.assertEqual(None, addr.city_name)
        self.assertEqual(None, addr.state_abbreviation)
        self.assertEqual(None, addr.zip_code)
        self.assertEqual('#2', addr.secondary_designator)
    
    def test_stray_dash_secondary_designator(self):
        addr = Address('407 West Doty St. - #2', self.parser)
        self.assertEqual('407', addr.primary_number)
        self.assertEqual('W.', addr.street_predirection)
        self.assertEqual('Doty', addr.street_name)
        self.assertEqual('St.', addr.street_suffix)
        self.assertEqual(None, addr.city_name)
        self.assertEqual(None, addr.state_abbreviation)
        self.assertEqual(None, addr.zip_code)
        self.assertEqual('#2', addr.secondary_designator)
    
    def test_unit_prefix(self):
        addr = Address('407 west doty st unit 2', self.parser)
        self.assertEqual('407', addr.primary_number)
        self.assertEqual('W.', addr.street_predirection)
        self.assertEqual('Doty', addr.street_name)
        self.assertEqual('St.', addr.street_suffix)
        self.assertEqual(None, addr.city_name)
        self.assertEqual(None, addr.state_abbreviation)
        self.assertEqual(None, addr.zip_code)
        self.assertEqual('unit 2', addr.secondary_designator)
    
    def test_unit_street_rhode_island(self):
        addr = Address('111-123 Unit St providence RI 02909', self.parser)
        self.assertEqual('Unit', addr.street_name)
        self.assertEqual('St.', addr.street_suffix)
        self.assertEqual('Providence', addr.city_name)
        self.assertEqual('111-123', addr.primary_number)
    
    def test_apt_prefix(self):
        addr = Address('407 west doty st apt 2', self.parser)
        self.assertEqual('407', addr.primary_number)
        self.assertEqual('W.', addr.street_predirection)
        self.assertEqual('Doty', addr.street_name)
        self.assertEqual('St.', addr.street_suffix)
        self.assertEqual(None, addr.city_name)
        self.assertEqual(None, addr.state_abbreviation)
        self.assertEqual(None, addr.zip_code)
        self.assertEqual('apt 2', addr.secondary_designator)
    
    def test_suffixless_street_with_city_name(self):
        addr = Address('431 West Johnson, Madison, WI', self.parser)
        self.assertEqual('431', addr.primary_number)
        self.assertEqual('W.', addr.street_predirection)
        self.assertEqual('Johnson', addr.street_name)
        self.assertEqual(None, addr.street_suffix)
        self.assertEqual('Madison', addr.city_name)
        self.assertEqual('WI', addr.state_abbreviation)
        self.assertEqual(None, addr.zip_code)
        self.assertEqual(None, addr.secondary_designator)
    
    def test_simple_address_issue_(self):
	      addr = Address('351 King St. #400, San Francisco, CA, 94158', self.parser)
	      self.assertEqual('351', addr.primary_number)
	      self.assertEqual('San Francisco', addr.city_name)
	      self.assertEqual('#400', addr.secondary_designator)
	  
    def test_complex_house_num(self):
	      addr = Address('18N608 some st madison, wi', self.parser)
	      self.assertEqual('18N608', addr.primary_number)
	  
    def test_second_delivery_line_has_floor(self):
	      addr = Address('351 King St. 2nd Floor, San Francisco, CA, 94158', self.parser)
	      self.assertEqual('2nd Floor', addr.secondary_designator)
	  
    def test_second_deliver_line_has_suite(self):
	      addr = Address('351 King St. suite 500, San Francisco, CA, 94158', self.parser)
	      self.assertEqual('suite 500', addr.secondary_designator)
	  

if __name__ == '__main__':
    unittest.main()