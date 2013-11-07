import unittest
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from __util__ import *

class UtilityMethodTest(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_ordinal(self):
        self.assertEqual('5th', ordinal(5))
    

if __name__ == '__main__':
    unittest.main()