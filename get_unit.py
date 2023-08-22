import requests
from html.parser import HTMLParser
from csv import DictWriter
import time
import os

# Define the URL template for querying unit data
master_query = 'http://www.masterunitlist.info/Tools/CustomCard/{}'

# Define a class to parse HTML and extract unit data
class UnitParser(HTMLParser):
    def __init__(self, unit_number: int):
        super().__init__()
        self.unit = {}  # Dictionary to store unit data
        self.looking_for_data = None  # Helper variable to track the current data attribute
        self.unit['UnitNumber'] = unit_number  # Store the unit number

    def handle_starttag(self, tag, attrs):
        if tag == 'input':
            attr_dict = dict(attrs)
            if 'name' in attr_dict and attr_dict['name'].startswith('Data.') and 'value' in attr_dict:
                # Store data attributes in the unit dictionary
                self.unit[attr_dict['name'][5:]] = attr_dict['value']
        elif tag == 'textarea':
            attr_dict = dict(attrs)
            if 'name' in attr_dict and attr_dict['name'].startswith('Data.'):
                # Store the name of the data attribute we are looking for
                self.looking_for_data = attr_dict['name'][5:]

    def handle_data(self, data: str):
        if self.looking_for_data:
            # Store the data for the corresponding attribute
            self.unit[self.looking_for_data] = data.strip()
            self.looking_for_data = None

# Function to fetch HTML text for a given unit number
def get_unit(unit_number: int):
    r = requests.get(master_query.format(unit_number))
    if r.status_code == 200:
        return r.text
    else:
        return None

# Function to parse unit data from HTML response
def parse_unit_response(unit_number: int, unit_response: str):
    unit_parser = UnitParser(unit_number)
    unit_parser.feed(unit_response)
    return unit_parser.unit

# Function to write unit data to a CSV file
def write_unit(units: list):
    if not os.path.exists('units.csv'):
        with open('units.csv', 'w', newline='') as f:
            writer = DictWriter(f, fieldnames=units[0].keys())
            writer.writeheader()

    with open('units.csv', 'a', newline='') as f:
        writer = DictWriter(f, fieldnames=units[0].keys())
        try:
            writer.writerows(units)
        except Exception as e:
            print('Error writing units to CSV file: {}'.format(e))
            # make a list of the UnitNumbers of the units that failed to write
            failed_units = [unit['UnitNumber'] for unit in units]
            print('Failed to write units: {}'.format(failed_units))

if __name__ == '__main__':
    begin_unit = 4624
    end_unit = 9529
    units = []

    # Loop through unit numbers and fetch data
    for unit_number in range(begin_unit, end_unit + 1):
        text = get_unit(unit_number)

        if text:
            print('Writing unit {}'.format(unit_number))
            unit_info = parse_unit_response(unit_number, text)
            
            if 'Name' not in unit_info:
                print('No name for unit {}'.format(unit_number))
                continue
            
            units.append(unit_info)

            if len(units) >= 5:
                write_unit(units)
                units = []

        time.sleep(0.1)  # Sleep to avoid overloading the server
        
    write_unit(units)  # Write remaining units to the CSV file
