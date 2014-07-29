import unittest

import requests
import simplejson

from constants import AGENCY
from constants import CP_NAME
from constants import FIWARE_HOST
from constants import OST_API_KEY
from constants import OST_API_MAIN_URL
from crawler import Crawler
from importer import FiWare
from utils import get_ost_api


class TestConstants(unittest.TestCase):
    """ TestCase for asserting we have all the needed values """

    def setUp(self):
        # Set some constant up
        self.fiware_host = FIWARE_HOST
        self.api_key = OST_API_KEY
        self.agencies_api = get_ost_api(
            api=OST_API_MAIN_URL,
            model_name='agencies',
            api_key=self.api_key
        )
        self.headers = {
            'content-type': 'application/json',
            'accept': 'application/json',
        }
        self.crawler = Crawler()
        self.fiware = FiWare()

    def test_fiware_host_not_none(self):
        # Assure the FIWARE_HOST is an environment variable
        self.assertTrue(self.fiware_host is not None)

    def test_ost_api_key_not_none(self):
        # Assure the OST_API_KEY is an environment variable
        self.assertTrue(self.api_key is not None)

    def test_ost_api_key_is_valid(self):
        # Assure the OST_API_KEY is a valid Server Key
        r = requests.get(self.agencies_api)
        self.assertEqual(r.status_code, 200)
        self.assertTrue('Objects' in r.content and 'Error' not in r.content)

    def test_fiware_version(self):
        # Assure the Context Broker is working (getting its version via API)
        r = requests.get(self.fiware_host + '/version', headers=self.headers)
        self.assertEqual(r.status_code, 200)
        content = simplejson.loads('{' + r.content + '}')
        self.assertTrue('orion' in content.keys())
        self.assertTrue('version' in content.get('orion').keys())

    def test_crawler_get_agency(self):
        # Check if crawler can retrieve the correct agency
        response = self.crawler.get_agency(CP_NAME)
        agency_labels = {'agency_name', 'agency_url', 'agency_phone',
                         'agency_timezone', 'agency_lang'}
        self.assertTrue(agency_labels <= set(response.keys()))
        self.assertTrue(response['agency_name'] == CP_NAME)

    def test_fiware_update_agency(self):
        # Check if importer works well
        agency = self.crawler.get_agency(CP_NAME)
        all_ok = self.fiware.insert_data(agency, content_type=AGENCY)
        self.assertTrue(all_ok)
        agency_data = self.fiware.get_data(content_type=AGENCY)
        agency_ids = self.fiware.get_ids(agency_data)
        self.assertTrue(str(agency['id']) in agency_ids)


if __name__ == '__main__':
    unittest.main()
