import csv
import json
import os
from string import capwords
from zipfile import ZipFile

import requests
import simplejson
from colorama import Fore
from datastore.ckan_client import CkanClient
from datastore.ckan_client import CkanAccessDenied
from datastore.ckan_client import CkanNotFound
from datastore.datastore_loader import upload_resource_to_datastore
from geopy.geocoders import GoogleV3
from geopy.exc import GeocoderTimedOut
from geopy.exc import GeocoderQuotaExceeded

from constants import BUS
from constants import TRAIN
from constants import JSON
from constants import PLACE_BODY
from constants import CKAN_API_KEY
from constants import CKAN_AUTHORIZATION as CKAN_AUTH
from constants import CKAN_DATASET
from constants import CKAN_CARRIS_DATASET
from constants import CKAN_CP_DATASET
from constants import CKAN_HOST
from constants import CKAN_PWD
from constants import CKAN_RESOURCE_NAME
from constants import CP_NAME
from constants import CP_URL
from constants import CARRIS_NAME
from constants import CARRIS_URL
from constants import DATASETS_NAMES
from constants import GTFS_RESOURCES
from constants import GTFS_EXTENSION
from constants import OST_API_KEY
from constants import OST_API_MAIN_URL
from constants import OST_GTFS_PARAMS_CARRIS
from constants import OST_GTFS_PARAMS_CP
from constants import STOP
from constants import TRANSPORTATION_CATEGORY
from errors import CKANError
from fiware.crawler import Crawler
from utils import get_ckan_api
from utils import get_ckan_error
from utils import get_extension
from utils import get_file_path
from utils import get_ost_api
from utils import get_string_type
from utils import grouper


