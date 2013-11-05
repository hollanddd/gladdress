import unittest
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from address import Address, AddressParser

class AddressTest(unittest.TestCase):
    parser = None
    
    def setUp(self):
        self.parser = AddressParser()
    
    def test_basic_full_address(self):
        addr = Address("2 N. Park Street, Madison, WI 53703", self.parser)
        self.assertTrue(addr.house_number == "2")
        self.assertTrue(addr.street_prefix == "N.")
        self.assertTrue(addr.street == "Park")
        self.assertTrue(addr.street_suffix == "St.")
        self.assertTrue(addr.city == "Madison")
        self.assertTrue(addr.state == "WI")
        self.assertTrue(addr.zipCode == "53703")
        self.assertTrue(addr.apartment == None)
        # self.assertTrue(addr.building == None)
    
    def test_multi_address(self):
        addr = Address("416/418 N. Carroll St.", self.parser)
        self.assertTrue(addr.house_number == "416")
        self.assertTrue(addr.street_prefix == "N.")
        self.assertTrue(addr.street == "Carroll")
        self.assertTrue(addr.street_suffix == "St.")
        self.assertTrue(addr.city == None)
        self.assertTrue(addr.state == None)
        self.assertTrue(addr.zipCode == None)
        self.assertTrue(addr.apartment == None)
        # self.assertTrue(addr.building == None)
    
    def test_no_suffix(self):
        addr = Address("230 Lakelawn", self.parser)
        self.assertTrue(addr.house_number == "230")
        self.assertTrue(addr.street_prefix == None)
        self.assertTrue(addr.street == "Lakelawn")
        self.assertTrue(addr.street_suffix == None)
        self.assertTrue(addr.city == None)
        self.assertTrue(addr.state == None)
        self.assertTrue(addr.zipCode == None)
        self.assertTrue(addr.apartment == None)
        # self.assertTrue(addr.building == None)
    
#     def test_building_in_front(self):
#         addr = Address("Roundhouse Apartments 626 Langdon", self.parser)
# #        print addr
#         self.assertTrue(addr.house_number == "626")
#         self.assertTrue(addr.street_prefix == None)
#         self.assertTrue(addr.street == "Langdon")
#         self.assertTrue(addr.street_suffix == None)
#         self.assertTrue(addr.city == None)
#         self.assertTrue(addr.state == None)
#         self.assertTrue(addr.zipCode == None)
#         self.assertTrue(addr.apartment == None)
#         # self.assertTrue(addr.building == "Roundhouse Apartments")
    def test_streets_named_after_states(self):
        addr = Address("504 W. Washington Ave.", self.parser)
        self.assertTrue(addr.house_number == "504")
        self.assertTrue(addr.street_prefix == "W.")
        self.assertTrue(addr.street == "Washington")
        self.assertTrue(addr.street_suffix == "Ave.")
        self.assertTrue(addr.city == None)
        self.assertTrue(addr.state == None)
        self.assertTrue(addr.zipCode == None)
        self.assertTrue(addr.apartment == None)
        # self.assertTrue(addr.building == None)
    
    def test_hash_apartment(self):
        addr = Address("407 West Doty St. #2", self.parser)
        self.assertTrue(addr.house_number == "407")
        self.assertTrue(addr.street_prefix == "W.")
        self.assertTrue(addr.street == "Doty")
        self.assertTrue(addr.street_suffix == "St.")
        self.assertTrue(addr.city == None)
        self.assertTrue(addr.state == None)
        self.assertTrue(addr.zipCode == None)
        self.assertTrue(addr.apartment == "#2")
        # self.assertTrue(addr.building == None)
    
    def test_stray_dash_apartment(self):
        addr = Address("407 West Doty St. - #2", self.parser)
        self.assertTrue(addr.house_number == "407")
        self.assertTrue(addr.street_prefix == "W.")
        self.assertTrue(addr.street == "Doty")
        self.assertTrue(addr.street_suffix == "St.")
        self.assertTrue(addr.city == None)
        self.assertTrue(addr.state == None)
        self.assertTrue(addr.zipCode == None)
        self.assertTrue(addr.apartment == "#2")
        # self.assertTrue(addr.building == None)
    
    def test_suffixless_street_with_city(self):
        addr = Address("431 West Johnson, Madison, WI", self.parser)
        self.assertTrue(addr.house_number == "431")
        self.assertTrue(addr.street_prefix == "W.")
        self.assertTrue(addr.street == "Johnson")
        self.assertTrue(addr.street_suffix == None)
        self.assertTrue(addr.city == "Madison")
        self.assertTrue(addr.state == "WI")
        self.assertTrue(addr.zipCode == None)
        self.assertTrue(addr.apartment == None)
        # self.assertTrue(addr.building == None)
    

class AddressParserTest(unittest.TestCase):
    ap = None
    
    def setUp(self):
        self.ap = AddressParser()
    
    def test_load_suffixes(self):
        self.assertTrue(self.ap.suffixes["ALLEY"] == "ALY")
    
    def test_load_cities(self):
        self.assertTrue("wisconsin rapids" in self.ap.cities)
    
    def test_load_states(self):
        self.assertTrue(self.ap.states["Wisconsin"] == "WI")
    

if __name__ == '__main__':
    unittest.main()