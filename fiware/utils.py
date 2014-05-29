import requests
import simplejson
from colorama   import Fore

from .constants import API_AGENCIES
from .constants import API_ROUTES
from .constants import API_STOPS
from .constants import API_TRIPS
from .constants import API_STOPTIMES
from .constants import OST_API_MAIN_URL
from .constants import FIWARE_GOOD_STATUS
from .constants import get_fiware_api
from .exceptions import APIKeyError
from .exceptions import CrawlerError
from .exceptions import OSTError
from .exceptions import FiWareError


def get_error_message(error):
    """ Generic method for pretty printing an error message when crawler/updater fails """
    message_get = ' Unable to fetch data, '
    message_put = ' Unable to insert data, '
    if 'No API Key was provided' in error.message:
        message = message_get + 'please check if you have an API key on your ' + \
        'environment by executing the following command: ' + \
        Fore.GREEN + 'echo $OST_SERVER_KEY'
    elif 'URL without API Key' in error.message:
        message = message_get + error.message
    elif 'API not found' in error.message:
        message = message_get + error.message
    elif 'Invalid key' in error.message:
        message = message_get + ' Please check if your key is a valid Server Key on www.ost.pt'
    elif 'OST is down' in error.message:
        message = message_get + ' We\'re sorry but www.ost.pt seems to be down'
    elif 'No Agency ID' in error.message:
        message = message_get + ' There was some problem retrieving data about CP'
    elif 'update unsuccessful' in error.message:
        message = message_put + error.message
    return message


class Crawler(object):
    """ Crawler to retrieve CP data from OST APIs """
    def validate_key(self, url):
        """
          Checks if URL contains a key or not.
          If not raises an exception (CrawlerError).
        """
        if '?key=' not in url:
            raise CrawlerError('URL without API Key: ' + url)
            return False
        return True
        
    def parse_response(self, request):
        """
          Parses the OST HTTP responses, checking
          for bad status codes and parsing the JSON.
        """
        # Checks if OST is down for maintenance
        down_for_maintenance = request.status_code == 200 and 'Temporarily Down' in request.content
        if request.status_code == 200 and not down_for_maintenance:
            # The response is a dictionary with agency attributes as keys
            content = simplejson.loads(request.content)
            return (content.get('Objects'), content.get('Meta'))
        elif request.status_code == 401:
            # HTTP 401 - Unauthorized
            raise APIKeyError('Invalid key')
        elif request.status_code == 404:
            # HTTP 404 - bad URL (not found or without key)
            if self.validate_key(request.url):
                raise CrawlerError('API not found:\n' + request.url)
        elif request.status_code in [ 403, 500, 502 ] or down_for_maintenance:
            # OST is doen (Internal Server Error, Bad Gateway, Down for Maintenance)
            raise OSTError('OST is down')
        return None
    
    def get_agency(self, agency_name):
        """
          Gets an agency's information by its name.
        """
        request = requests.get(API_AGENCIES + '&name=%s' % agency_name)
        response, meta = self.parse_response(request)
        return response[0] if response else None
        
    def get_routes(self, agency_id):
        """
          Gets all routes belonging to an agency.
        """
        if not agency_id:
            raise CrawlerError('No Agency ID was provided')
        routes = []
        are_routes_available = True
        api_url = API_ROUTES + '&agency=%s' % agency_id
        while are_routes_available:
            # Iterate over the API's pages
            request = requests.get(api_url)
            response, meta = self.parse_response(request)
            routes.append(response)
            # Append ?next_page attribute to URL
            if meta.get('next_page'):
                api_url = OST_API_MAIN_URL + meta['next_page']
            else:
                # End of pages, break cycle
                are_routes_available = False
        return routes
    
    def get_trips(self, routes_list):
        """
          Gets all trips belonging to the given routes ids.
        """
        if not routes_list:
            raise CrawlerError('No Routes IDs were provided')
        trips = []
        for route in routes_list:
            are_trips_available = True
            api_url = API_TRIPS + '&route=%s' % route
            while are_trips_available:
                # Iterate over the API's pages
                request = requests.get(api_url)
                response, meta = self.parse_response(request)
                trips.append(response)
                # Append ?next_page attribute to URL
                if meta.get('next_page'):
                    api_url = OST_API_MAIN_URL + meta['next_page']
                else:
                    # End of pages, break cycle
                    are_trips_available = False
        return trips