class Connector(object):
    """ Connector to fetch GTFS data from OST API and put on CKAN """

    def __init__(self):
        self.ckan = CkanClient(CKAN_HOST, CKAN_API_KEY)
        self.places_list = []
        self.cp_stops = []
        self.carris_stops = []

    @staticmethod
    def fetch_full_gtfs():
        """
          Fetches the GTFS zip file from OST into the data folder,
          extracts the .txt files from the ZIP and removes the archive.
        """
        api_params = (
            OST_GTFS_PARAMS_CARRIS,
            OST_GTFS_PARAMS_CP
        )
        for parameter in api_params:
            api_url = get_ost_api(
                api=OST_API_MAIN_URL,
                model_name='gtfs',
                api_key=OST_API_KEY,
                params=parameter,
            )
            # Data folder is created if it doesn't exist
            dataset_name = DATASETS_NAMES[parameter['publisher_name']]
            data_folder = ''.join([CKAN_PWD, dataset_name, '/'])
            zip_path = os.path.join(data_folder, 'gtfs.zip')
            if not os.path.exists(data_folder):
                os.makedirs(data_folder)
            command = 'curl --silent \'{url}\' >> {data_dir}'.format(
                url=api_url, data_dir=zip_path,
            )
            # Check if curl command runs well
            return_value = os.system(command)
            if return_value > 0:
                error = {
                    '__type': ['curl'],
                    'name': ['command not found. Please see docs for details'],
                }
                raise CKANError(get_ckan_error(error, ''))
            with ZipFile(zip_path, 'r') as gtfs_zip:
                gtfs_zip.extractall(data_folder)
            if os.path.exists(zip_path):
                os.remove(zip_path)

    def fetch_gtfs_stops(self):
        """
          Fetches the GTFS Stops of the given agencies
        """
        crawler = Crawler()
        cp_id = crawler.get_agency(CP_NAME).get('id')
        carris_id = crawler.get_agency(CARRIS_NAME).get('id')
        # Get stops contained in Lisbon district
        lisbon_box = {
            'corner1': '-9.50052660716588, 38.6731469051283',
            'corner2': '-8.781861006420504, 39.31772866134264'
        }
        self.cp_stops = crawler.get_data_by_agency(cp_id, STOP, lisbon_box)
        # Get all stops from Carris (all in Lisbon)
        self.carris_stops = crawler.get_data_by_agency(carris_id, STOP)
        print "{} @ CP and {} @ CARRIS".format(
            len(self.cp_stops),
            len(self.carris_stops),
        )

    def create_dataset(self, dataset):
        """
            Creates the CKAN dataset we need
        """
        print '\n> Creating the dataset...'
        try:
            dataset = self.ckan.action('package_create', dataset)
        except CkanAccessDenied:
            message = Fore.RED + 'API Key is invalid' + Fore.RESET +\
                ', please read the docs and change it'
            print message
            return None
        return dataset

    def get_dataset(self, dataset):
        """ Returns the GTFS dataset """
        return self.ckan.action('package_show', {'id': dataset['name']})

    def create_resource(self, resource_name, dataset, resource_format=None, file_path=None):
        """
          Creates the CKAN Resource (needed for the DataStore data upload)
        """
        try:
            print "> Creating resource {}".format(resource_name)
            if file_path is None:
                extension = get_extension(resource_format)
                file_path = get_file_path(dataset['name'], resource_name, extension)
            print file_path
            resource = {
                'package_id': self.get_dataset(dataset)['id'],
                'name': resource_name,
                'url': file_path,
                'format': resource_format if resource_format else 'csv',
                'force': True,
            }
            api = get_ckan_api(
                ckan_host=CKAN_HOST,
                ckan_type='resource',
                ckan_action='create',
            )
            response = requests.post(
                api,
                data=simplejson.dumps(resource),
                headers=CKAN_AUTH,
            )
            resource = simplejson.loads(response.content)
            if response.status_code != 200 or resource.get('success') is False:
                return None
        except CkanAccessDenied:
            message = Fore.RED + 'API Key is invalid' + Fore.RESET +\
                ', please read the docs and change it'
            print message
            return None
        return resource['result']

    def get_resource(self, resource_name, dataset):
        """
          Fetches a DataStore Resource by its name
        """
        resources = self.get_dataset(dataset)['resources']
        for resource in resources:
            if resource['name'] == resource_name:
                return resource
        return None

    @staticmethod
    def get_gtfs_resources(dataset):
        """
          Parses GTFS .txt files and returns a dictionary with all of them
            * dataset_resources - dictionary where key is filename and value
              is list of dictionaries (key = attribute name, value = attribute)
        """
        dataset_resources = {}
        for filename in sorted(GTFS_RESOURCES):
            resources = []
            curr_file = ''.join([
                CKAN_PWD,
                dataset['name'],
                '/',
                filename,
                GTFS_EXTENSION]
            )
            with open(curr_file, 'r') as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    resources.append(row)
            if resources:
                dataset_resources[filename] = resources
        return dataset_resources

    def get_resources_names(self, dataset):
        """
          Returns the names of the resources created in the current
          CKAN package (dataset)
        """
        names = []
        dataset = self.get_dataset(dataset)
        if dataset.get('resources'):
            names = [resource['name'] for resource in dataset['resources']]
        return names

    @staticmethod
    def get_fields(resource_list):
        """
          Returns a list of dictionaries with every field name and type:
          [
            {
              'id': 'x',
              'type: 'float',
            },
            {
              'id': 'name',
              'type': 'string',
            }
          ]
        """
        fields = []
        for attr_name, attr_value in resource_list.iteritems():
            field_type = get_string_type(attr_value)
            fields.append({'id': attr_name, 'type': field_type})
        return fields

    @staticmethod
    def remove_files(dataset):
        """ Removes all .txt files from data directory """
        gtfs_dir = ''.join([
            CKAN_PWD,
            dataset['name']
        ])
        files = [f for f in os.listdir(gtfs_dir) if f.endswith('.txt')]
        for txt_file in files:
            os.remove(os.path.join(gtfs_dir, txt_file))

    @staticmethod
    def push_stops_to_ckan(stops_list, is_cp, resource_id):
        """ Pushes OST's GTFS Stops to CKAN Datastore in chunks of five """
        google_api_keys = os.environ.get('GOOGLE_SERVER_KEYS').split(';')
        google_api_index = 0
        geolocator = GoogleV3(api_key=google_api_keys[google_api_index])
        # Needed variables for the places' description
        agency_name = CP_NAME if is_cp else CARRIS_NAME
        transport = TRAIN if is_cp else BUS
        agency_url = CP_URL if is_cp else CARRIS_URL
        print '\n- Started importing stops from {}'.format(agency_name)
        api = get_ckan_api(
            ckan_host=CKAN_HOST,
            ckan_type='datastore',
            ckan_action='create',
        )
        for stop_group in grouper(stops_list, 5):
            stop_places = []
            for stop in stop_group:
                location = None
                is_able_to_continue = False
                if stop:
                    place = {}
                    coords = (
                        stop['point']['coordinates'][1],
                        stop['point']['coordinates'][0],
                    )
                    api_url = get_ost_api(
                        api=OST_API_MAIN_URL,
                        model_name='whereat',
                        api_key=OST_API_KEY,
                        params={
                            'coords': ','.join((str(coords[1]), str(coords[0])))
                        },
                    )
                    # Get the parish/neighbourhood from OST
                    whereat = requests.get(api_url)
                    if whereat.status_code == 200:
                        whereat = json.loads(whereat.content)
                    else:
                        whereat = {}
                    parish = whereat.get('parish', {})
                    municipality = whereat.get('municipality', {})
                    # Get the Address from coordinates with GoogleMaps API
                    while is_able_to_continue is False:
                        try:
                            location = geolocator.reverse(coords, exactly_one=True, timeout=60)
                            is_able_to_continue = True
                        except GeocoderTimedOut as e:
                            print '>>>>>>>>>>>>>>> GeocoderTimedOut\n', e
                            location = None
                            print 'Moving on...\n\n'
                        except GeocoderQuotaExceeded as e:
                            # TODO Google Geocoding usage isn't fetched by API
                            # Key but by IP address so the thing to do is when
                            # limit is reached change the Geocoding service
                            # to Nominatim or something else. To be implemented
                            # soon enough.
                            print '>>>>>>>>>>>>>>> GeocoderQuotaExceeded\n', e
                            google_api_index += 1
                            if google_api_index < len(google_api_keys):
                                geolocator = GoogleV3(api_key=google_api_keys[google_api_index])
                                print 'Trying a new key: {}...\n\n'.format(google_api_keys[google_api_index])
                            else:
                                print 'Oh noes, don\'t know what to do :(\n\n'
                                google_api_index = 0
                                geolocator = GoogleV3(api_key=google_api_keys[google_api_index])
                                break
                    place_name = capwords(stop['stop_name'])
                    body = PLACE_BODY.format(
                        agency_name, transport, place_name.encode('utf-8')
                    )
                    # Create a JSON list to be written to file
                    place['field_title'] = place_name
                    place['field_category_places'] = TRANSPORTATION_CATEGORY
                    place['body'] = body
                    place['field_photographs'] = None
                    place['field_website'] = agency_url
                    place['field_email'] = ''
                    place['field_phone'] = ''
                    place['field_location_latitude'] = coords[0]
                    place['field_location_longitude'] = coords[1]
                    if parish:
                        place['field_neighbourhood'] = parish.get('name', '')
                    else:
                        place['field_neighbourhood'] = ''
                    if location:
                        # Previously:
                        #  location.raw.get('display_name').replace(';', ' ')
                        address = location.address
                        place['field_location_address_line_1'] = address
                    else:
                        place['field_location_address_line_1'] = ''

                    place['field_location_address_line_2'] = ''
                    if municipality:
                        municipality_name = municipality.get('name', '')
                        place['field_location_city'] = municipality_name
                    else:
                        place['field_location_city'] = ''
                    place['field_location_country'] = 'Portugal'
                    place['resource_id'] = resource_id
                    stop_places.append(place)
            records = {
                'resource_id': resource_id,
                'records': stop_places,
                'force': True
            }
            response = requests.post(
                api,
                data=simplejson.dumps(records),
                headers=CKAN_AUTH,
            )
            print "\n", response.content.encode('utf-8', 'replace'), "\n"

    def push_to_ckan(self, gtfs_csv=False):
        """
          Main routine that calls the other functions:
              - Creates a dataset if it doesn't exist
              - Fetches GTFS data from OST (either whole dataset or only stops)
              - If whole dataset, creates a CKAN Resource per GTFS file
              - Else creates only one (Stops as Places)
              - Uploads data to CKAN DataStore
              - Removes locally created files
        """
        dataset = None
        if gtfs_csv:
            datasets = (CKAN_CARRIS_DATASET, CKAN_CP_DATASET)
            for each in datasets:
                try:
                    dataset = self.get_dataset(each)
                except CkanNotFound as error:
                    if 'Resource not found' in error.message:
                        dataset = self.create_dataset(each)
                if dataset is not None:
                    resources_names = self.get_resources_names(each)
                    # Routine to import the entire GTFS to CKAN
                    gtfs_resources = self.get_gtfs_resources(each)
                    for resource_name, resource_list in gtfs_resources.iteritems():
                        if resource_name not in resources_names:
                            self.create_resource(resource_name, each)
                        resource = self.get_resource(resource_name, each)
                        upload_resource_to_datastore(
                            resource=resource,
                            if_changed=False,
                            locally_cache_content=False,
                            ckan=self.ckan,
                        )
                    self.remove_files(each)
        else:
            try:
                dataset = self.get_dataset(CKAN_DATASET)
            except CkanNotFound as error:
                if 'Resource not found' in error.message:
                    dataset = self.create_dataset(CKAN_DATASET)
            if dataset is not None:
                # Routine to import GTFS Stops as Places (POIs)
                resources_names = self.get_resources_names(dataset)
                self.places_list = []
                if CKAN_RESOURCE_NAME not in resources_names:
                    self.create_resource(
                        resource_name=CKAN_RESOURCE_NAME,
                        resource_format=JSON,
                        dataset=dataset,
                        file_path='https://api.ost.pt/stops/'
                    )
                resource = self.get_resource(CKAN_RESOURCE_NAME, dataset)
                resource_id = resource.get('id')
        
                self.push_stops_to_ckan(self.cp_stops, True, resource_id)
                self.push_stops_to_ckan(self.carris_stops, False, resource_id)
