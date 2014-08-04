from string import capwords
from zipfile import ZipFile
import csv
import json
import os
import sys
import time

from colorama import Fore
from geopy.geocoders import Nominatim
import requests
import simplejson

from datastore.ckan_client import CkanClient
from datastore.ckan_client import CkanAccessDenied
from datastore.ckan_client import CkanNotFound
from datastore.datastore_loader import upload_resource_to_datastore
from constants import BUS
from constants import TRAIN
from constants import JSON
from constants import PLACE_BODY
from constants import CKAN_API_KEY
from constants import CKAN_AUTHORIZATION as CKAN_AUTH
from constants import CKAN_DATASET
from constants import CKAN_HOST
from constants import CKAN_PWD
from constants import CKAN_RESOURCE_NAME
from constants import CP_NAME
from constants import CP_URL
from constants import CARRIS_NAME
from constants import CARRIS_URL
from constants import GTFS_RESOURCES
from constants import GTFS_EXTENSION
from constants import OST_API_KEY
from constants import OST_API_MAIN_URL
from constants import OST_GTFS_PARAMS
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
        reload(sys)
        sys.setdefaultencoding('utf-8')

    @staticmethod
    def fetch_full_gtfs():
        """
          Fetches the GTFS zip file from OST into the data folder,
          extracts the .txt files from the ZIP and removes the archive.
        """
        api_url = get_ost_api(
            api=OST_API_MAIN_URL,
            model_name='gtfs',
            api_key=OST_API_KEY,
            params=OST_GTFS_PARAMS,
        )
        # Data folder is created if it doesn't exist
        zip_path = os.path.join(CKAN_PWD, 'gtfs.zip')
        if not os.path.exists(CKAN_PWD):
            os.makedirs(CKAN_PWD)
        command = 'curl --silent \'{url}\' >> {data_dir}'.format(
            url=api_url, data_dir=zip_path,
        )
        # Check if curl command runs well
        return_value = os.system(command)
        if return_value > 0:
            error = {
                '__type': ['curl'],
                'name': ['command not found. Please see README for details.'],
            }
            raise CKANError(get_ckan_error(error, ''))
        with ZipFile(zip_path, 'r') as gtfs_zip:
            gtfs_zip.extractall(CKAN_PWD)
        if os.path.exists(zip_path):
            os.remove(zip_path)

    def fetch_gtfs_stops(self):
        """
          Fetches the GTFS Stops of the given agencies
        """
        crawler = Crawler()
        cp_id = crawler.get_agency(CP_NAME).get('id')
        carris_id = crawler.get_agency(CARRIS_NAME).get('id')
        self.cp_stops = crawler.get_data_by_agency(cp_id, STOP)
        # self.carris_stops = crawler.get_data_by_agency(carris_id, STOP)
        print "{} @ CP and {} @ CARRIS".format(
            len(self.cp_stops),
            0 # len(self.carris_stops),
        )

    def create_dataset(self):
        """ Creates the CKAN dataset we need """
        print '\n> Creating the dataset...'
        try:
            dataset = self.ckan.action('package_create', CKAN_DATASET)
        except CkanAccessDenied:
            message = Fore.RED + 'API Key is invalid' + Fore.RESET +\
                ', please read the docs and change it'
            print message
            return None
        return dataset

    def get_dataset(self):
        """ Returns the GTFS dataset """
        return self.ckan.action('package_show', {'id': CKAN_DATASET['name']})

    def create_resource(self, resource_name, resource_format=None):
        """
          Creates the CKAN Resource (needed for the DataStore data upload)
        """
        try:
            print "> Creating resource {}".format(resource_name)
            extension = get_extension(resource_format)
            file_path = get_file_path(resource_name, extension)
            resource = {
                'package_id': self.get_dataset()['id'],
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

    def get_resource(self, resource_name):
        """
          Fetches a DataStore Resource by its name
        """
        resources = self.get_dataset()['resources']
        for resource in resources:
            if resource['name'] == resource_name:
                return resource
        return None

    @staticmethod
    def get_gtfs_resources():
        """
          Parses GTFS .txt files and returns a dictionary with all of them
            * dataset_resources - dictionary where key is filename and value
              is list of dictionaries (key = attribute name, value = attribute)
        """
        dataset_resources = {}
        for filename in sorted(GTFS_RESOURCES):
            resources = []
            current_file = ''.join([CKAN_PWD, filename, GTFS_EXTENSION])
            with open(current_file, 'r') as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    resources.append(row)
            if resources:
                dataset_resources[filename] = resources
        return dataset_resources

    def get_resources_names(self):
        """
          Returns the names of the resources created in the current
          CKAN package (dataset)
        """
        names = []
        dataset = self.get_dataset()
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
    def remove_files():
        """ Removes all .txt files from data directory """
        files = [f for f in os.listdir(CKAN_PWD) if f.endswith('.txt')]
        for txt_file in files:
            os.remove(os.path.join(CKAN_PWD, txt_file))

    def push_stops_to_ckan(self, stops_list, is_cp, resource_id):
        """ Writes all the stops to a file to be pushed to DataStore """
        geolocator = Nominatim()
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
                    whereat = json.loads(whereat.content) if whereat.status_code == 200 else {}
                    parish = whereat.get('parish', {})
                    # Get the Address from coordinates with Nominatim
                    location = geolocator.reverse(coords, timeout=2)
                    address = location.raw['address']
                    place_name = capwords(stop['stop_name'])            
                    body = PLACE_BODY.format(agency_name, transport, place_name)
                    # Create a JSON list to be written to file
                    place['field_neighbourhood'] = parish.get('name', '') if parish else ''
                    place['field_title'] = place_name
                    place['field_category_places'] = TRANSPORTATION_CATEGORY
                    place['body'] = body
                    place['field_photographs'] = None
                    place['field_website'] = agency_url
                    place['field_email'] = ''
                    place['field_phone'] = ''
                    place['field_location_latitude'] = coords[0]
                    place['field_location_longitude'] = coords[1]
                    place['field_location_address_line_1'] = location.raw.get('display_name').replace(';', ' ')
                    place['field_location_address_line_2'] = ''
                    place['field_location_city'] = address['city'] if address.get('city') else address.get('town', '')
                    place['field_location_country'] = address.get('country', 'Portugal')
                    place['resource_id'] = resource_id
                    stop_places.append(place)
                    # one second sleep because of Nominatim usage limits
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
            print "\n", response.content, "\n"

    def push_to_ckan(self, gtfs_csv=False):
        """
          Main routine that calls the other functions:
              - Creates a dataset if it doesn't exist
              - Fetches GTFS data from OST
              - Creates a CKAN Resource per GTFS file
              - Uploads its data to CKAN DataStore
              - Removes the .txt files
        """
        dataset = None
        try:
            dataset = self.get_dataset()
        except CkanNotFound as error:
            if 'Resource not found' in error.message:
                dataset = self.create_dataset()
        if dataset is not None:
            resources_names = self.get_resources_names()
            if gtfs_csv:
                gtfs_resources = self.get_gtfs_resources()
                for resource_name, resource_list in gtfs_resources.iteritems():
                    if resource_name not in resources_names:
                        # fields = self.get_fields(resource_list[0])
                        self.create_resource(resource_name)
                    resource = self.get_resource(resource_name)
                    upload_resource_to_datastore(
                        resource=resource,
                        if_changed=False,
                        locally_cache_content=False,
                        ckan=self.ckan,
                    )
                # self.remove_files()
            else:
                self.places_list = []
                if CKAN_RESOURCE_NAME not in resources_names:
                    self.create_resource(
                        resource_name=CKAN_RESOURCE_NAME,
                        resource_format=JSON,
                    )
                resource = self.get_resource(CKAN_RESOURCE_NAME)
                resource_id = resource.get('id')
                # A local file is needed to update the CKAN datastore
                extension = get_extension(JSON)
                file_path = ''.join([CKAN_PWD, CKAN_RESOURCE_NAME, extension])
                if not os.path.exists(file_path):
                    with open(file_path, 'a'):
                        os.utime(file_path, None)
                self.push_stops_to_ckan(self.cp_stops, True, resource_id)
                #self.push_stops_to_ckan(self.carris_stops, True, resource_id)

