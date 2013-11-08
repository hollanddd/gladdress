import csv, os, sys
cwd = os.path.dirname(os.path.realpath(__file__))
class AddressParser(object):
    '''
    AddressParser is used to create Address objects. It contains a list of preseeded cities, states, prefixes,
    suffixes, and street names that will help the Address object parse the given string. 
    It's loaded with defaults that work in the average case, but can be adjusted for specific cases.
    '''
    zip_codes = {}
    suffixes = {}
    cities = []
    streets = []
    directionals = {
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
            for zipcode in zips:
                self.zip_codes[zipcode['zip']] = {
                                                    'city_name': zipcode['city'], 
                                                    'state': zipcode['state']
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
        Load up all cities in lowercase for easier matching. The file should have one city name per line, with no extra
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
    
