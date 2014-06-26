import unittest

import requests
import simplejson

from constants import AGENCY
from constants import CP_NAME
from constants import FIWARE_HOST
from constants import OST_API_KEY
from constants import get_ost_api
from crawler   import Crawler
from importer  import FiWare


class TestConstants(unittest.TestCase):
    """ TestCase for asserting we have all the needed values """

    def setUp(self):
        # Set some constant up
        self.fiware_host = FIWARE_HOST
        self.api_key = OST_API_KEY
        self.agencies_api = get_ost_api('agencies', self.api_key)
        self.headers = {
                                'content-type': 'application/json',
                                'accept': 'application/json',
                            }
        self.crawler = Crawler()
        self.fiware = FiWare()

    def testFiwareHostNotNone(self):
        # Assure the FIWARE_HOST is an environment variable
        self.assertTrue(FIWARE_HOST is not None)

    def testOSTAPIKeyNotNone(self):
        # Assure the OST_API_KEY is an environment variable
        self.assertTrue(OST_API_KEY is not None)

    def testOSTAPIKeyIsValid(self):
        # Assure the OST_API_KEY is a valid Server Key
        r = requests.get(self.agencies_api)
        self.assertEqual(r.status_code, 200)
        self.assertTrue('Objects' in r.content and 'Error' not in r.content)

    def testFIWAREVersion(self):
        # Assure the Context Broker is working (getting its version via API)
        r = requests.get(self.fiware_host + '/version', headers=self.headers)
        self.assertEqual(r.status_code, 200)
        content = simplejson.loads('{' + r.content + '}')
        self.assertTrue('orion' in content.keys())
        self.assertTrue('version' in content.get('orion').keys())

    def testCrawlerGetAgency(self):
        # Check if crawler can retrieve the correct agency
        response = self.crawler.get_agency(CP_NAME)
        agency_labels = set(['agency_name', 'agency_url', 'agency_phone', \
                             'agency_timezone', 'agency_lang'])
        self.assertTrue(agency_labels <= set(response.keys()))
        self.assertTrue(response['agency_name'] == CP_NAME)

    def testFIWAREupdateAgency(self):
        # Check if importer works well
        agency = self.crawler.get_agency(CP_NAME)
        all_ok = self.fiware.insert_data(agency, content_type=AGENCY)
        self.assertTrue(all_ok)
        agency_data = self.fiware.get_data(content_type=AGENCY)
        agency_ids = self.fiware.get_ids(agency_data)
        self.assertTrue(str(agency['id']) in agency_ids)


if __name__ == '__main__':
    unittest.main()
