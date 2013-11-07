import re, csv, os, sys
from __util__ import *

class InvalidAddressException(Exception): pass

# Keep lowercase, no periods
# Requires number first, then optional dash plus numbers
street_num_regex = r'^(\d+)([-/\w*]?)(\d*)$'

apartment_regex_num = r'(#?)(\d*)(\w*)'
cwd = os.path.dirname(os.path.realpath(__file__))

class AddressParser(object):
    '''
    AddressParser is used to create Address objects. It contains a list of preseeded cities, states, prefixes,
    suffixes, and street names that will help the Address object parse the given string. 
    It's loaded with defaults that work in the average case, but can be adjusted for specific cases.
    '''
    zipCodes = {}
    suffixes = {}
    cities = []
    streets = []
    prefixes = {
        "n": "N.", "e": "E.", "s": "S.", "w": "W.", "ne": "NE.", "nw": "NW.", 'se': "SE.", 'sw': "SW.", 'north': "N.",
        'east': "E.", 'south': "S.",
        'west': "W.", 'northeast': "NE.", 'northwest': "NW.", 'southeast': "SE.", 'southwest': "SW."}
    
    states = {
        'Mississippi': 'MS', 'Oklahoma': 'OK', 'Delaware': 'DE', 'Minnesota': 'MN', 'Illinois': 'IL', 'Arkansas': 'AR',
        'New Mexico': 'NM', 'Indiana': 'IN', 'Maryland': 'MD', 'Louisiana': 'LA', 'Idaho': 'ID', 'Wyoming': 'WY',
        'Tennessee': 'TN', 'Arizona': 'AZ', 'Iowa': 'IA', 'Michigan': 'MI', 'Kansas': 'KS', 'Utah': 'UT',
        'Virginia': 'VA', 'Oregon': 'OR', 'Connecticut': 'CT', 'Montana': 'MT', 'California': 'CA',
        'Massachusetts': 'MA', 'West Virginia': 'WV', 'South Carolina': 'SC', 'New Hampshire': 'NH',
        'Wisconsin': 'WI', 'Vermont': 'VT', 'Georgia': 'GA', 'North Dakota': 'ND', 'Pennsylvania': 'PA',
        'Florida': 'FL', 'Alaska': 'AK', 'Kentucky': 'KY', 'Hawaii': 'HI', 'Nebraska': 'NE', 'Missouri': 'MO',
        'Ohio': 'OH', 'Alabama': 'AL', 'New York': 'NY', 'South Dakota': 'SD', 'Colorado': 'CO', 'New Jersey': 'NJ',
        'Washington': 'WA', 'North Carolina': 'NC', 'District of Columbia': 'DC', 'Texas': 'TX', 'Nevada': 'NV',
        'Maine': 'ME', 'Rhode Island': 'RI'}
    
    def __init__(self, suffixes=None, cities=None, streets=None, logger=None):
        '''
        suffixes, cities and streets provide a chance to use different lists than the provided lists.
        suffixes is probably good for most users, unless you have some suffixes not recognized by USPS.
        Cities is a very expansive list that may lead to false positives in some cases. If you only have a few cities
        you know will show up, provide your own list for better accuracy. If you are doing addresses across the US,
        the provided list is probably better.
        Streets can be used to limit the list of possible streets the address are on. It comes blank by default and
        uses positional clues instead. If you are instead just doing a couple cities, a list of all possible streets
        will decrease incorrect street names.       
        '''
        self.logger = logger
        self.load_zips(os.path.join(cwd, 'zipcode.csv'))
        if suffixes:
            self.suffixes = suffixes
        else:
            self.load_suffixes(os.path.join(cwd, 'suffixes.csv'))
        if cities:
            self.cities = cities
        else:
            self.load_cities(os.path.join(cwd, 'cities.csv'))
        if streets:
            self.streets = streets
    
    def parse_address(self, address):
        '''
        Return an Address object from the given address. Passes itself to the Address constructor to use all 
        the custom loaded cities, streets, suffixes, etc.
        '''
        return Address(address, self, self.logger)
    
    def load_zips(self, file_name):
        '''
        Builds a zip code dictionary from csv
        '''
        with open(file_name) as f:
            zips = csv.DictReader(f, delimiter=',')
            for zipCode in zips:
                self.zipCodes[zipCode['zip']] = {
                                                    'city': zipCode['city'], 
                                                    'state': zipCode['state']
                                                }
                
    
    def load_suffixes(self, file_name):
        '''
        Build the suffix dictionary. The keys will be possible long versions, and the values will be the
        accepted abbreviations. Everything should be stored using the value version, and you can search all
        by using building a set of self.suffixes.keys() and self.suffixes.values().
        '''
        with open(file_name, 'r') as f:
            for line in f:
                # make sure we have key and value
                if len(line.split(',')) != 2:
                    continue
                # strip off newlines
                self.suffixes[line.strip().split(',')[0]] = line.strip().split(',')[1]
    
    def load_cities(self, file_name):
        '''
        Load up all cities in lowercase for easier matching. The file should have one city per line, with no extra
        characters. This isn't strictly required, but will vastly increase the accuracy.
        '''
        with open(file_name, 'r') as f:
            for line in f:
                self.cities.append(line.strip().lower())
    
    def load_streets(self, file_name):
        '''
        Load up all streets in lowercase for easier matching. The file should have one street per line, with no extra
        characters. This isn't strictly required, but will vastly increase the accuracy.
        '''
        with open(file_name, 'r') as f:
            for line in f:
                self.streets.append(line.strip().lower())
    