class FiWare(object):
    """ Helper to insert CP data into Context Broker """
    def wrap_content(self, content, content_type):
        """
          ContextBroker requires a specific JSON schema
          when inserting data. This method wraps the
          data to be inserted with that schema.
        """
        # This is the schema to be received by the ContextBroker
        fiware_content = { 'contextElements': [], 'updateAction': 'APPEND' }
        if type(content) == type(dict()):
            # Just one element, convert to a list
            content = [ content ]
        for each in content:
            # Removes unnecessary attribute
            each.pop('resource_uri')
            element = {
                        'type': content_type,
                        'isPattern': 'false',
                        'id': str(each.pop('id')),
                        'attributes': []
                      }
            for key, value in each.iteritems():
                # If an attribute is a Foreign key...
                if type(value) == type(dict()):
                    if 'id' not in value.keys() and 'resource_uri' in value.keys():
                        # There is no id but we can replace it with resource_uri
                        value = [int(string) for string in value['resource_uri'].split('/') if string.isdigit()][0]
                        key = 'id'
                    else:
                        # ...get solely the ID
                        value = value.get('id')
                attribute = {
                    'name': key,
                    'value': value
                }
                element['attributes'].append(attribute)
            # Finally append the element to the list of items to be inserted
            fiware_content['contextElements'].append(element)
        # print simplejson.dumps(fiware_content, indent=' ' * 4) # DEBUG
        return simplejson.dumps(fiware_content)
    
    def handle_response(self, response):
        """
          Checks if the FiWare ContextBroker response
          contains errors, returning True if not and
          False if something went wrong.
        """
        fiware_error = 'FiWare returned:\n\n'
        if response.status_code != 200:
            return False, fiware_error + response.content
        content = simplejson.loads(response.content)
        if 'errorCode' in content.keys():
            return False, fiware_error + content
        if content['contextResponses'][0]['statusCode'] == FIWARE_GOOD_STATUS:
            return True, content
            
    def get_data(self, content_type, attributes=None):
        """
          Method to query data from the FiWare
          ContextBroker instance.
          - content_type = Entity type name
          - attributes = List of attributes to query
        """
        # Get the API URL and set Headers
        api_url = get_fiware_api()
        headers = { 'content-type': 'application/json', 'accept': 'application/json' }
        json_data = {
            'entities': [
                {
                    'type': content_type,
                    'isPattern': 'true',
                    'id': '.*'
                }
            ],
        }
        # If the method received a list of attributes
        if attributes and type(attributes) == type(list()):
            json_data['attributes'] = attributes
        response = requests.post(api_url, data=simplejson.dumps(json_data), headers=headers)
        all_ok, response_content = self.handle_response(response)
        return all_ok, response_content
        
    def get_ids(self, content):
        """
          Gets the list of ids of a query response
        """
        id_list = []
        if content:
            id_list = [ each.get('contextElement')['id'] for each in content.get('contextResponses') ]
        return id_list
    
    def insert_data(self, content, content_type):
        """
          Method to insert data into the FiWare
          ContextBroker instance.
        """
        # Get the API URL and set Headers
        api_url = get_fiware_api(update=True)
        headers = { 'content-type': 'application/json', 'accept': 'application/json' }
        if type(content) == type(dict()):
            # Just one element, convert to a list
            content = [ content ]    
        # Wrap the content with ContextBroker expected syntax
        for each in content:
            # Change the content to match ContextBroker expected JSON
            json_content = self.wrap_content(each, content_type)
            # Post the data
            response = requests.post(api_url, data=json_content, headers=headers)
            all_ok, response_content = self.handle_response(response)
            if not all_ok:
                message = '%s update unsuccessful.\n\n%s' % content_type, response_content
                raise FiWareError( message )
        
        
        