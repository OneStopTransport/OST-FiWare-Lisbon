from zipfile import ZipFile
import csv
import os

from colorama import Fore
import requests
import simplejson

from datastore.ckan_client import CkanClient
from datastore.ckan_client import CkanAccessDenied
from datastore.ckan_client import CkanNotFound
from datastore.datastore_loader import upload_resource_to_datastore
from constants import CKAN_API_KEY
from constants import CKAN_AUTHORIZATION as CKAN_AUTH
from constants import CKAN_DATASET
from constants import CKAN_HOST
from constants import CKAN_PWD
from constants import GTFS_RESOURCES
from constants import GTFS_EXTENSION
from constants import OST_API_KEY
from constants import OST_API_MAIN_URL
from constants import OST_GTFS_PARAMS
from errors import CKANError
from utils import get_ckan_api
from utils import get_ckan_error
from utils import get_file_path
from utils import get_ost_api
from utils import get_string_type


class Connector(object):
    """ Connector to fetch GTFS data from OST API and put on CKAN """

    def __init__(self):
        self.ckan = CkanClient(CKAN_HOST, CKAN_API_KEY)

    @staticmethod
    def fetch_gtfs():
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

    def create_resource(self, resource_name):
        """
          Creates the CKAN Resource (needed for the DataStore data upload)
        """
        try:
            print "> Creating resource {}".format(resource_name)
            file_path = get_file_path(resource_name, GTFS_EXTENSION)
            resource = {
                'package_id': self.get_dataset()['id'],
                'name': resource_name,
                'url': file_path,
                'format': 'csv',
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

    def push_to_ckan(self):
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
            gtfs_resources = self.get_gtfs_resources()
            for resource_name, resource_list in gtfs_resources.iteritems():
                resources_names = self.get_resources_names()
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