class Address:
    '''
    Makes an attempt to break an address into components
    '''
    unmatched = False
    unmatched_list = []
    comma_separated_address = []
    last_matched = None
    house_number = None
    street_prefix = None
    street = None
    street_suffix = None
    apartment = None
    city = None
    state = None
    zipCode = None
    original = None
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
        if self.house_number is None or self.house_number <= 0:
            self.issues.append('House number could not be determined')
        if self.street is None or self.street == '':
            self.issues.append('Street could not be determined')
    
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
                if self.check_city(token): continue
            
            if self.zipCode: address = address.replace(self.zipCode, '')
            if self.state: address = address.replace(self.state.lower(), '')
            if self.city: address = address.replace(self.city.lower(), '')
        
        # populate the blind_guess with a house number if we can
        house_num_placeholder = address.split()[0]
        try:
            # yeah that's a little ugly but gets the job done
            self.blind_guess['house_number'] = str(int(house_num_placeholder))
        except ValueError:
                if re.match(street_num_regex, house_num_placeholder):
                    # we got something like 111-123 or 111/123, lets stash it
                    self.blind_guess['house_number'] = house_num_placeholder
                else:
                    # if we fall here we don't want that key to be available later
                    # display to the screen for now
                    print 'address zero index is:', house_num_placeholder
                    pass
        # Try all our address regexes. USPS says parse from the back.
        address = reversed(address.split())
        # Save unmatched to process after the rest is processed.
        unmatched = []
        # Use for contextual data
        for token in address:
            # Check zip code first
            if self.check_zip(token):           continue
            if self.check_state(token):         continue
            if self.check_city(token):          continue
            if self.check_street_suffix(token): continue
            if self.check_house_number(token):  continue
            if self.check_street_prefix(token): continue
            if self.check_street(token):        continue
            if self.guess_unmatched(token):     continue
            
            unmatched.append(token)
            
        # Post processing
        self.unmatched_list = unmatched
        if len(unmatched) == 2:
            if self.check_apartment_number(' '.join(reversed(unmatched))):
                self.unmatched_list = []
                return True
        else:
            for token in unmatched:
                if self.check_apartment_number(token): continue
                self.unmatched = True
    
    def check_zip(self, token):
        '''
        Returns true if token is matches a zip code (5 and 9 number). Zip code must be the 
        last token in an address (minus anything removed during preprocessing)
        '''
        if type(token) == int: token = str(token)
        if self.zipCode is None:
            if self.last_matched is not None:
                return False
            if re.match(r'\d{5}-?\d{4}', token):
                self.zipCode = self._cleanup(token)
                return True
            if len(token) == 5 and re.match(r'\d{5}', token):
                self.zipCode = to_utf8(token)
                if self.parser.zipCodes.has_key(self.zipCode):
                    self.blind_guess['city'] = self.parser.zipCodes[self.zipCode]['city']
                    self.blind_guess['state'] = self.parser.zipCodes[self.zipCode]['state']
                return True                
        return False
    
    def check_city(self, token):
        '''Checks for known city in city list'''
        shortened_cities = {'saint': 'st.'}
        # blind guess logic is going to fill the state more times than not. lets handle here
        if self.city is None and self.state is not None and self.street_suffix is None:
            if token.lower() in self.parser.cities:
                if len(token.split()) == 1:
                    if self.blind_guess.has_key('city') and len(self.blind_guess['city'].split()) == 1:
                        self.city = to_utf8(cap_words(token))
                        return True
                    else:
                        self.city = to_utf8(cap_words(token))
            elif self.blind_guess.has_key('city'):
                self.city = to_utf8(self.blind_guess['city'])
                return True
            return False
        # check that we are in the correct location and that we have at least one comma in the address
        if self.city is None and self.apartment is None and self.street_suffix is None and len(self.comma_separated_address) > 1:
            if token.lower() in self.parser.cities:
                self.city = to_utf8(cap_words(token))
                return True
            return False
        # Multi word cities
        if self.city is not None and self.street_suffix is None and self.street is None:
            # print "Checking for multi part city", token.lower(), token.lower() in shortened_cities.keys()
            if token.lower() + ' ' + self.city in self.parser.cities:
                self.city = to_utf8(cap_words(cap_words(token) + ' ' + self.city))
                return True
            if token.lower() in shortened_cities.keys():
                token = shortened_cities[token.lower()]
                print "Checking for shorted multi part city", token.lower() + ' ' + self.city
                if token.lower() + ' ' + self.city.lower() in self.parser.cities:
                    self.city = to_utf8(cap_words(token) + ' ' + cap_words(self.city))
                    return True
    
    def check_state(self, token):
        '''Check if state is in either the keys or values of our states list. Must come before the suffix.'''
        if len(token) == 2 and self.state is None:
            if token.capitalize() in self.parser.states.keys():
                self.state = to_utf8(self.parser.states[token.capitalize()])
                return True
            elif token.upper() in self.parser.states.values():
                self.state = to_utf8(token.upper())
                return True
        if self.state is None and self.street_suffix is None and len(self.comma_separated_address) > 1:
            if token.capitalize() in self.parser.states.keys():
                self.state = to_utf8(self.parser.states[token.capitalize()])
                return True
            elif token.upper() in self.parser.states.values():
                self.state = to_utf8(token.upper())
                return True
        # a blind guess is better than nothing
        if self.state is None and self.blind_guess.has_key('state'):
            self.state = to_utf8(self.blind_guess['state'])
            return True
        return False
    
    def check_apartment_number(self, token):
        '''
        Finds apartment, unit, #, etc, regardless of spot in string. This needs to come after everything 
        else has been ruled out, because it has a lot of false positives.
        '''
        apartment_regexes = [
                             r'#\w+ & \w+', '#\w+ rm \w+', "#\w+-\w", r'apt #{0,1}\w+', r'apartment #{0,1}\w+', r'#\w+',
                             r'# \w+', r'rm \w+', r'unit #?\w+', r'units #?\w+', r'- #{0,1}\w+', r'no\s?\d+\w*',
                             r'style\s\w{1,2}', r'\d{1,4}/\d{1,4}', r'\d{1,4}', r'\w{1,2}'
                            ]
        
        for regex in apartment_regexes:
            if re.match(regex, token.lower()):
                self.apartment = to_utf8(token)
                return True
        if self.apartment and token.lower() in ['apt', 'apartment']:
            self.apartment = to_utf8(token + ' ' + self.apartment)
            return True
        if not self.street_suffix and not self.street and not self.apartment:
            if re.match(r'\d?\w?', token.lower()):
                self.apartment = to_utf8(token)
                return True
        return False
    
    def check_street_suffix(self, token):
        '''
        Attempts to match a street suffix. If found, it will return the abbreviation, 
        with the first letter capitalized and a period after it. E.g. "St." or "Ave."
        '''
        # suffix must come before street
        if self.street_suffix is None and self.street is None:
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
        This check must come after the checks for house_number and street_prefix to help us deal with multi word streets.
        '''
        # first check for single word streets between a prefix and a suffix
        if self.street is None and self.street_suffix is not None and self.street_prefix is None and self.house_number is None:
            self.street = to_utf8(cap_words(token))
            return True
        # now check for multiple word streets. this check must come after the check for street_prefix and house_number for this reason.
        elif self.street is not None and self.street_suffix is not None and self.street_prefix is None and self.house_number is None:
            self.street = to_utf8(token.capitalize() + ' ' + self.street)
            return True
        if not self.street_suffix and not self.street and token.lower() in self.parser.streets:
            self.street = to_utf8(token)
            return True
        return False
    
    def check_street_prefix(self, token):
        '''
        Finds street prefixes, such as N. or Northwest, before a street name. 
        Standardizes to 1 or two letters, followed by a period.
        '''
        if self.street and not self.street_prefix and token.lower().replace('.', '') in self.parser.prefixes.keys():
            self.street_prefix = to_utf8(self.parser.prefixes[token.lower().replace('.', '')])
            return True
        return False
    
    def check_house_number(self, token):
        '''
        Attempts to find a house number, generally the first thing in an address. 
        We assume anything in front of a house_number is a building name.
        '''
        if self.street and self.house_number is None and re.match(street_num_regex, token.lower()):
            if self.blind_guess.has_key('house_number') and token == self.blind_guess['house_number']:
                self.house_number = to_utf8(str(token).upper())
                return True
            return True
        return False
    
    def check_building(self, token):
        '''
        Building name check. If we have leftover and everything else is set, probably building names.
        Allows for multi word building names.
        '''
        if self.street and self.house_number:
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
        if self.house_number is None and self.blind_guess.has_key('house_number'):
            if token == self.blind_guess['house_number']:
                self.house_number = to_utf8(self.blind_guess['house_number'])
                return True
        # Check if this is an apartment
        if token.lower() in ['apt', 'apartment']:
            return False
        # a stray dash mayhaps
        if token.strip() == '-':
            return True
        # probably garbage if its two chars long
        if len(token) <= 2:
            return False
        # how about a suffixless street
        if self.street_suffix is None and self.street is None and self.street_prefix is None and self.house_number is None:
            if re.match(r'[A-za-z]', token):
                self.street = to_utf8(token.capitalize())
                return True
        return False
    
    def full_address(self):
        '''print human readable address'''
        addr = ''
        if self.house_number:  addr = addr + self.house_number
        if self.street_prefix: addr = addr + " " + self.street_prefix
        if self.street:        addr = addr + " " + self.street
        if self.street_suffix: addr = addr + " " + self.street_suffix
        if self.apartment:     addr = addr + " " + self.apartment
        if self.city:          addr = addr + ", " + self.city
        if self.state:         addr = addr + ", " + self.state
        if self.zipCode:       addr = addr + " " + self.zipCode
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
        # Now let's get the apartment stuff out of the way. Using only sure match regexes, delete apartment parts from
        # the address. This prevents things like "Unit" being the street name.
        apartment_regexes = [
                             r'#\w+ & \w+', '#\w+ rm \w+', "#\w+-\w", r'apt #{0,1}\w+', r'apartment #{0,1}\w+', r'#\w+',
                             r'# \w+', r'rm \w+', r'unit #?\w+', r'units #?\w+', r'- #{0,1}\w+', r'no\s?\d+\w*',
                             r'style\s\w{1,2}', r'townhouse style\s\w{1,2}', r'\d*\w* floor', r'suite \d*'
                            ]
        
        for regex in apartment_regexes:
            apartment_match = re.search(regex, address, re.IGNORECASE)
            if apartment_match:
                carry_on = True
                for part in apartment_match.group().split():
                    if part.lower() in ['st', 'street', 'rd', 'road']:
                        carry_on = False
                        break
                if carry_on:
                    # print "Matched regex: ", regex, apartment_match.group()
                    self.apartment = to_utf8(apartment_match.group())
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
                            'house_number': self.house_number,
                            'street_prefix': self.street_prefix,
                            'street': self.street,
                            'street_suffix': self.street_suffix,
                            'apartment': self.apartment,
                            'city':self.city,
                            'state':self.state,
                            'zip':self.zipCode,
                            'unmatched': self.unmatched_list,
                            'issues': self.issues,
                            'blind_guess': self.blind_guess
                        }
        return address_dict
    
    def __unicode__(self):
        ''''''
        address_dict = self.as_dict()
        return u"Address - House number: {house_number} Prefix: {street_prefix} Street: {street} Suffix: {street_suffix}" \
               u" Apartment: {apartment} City,State,Zip: {city}, {state} {zip}".format(**address_dict)
    

if __name__ == '__main__':
    ap = AddressParser()
    addr = Address('351 King St. 2nd Floor, San Francisco, CA, 94158', ap)
    print addr.as_dict()
