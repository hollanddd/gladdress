import unittest
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from __util__ import *

class UtilityMethodTest(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_ordinal(self):
        self.assertEqual('5th', ordinal(5))
    
    def test_cap_words(self):
        self.assertEqual('The Quick Brown Fox', cap_words('the quick brown fox'))
    
    def test_to_utf8(self):
        valid_utf8 = True
        try:
            to_utf8(u'the quick brown fox').decode('utf-8')
        except UnicodeDecodeError:
            valid_utf8 = False
        self.assertTrue(valid_utf8)
    

if __name__ == '__main__':
    unittest.main()