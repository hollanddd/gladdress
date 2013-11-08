import re
from address_parser import AddressParser
from __util__ import *

class InvalidAddressException(Exception): pass

# Keep lowercase, no periods
# Requires number first, then optional dash plus numbers
street_num_regex = r'^(\d+)([-/\w*]?)(\d*)$'
secondary_designator_regex_num = r'(#?)(\d*)(\w*)'
secondary_designator_regexes = [
                                 r'#\w+ & \w+', '#\w+ rm \w+', "#\w+-\w", r'apt #{0,1}\w+', r'apartment #{0,1}\w+', r'#\w+',
                                 r'# \w+', r'rm \w+', r'unit #?\w+', r'units #?\w+', r'- #{0,1}\w+', r'no\s?\d+\w*',
                                 r'style\s\w{1,2}', r'townhouse style\s\w{1,2}', r'\d*\w* floor', r'suite \d*'
                                ]

class Address:
    '''
    Makes an attempt to break an address into components
    '''
    
    # 
    delivery_line = None
    delivery_line2 = None
    last_line = None
    metadata = None
    analysis = None
    
    # components
    primary_number = None # House, PO box, or building number
    street_name = None 
    street_predirection = None
    street_postdirection = None
    street_suffix = None
    secondary_number = None # secondary_designator of suite number, if any
    secondary_designator = None # Location within a complex/building (ste, apt, etc.)
    extra_secondary_designator = None
    pmb_designator = None # Private Maild box
    pmb_number = None 
    city_name = None # Accepted or proper name
    state_abbreviation = None
    zip_code = None # 5 digit zip code
    plus4_code = None # the 4 digit add on code
    
    # place holders for parsing
    original = None
    unmatched = False
    unmatched_list = []
    comma_separated_address = []
    last_matched = None
    issues = []
    
    def __init__(self, address, parser=None, logger=None):
        ''''''
        self.original = to_utf8(address)
        self.parser = parser
        self.logger = logger
        self.blind_guess = {}
        
        if address is None: return 
        
        self.parse_address(self.preprocess_address(address))
        
        # It is prefectly valid for an address to not have a house number
        if self.primary_number is None or self.primary_number <= 0:
            self.issues.append('Primary number could not be determined')
            
        if self.street_name is None or self.street_name == '':
            self.issues.append('Street name could not be determined')
    
    def parse_address(self, address):
        ''''''
        # Get rid of periods and commas, split by spaces, reverse.
        # Periods should not exist, remove them. Commas separate tokens. 
        # It's possible we can use commas for better guessing.
        address = address.strip().replace('.', '')
        
        sep_list = []
        for item in address.split(','):
            sep_list.append(item.strip())
        self.comma_separated_address = sep_list
        
        address = address.lower().replace(',', '')
        # lets start off by using the comma separated address
        if len(self.comma_separated_address) > 1:
            for token in reversed(self.comma_separated_address):
                if self.check_zip(token): continue
                if self.check_state(token): continue
                if self.check_city_name(token): continue
            
            if self.zip_code: address = address.replace(self.zip_code, '')
            if self.state_abbreviation: address = address.replace(self.state_abbreviation.lower(), '')
            if self.city_name: address = address.replace(self.city_name.lower(), '')
        
        # populate the blind_guess with a house number if we can
        primary_num_placeholder = address.split()[0]
        try:
            # yeah that's a little ugly but gets the job done
            self.blind_guess['primary_number'] = str(int(primary_num_placeholder))
        except ValueError:
                if re.match(street_num_regex, primary_num_placeholder):
                    # we got something like 111-123 or 111/123, lets stash it
                    self.blind_guess['primary_number'] = primary_num_placeholder
                else:
                    # if we fall here we don't want that key to be available later
                    # display to the screen for now
                    print 'address zero index is:', primary_num_placeholder
                    pass
        # Try all our address regexes. USPS says parse from the back.
        address = reversed(address.split())
        # Save unmatched to process after the rest is processed.
        unmatched = []
        # Use for contextual data
        for token in address:
            # Check zip code first
            if self.check_zip(token):                 continue
            if self.check_state(token):               continue
            if self.check_city_name(token):           continue
            if self.check_street_suffix(token):       continue
            if self.check_primary_number(token):      continue
            if self.check_street_predirection(token): continue
            if self.check_street(token):              continue
            if self.guess_unmatched(token):           continue
            
            unmatched.append(token)
            
        # Post processing
        self.unmatched_list = unmatched
        if len(unmatched) == 2:
            if self.check_secondary_designator_number(' '.join(reversed(unmatched))):
                self.unmatched_list = []
                return True
        else:
            for token in unmatched:
                if self.check_secondary_designator_number(token): continue
                self.unmatched = True
    
    def check_zip(self, token):
        '''
        Returns true if token is matches a zip code (5 and 9 number). Zip code must be the 
        last token in an address (minus anything removed during preprocessing)
        '''
        if type(token) == int: token = str(token)
        if self.zip_code is None:
            if self.last_matched is not None:
                return False
            if re.match(r'\d{5}-?\d{4}', token):
                self.zip_code = self.to_utf8(token.split('-')[0])
                self.plus4_code = self.to_utf8(token.split('-')[-1])
                return True
            if len(token) == 5 and re.match(r'\d{5}', token):
                self.zip_code = to_utf8(token)
                if self.parser.zip_codes.has_key(self.zip_code):
                    self.blind_guess['city_name'] = self.parser.zip_codes[self.zip_code]['city_name']
                    self.blind_guess['state'] = self.parser.zip_codes[self.zip_code]['state']
                return True                
        return False
    
    def check_city_name(self, token):
        '''Checks for known city name in list of cities provided to parser'''
        shortened_cities = {'saint': 'st.'}
        # blind guess logic is going to fill the state more times than not. lets handle here
        if self.city_name is None and self.state_abbreviation is not None and self.street_suffix is None:
            if token.lower() in self.parser.cities:
                if len(token.split()) == 1:
                    if self.blind_guess.has_key('city_name') and len(self.blind_guess['city_name'].split()) == 1:
                        self.city_name = to_utf8(cap_words(token))
                        return True
                    else:
                        self.city_name = to_utf8(cap_words(token))
            elif self.blind_guess.has_key('city_name'):
                self.city_name = to_utf8(self.blind_guess['city_name'])
                return True
            return False
        # check that we are in the correct location and that we have at least one comma in the address
        if self.city_name is None and self.secondary_designator is None and self.street_suffix is None and len(self.comma_separated_address) > 1:
            if token.lower() in self.parser.cities:
                self.city_name = to_utf8(cap_words(token))
                return True
            return False
        # Multi word cities
        if self.city_name is not None and self.street_suffix is None and self.street_name is None:
            if token.lower() + ' ' + self.city_name in self.parser.cities:
                self.city_name = to_utf8(cap_words(cap_words(token) + ' ' + self.city_name))
                return True
            if token.lower() in shortened_cities.keys():
                token = shortened_cities[token.lower()]
                print "Checking for shorted multi part city_name", token.lower() + ' ' + self.city_name
                if token.lower() + ' ' + self.city_name.lower() in self.parser.cities:
                    self.city_name = to_utf8(cap_words(token) + ' ' + cap_words(self.city_name))
                    return True
    
    def check_state(self, token):
        '''Check if state is in either the keys or values of our states list. Must come before the suffix.'''
        if len(token) == 2 and self.state_abbreviation is None:
            if token.capitalize() in self.parser.states.keys():
                self.state_abbreviation = to_utf8(self.parser.states[token.capitalize()])
                return True
            elif token.upper() in self.parser.states.values():
                self.state_abbreviation = to_utf8(token.upper())
                return True
        if self.state_abbreviation is None and self.street_suffix is None and len(self.comma_separated_address) > 1:
            if token.capitalize() in self.parser.states.keys():
                self.state_abbreviation = to_utf8(self.parser.states[token.capitalize()])
                return True
            elif token.upper() in self.parser.states.values():
                self.state_abbreviation = to_utf8(token.upper())
                return True
        # a blind guess is better than nothing
        if self.state_abbreviation is None and self.blind_guess.has_key('state'):
            self.state_abbreviation = to_utf8(self.blind_guess['state'])
            return True
        return False
    
    def check_secondary_designator_number(self, token):
        '''
        Finds secondary_designator, unit, #, etc, regardless of spot in string. This needs to come after everything 
        else has been ruled out, because it has a lot of false positives.
        '''
        for regex in secondary_designator_regexes:
            if re.match(regex, token.lower()):
                self.secondary_designator = to_utf8(token)
                return True
        if self.secondary_designator and token.lower() in ['apt', 'apartment']:
            self.secondary_designator = to_utf8(token + ' ' + self.secondary_designator)
            return True
        if not self.street_suffix and not self.street_name and not self.secondary_designator:
            if re.match(r'\d?\w?', token.lower()):
                self.secondary_designator = to_utf8(token)
                return True
        return False
    
    def check_street_suffix(self, token):
        '''
        Attempts to match a street suffix. If found, it will return the abbreviation, 
        with the first letter capitalized and a period after it. E.g. "St." or "Ave."
        '''
        # suffix must come before street
        if self.street_suffix is None and self.street_name is None:
            if token.upper() in self.parser.suffixes.keys():
                suffix = self.parser.suffixes[token.upper()]
                self.street_suffix = to_utf8(suffix.capitalize() + '.')
                return True
            elif token.upper() in self.parser.suffixes.values():
                self.street_suffix = to_utf8(token.capitalize() + '.')
                return True
        return False              
    
    def check_street(self, token):
        '''
        Let's assume a street comes before a prefix and after a suffix. This isn't always the case, but we'll deal
        with that in our guessing game. Also, two word street names...well...
        This check must come after the checks for primary_number and street_predirection to help us deal with multi word streets.
        '''
        # first check for single word streets between a prefix and a suffix
        if self.street_name is None and self.street_suffix is not None and self.street_predirection is None and self.primary_number is None:
            self.street_name = to_utf8(cap_words(token))
            return True
        # now check for multiple word streets. this check must come after the check for street_predirection and primary_number for this reason.
        elif self.street_name is not None and self.street_suffix is not None and self.street_predirection is None and self.primary_number is None:
            self.street_name = to_utf8(token.capitalize() + ' ' + self.street)
            return True
        if not self.street_suffix and not self.street_name and token.lower() in self.parser.streets:
            self.street_name = to_utf8(token)
            return True
        return False
    
    def check_street_predirection(self, token):
        '''
        Finds street directionals, such as N. or Northwest, before a street name. 
        Standardizes to 1 or two letters, followed by a period.
        '''
        if self.street_name and not self.street_predirection and token.lower().replace('.', '') in self.parser.directionals.keys():
            self.street_predirection = to_utf8(self.parser.directionals[token.lower().replace('.', '')])
            return True
        return False
    
    def check_primary_number(self, token):
        '''
        Attempts to find a house number, generally the first thing in an address. 
        We assume anything in front of a primary_number is a building name.
        '''
        if self.street_name and self.primary_number is None and re.match(street_num_regex, token.lower()):
            if self.blind_guess.has_key('primary_number') and token == self.blind_guess['primary_number']:
                self.primary_number = to_utf8(str(token).upper())
                return True
            return True
        return False
    
    def check_building(self, token):
        '''
        Building name check. If we have leftover and everything else is set, probably building names.
        Allows for multi word building names.
        '''
        if self.street_name and self.primary_number:
            if not self.building:
                self.building = to_utf8(token)
            else:
                self.building = to_utf8(token + ' ' + self.building)
            return True
        return False
    
    def guess_unmatched(self, token):
        '''
        When we find something that doesn't match, we can make an educated guess and log it as such.
        '''
        # is it a house number
        if self.primary_number is None and self.blind_guess.has_key('primary_number'):
            if token == self.blind_guess['primary_number']:
                self.primary_number = to_utf8(self.blind_guess['primary_number'])
                return True
        # Check if this is an secondary_designator
        if token.lower() in ['apt', 'apartment']:
            return False
        # a stray dash mayhaps
        if token.strip() == '-':
            return True
        # probably garbage if its two chars long
        if len(token) <= 2:
            return False
        # how about a suffixless street
        if self.street_suffix is None and self.street_name is None and self.street_predirection is None and self.primary_number is None:
            if re.match(r'[A-za-z]', token):
                self.street_name = to_utf8(token.capitalize())
                return True
        return False
    
    def full_address(self):
        '''print human readable address'''
        addr = ''
        if self.primary_number:       addr = addr + self.primary_number
        if self.street_predirection:  addr = addr + " " + self.street_predirection
        if self.street_name:          addr = addr + " " + self.street_name
        if self.street_suffix:        addr = addr + " " + self.street_suffix
        if self.secondary_designator: addr = addr + " " + self.secondary_designator
        if self.city_name:            addr = addr + ", " + self.city_name
        if self.state_abbreviation:   addr = addr + ", " + self.state_abbreviation
        if self.zip_code:             addr = addr + " " + self.zip_code
        if self.plus4_code:           addr = addr + "-" + self.plus4_code
        return addr
    
    def preprocess_address(self, address):
        '''
        Takes a basic address and attempts to clean it up
        '''
        address = address.replace('# ', '#')
        address = address.replace(' & ', '&')
        # Clear the address of things like 'X units', which shouldn't be in an address anyway. We won't save this for now.
        if re.search(r"-?-?\w+ units", address, re.IGNORECASE):
            address = re.sub(r"-?-?\w+ units", "", address, flags=re.IGNORECASE)        
        # Now let's get the secondary_designator stuff out of the way. Using only sure match regexes, delete secondary_designator parts from
        # the address. This prevents things like "Unit" being the street name.
        for regex in secondary_designator_regexes:
            secondary_designator_match = re.search(regex, address, re.IGNORECASE)
            if secondary_designator_match:
                carry_on = True
                for part in secondary_designator_match.group().split():
                    if part.lower() in ['st', 'street', 'rd', 'road']:
                        carry_on = False
                        break
                if carry_on:
                    # print "Matched regex: ", regex, secondary_designator_match.group()
                    self.secondary_designator = to_utf8(secondary_designator_match.group())
                    address = re.sub(regex, "", address, flags=re.IGNORECASE)
            # Now check for things like ",  ,"
        address = re.sub(r"\,\s*\,", ",", address)
        return address
    
    def __repr__(self):
        return unicode(self)
    
    def __str__(self):
        return unicode(self)
    
    def as_dict(self):
        '''returns dict representation of address'''
        address_dict = {
                            'input_given': self.original,
                            'comma_delimited': self.comma_separated_address,
                            'primary_number': self.primary_number,
                            'street_predirection': self.street_predirection,
                            'street_name': self.street_name,
                            'street_suffix': self.street_suffix,
                            'secondary_designator': self.secondary_designator,
                            'city_name': self.city_name,
                            'state_abbreviation': self.state_abbreviation,
                            'zip_code': self.zip_code,
                            'plus4_code': self.plus4_code,
                            'unmatched': self.unmatched_list,
                            'issues': self.issues,
                            'blind_guess': self.blind_guess
                        }
        return address_dict
    
    def __unicode__(self):
        ''''''
        address_dict = self.as_dict()
        return u"Address - Primary number: {primary_number} Predirection: {street_predirection} Street: {street_name} Suffix: {street_suffix}" \
               u" Secondarydesignator: {secondary_designator} City: {city_name}, State: {state}, Zip: {zip}".format(**address_dict)
    

if __name__ == '__main__':
    ap = AddressParser()
    addr = Address('351 King St. 2nd Floor, San Francisco, CA, 94158', ap)
    print addr.as_dict()
