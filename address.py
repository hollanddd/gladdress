import re, json, pprint
from collections import OrderedDict
from address_parser import AddressParser
from __util__ import *

class InvalidAddressException(Exception): pass

# Keep lowercase, no periods
# Requires number first, then optional dash plus numbers
street_num_regex = r'^(\d+)([-/\w*]?)(\d*)$'
secondary_designators = ['apartment', 'apt', 'building', 'bldg', 'floor', 'fl', 'flr', 'suite', 'ste', 'unit', 'room', 'rm', 'department', 'dept']
secondary_designator_regex_num = r'(#?)(\d*)(\w*)'
secondary_designator_regexes = [
                                 r'#\w+ & \w+', '#\w+ rm \w+', "#\w+-\w", r'apt #{0,1}\w+', r'apartment #{0,1}\w+', r'#\w+',
                                 r'# \w+', r'rm \w+', r'unit #?\w+', r'units #?\w+', r'- #{0,1}\w+', r'no\s?\d+\w*',
                                 r'style\s\w{1,2}', r'townhouse style\s\w{1,2}', r'floor \d', r'\d*\w* floor', r'suite \d*'
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
            
        self.guess_blindly(address)
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
            if self.check_street_directional(token):  continue
            if self.check_street(token):              continue
            if self.guess_unmatched(token):           continue
            
            unmatched.append(token)
            
        self.unmatched_list = unmatched
        if len(unmatched) == 2:
            if self.check_secondary_designator_number(' '.join(reversed(unmatched))):
                self.unmatched_list = []
                return True
        else:
            for token in unmatched:
                if self.check_secondary_designator_number(token): continue
                self.unmatched = True
                
        self.post_process()
    
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
                    if self.blind_guess.has_key('city_name'):
                        if len(self.blind_guess['city_name'].split()) == 1:
                            self.city_name = to_utf8(cap_words(token))
                            return True
                        elif len(self.blind_guess['city_name'].split()) == 2:
                            # this city name is comming from a zip look up so i trust it more than the parsing logic
                            self.city_name = self.blind_guess['city_name']
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
    
    def check_street_directional(self, token):
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
    
    def guess_blindly(self, address):
        '''populates dict named blind_guess with assumptions about address placement'''
        # populate the blind_guess with a house number if we can
        addr_parts = address.split()
        primary_num_placeholder = addr_parts[0]
        try:
            # yeah that's a little ugly but gets the job done
            self.blind_guess['primary_number'] = str(int(primary_num_placeholder))
            # we might have a primary number so lets take a stab at guessing some other things
            if len(addr_parts[1]) <= 2: # we probably have a street predirection
                if addr_parts[1] in self.parser.directionals.keys():
                    self.blind_guess['street_predirection'] = self.parser.directionals[addr_parts[1]]
                    # and then a street name and suffix to follow. lets guess
                    self.blind_guess['street_name'] = addr_parts[2]
                    self.blind_guess['street_suffix'] = addr_parts[3]
                    if len(addr_parts[4]) <=2 and addr_parts[4] in self.parser.directionals.keys():
                        # we have a postdirectional ?
                        self.blind_guess['street_postdirection'] = self.parser.directionals[addr_parts[4]]
            else: 
                if addr_parts[1] not in self.parser.directionals.values(): # we probalby have a street
                    self.blind_guess['street_name'] = addr_parts[1]
                    # and if that's the case we can guess that what follows is the suffix
                    self.blind_guess['street_suffix'] = addr_parts[2]
                    if len(addr_parts[3]) <=2 and addr_parts[3] in self.parser.directionals.keys():
                        # we have a postdirectional ?
                        self.blind_guess['street_postdirection'] = self.parser.directionals[addr_parts[3]]
                    
                else: # it is the long for directional
                    self.blind_guess['street_predirection'] = addr_parts[1]
                    # and then a street name and suffix to follow. lets guess
                    self.blind_guess['street_name'] = addr_parts[2]
                    self.blind_guess['street_suffix'] = addr_parts[3]
                    if len(addr_parts[4]) <=2 and addr_parts[4] in self.parser.directionals.keys():
                        # we have a postdirectional ?
                        self.blind_guess['street_postdirection'] = self.parser.directionals[addr_parts[4]]
                    
        except ValueError:
            if re.match(street_num_regex, primary_num_placeholder):
                # we got something like 111-123 or 111/123, lets stash it
                self.blind_guess['primary_number'] = primary_num_placeholder
            else:
                # if we fall here we don't want that key to be available later
                # display to the screen for now
                print 'address zero index is:', primary_num_placeholder
                pass
        except IndexError:
            # we can't make any more guesses because we don't have anything else to guess
            pass        
    
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
        if self.delivery_line: addr += self.delivery_line + ' '
        if self.delivery_line2: 
            addr += self.delivery_line2 + '\n'
        else: 
            addr = addr.strip() + '\n'
        if self.last_line: addr += self.last_line
        return addr
    
    def usps_normalized(self):
        '''returns normalized address per upsps pub28'''
        return self._scrubbed_address().upper()
    
    def _scrubbed_address(self):
        return self.full_address().replace(',', '').replace('.', '').upper()
    
    def one_line_usps(self):
        return self.usps_normalized().replace('\n', ' ')
    
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
                    parts = secondary_designator_match.group().split()
                    self.blind_guess['delivery_line2'] = to_utf8(secondary_designator_match.group())
                    if len(parts) == 1:
                        for char in parts[0]:
                            if char == '#': self.secondary_number = to_utf8(parts[0])
                    elif len(parts) == 2:
                        for part in parts:
                            if part.lower() in secondary_designators:
                                if parts.index(part) == 0:
                                    self.secondary_number = to_utf8(parts[1])
                                    self.secondary_designator = to_utf8(parts[0])
                                elif parts.index(part) == 1:
                                    self.secondary_number = to_utf8(parts[0])
                                    self.secondary_designator = to_utf8(parts[1])
                    else:
                        self.secondary_designator = to_utf8(secondary_designator_match.group())
                    address = re.sub(regex, "", address, flags=re.IGNORECASE)
            # Now check for things like ",  ,"
        address = re.sub(r"\,\s*\,", ",", address)
        return address
    
    def post_process(self):
        '''builds analysis, metadata, and delivery lines.'''
        self.delivery_line = self._set_delivery_line()
        self.delivery_line2 = self._set_delivery_line2()
        self.last_line = self._set_last_line()
    
    def _set_delivery_line(self):
        '''determines first delivery line give primary_number and street componenets'''
        dl1 = ''
        if self.primary_number: dl1 += self.primary_number + ' '
        if self.street_predirection: dl1 += self.street_predirection + ' '
        if self.street_name: dl1 += self.street_name + ' '
        if self.street_suffix: dl1 += self.street_suffix + ' '
        if self.street_postdirection: dl1 = self.street_postdirection
        return dl1.strip()
    
    def _set_delivery_line2(self):
        '''determines delivery line 2 given secondary designators'''
        dl2 = None
        if self.secondary_number and self.secondary_designator:
            if self.blind_guess.has_key('delivery_line2'):
                blind_dl2_parts = self.blind_guess['delivery_line2'].split()
                des_index = blind_dl2_parts.index(self.secondary_designator)
                num_index = blind_dl2_parts.index(self.secondary_number)
                if des_index == 0:
                    dl2 = self.secondary_designator + ' ' + self.secondary_number
                else:
                    dl2 = self.secondary_number + ' ' + self.secondary_designator
        elif self.secondary_number and not self.secondary_designator:
            dl2 = self.secondary_number
        elif not self.secondary_number and self.secondary_designator:
            dl2 = self.secondary_designator
        return dl2
    
    def _set_last_line(self):
        '''determines last line given city state zip'''
        last_line = ''
        if self.city_name: last_line += self.city_name
        if self.state_abbreviation: last_line += ', ' + self.state_abbreviation
        if self.zip_code: last_line += ' ' + self.zip_code
        if self.plus4_code: last_line += '-' + self.plus4_code
        return last_line
    
    def components(self):
        '''dict of components'''
        components = OrderedDict()
        components['primary_number'] = self.primary_number
        components['street_predirection'] = self.street_predirection
        components['street_name'] = self.street_name
        components['street_postdirection'] = self.street_postdirection
        components['street_suffix'] = self.street_suffix
        components['secondary_number'] = self.secondary_number
        components['secondary_designator'] = self.secondary_designator
        components['city_name'] = self.city_name
        components['state_abbreviation'] = self.state_abbreviation
        components['zip_code'] = self.zip_code
        components['plus4_code'] = self.plus4_code
        return components
    
    def meta_data(self):
        '''dict of medatadata'''
        meta_data = OrderedDict()
        meta_data['blind_guess'] = self.blind_guess
        meta_data['unmatched'] = self.unmatched_list
        return meta_data
    
    def formats(self):
        '''dict of format representations'''
        formats = OrderedDict()
        formats['usps'] = self.usps_normalized()
        formats['oneline'] = self.one_line_usps()
        formats['downcase_oneline'] = self.one_line_usps().lower() 
        return formats
    
    def as_dict(self):
        '''returns dict representation of address'''
        address_dict = OrderedDict()
        address_dict['address_provided'] = self.original
        address_dict['delivery_line'] =    self.delivery_line
        address_dict['delivery_line2'] =   self.delivery_line2
        address_dict['last_line'] =        self.last_line
        address_dict['components'] =       self.components()
        address_dict['metadata'] =         self.meta_data()
        address_dict['analysis'] =         self.analysis
        address_dict['formats'] =          self.formats()
        return address_dict
    
    def as_json(self, pretty=False):
        '''provide in json format cause...'''
        if pretty:
            return json.dumps(self.as_dict(), ensure_ascii=False, indent=4)
        return json.dumps(self.as_dict(), ensure_ascii=False)
    
    def pp_json(self):
        return self.as_json(pretty=True)
    
    def __repr__(self):
        return unicode(self)
    
    def __str__(self):
        return unicode(self)
    
    def __unicode__(self):
        return self.as_json()
    

if __name__ == '__main__':
    ap = AddressParser()
    #addr = Address('407 West Doty St. #2', ap)
    addr = Address('351 King St. SW suite 500, San Francisco, CA 94158', ap)
    print addr.pp_json()