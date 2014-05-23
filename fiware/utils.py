import requests
import simplejson
from colorama   import Fore

from .constants import API_AGENCIES
from .constants import API_ROUTES
from .constants import API_STOPS
from .constants import API_TRIPS
from .constants import API_STOPTIMES
from .constants import OST_API_MAIN_URL
from .exceptions import APIKeyError
from .exceptions import CrawlerError
from .exceptions import OSTError


class Crawler(object):
    """
      Crawler to retrieve CP data from OST APIs
      and insert it into Orion's Context Broker
    """
    def validate_key(self, url):
        # Checks if URL contains a key or not
        if '?key=' not in url:
            raise CrawlerError('URL without API Key: ' + url)
            return False
        return True

    def get_error_message(self, error):
        # Generic method for pretty printing an error message when crawler fails
        message = ' Unable to fetch data, '
        if 'No API Key was provided' in error.message:
            message = message + 'please check if you have an API key on your ' + \
            'environment by executing the following command: ' + \
            Fore.GREEN + 'echo $OST_SERVER_KEY'
        elif 'URL without API Key' in error.message:
            message = message + error.message
        elif 'API not found' in error.message:
            message = message + error.message
        elif 'Invalid key' in error.message:
            message = message + ' Please check if your key is a valid Server Key on www.ost.pt'
        elif 'OST is down' in error.message:
            message = message + ' We\'re sorry but www.ost.pt seems to be down'
        elif 'No Agency ID' in error.message:
            message = message + ' There was some problem retrieving data about CP'
        return message
        
    def parse_response(self, request):
        # Check if OST is down for maintenance
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
        # Get CP Agency information
        request = requests.get(API_AGENCIES + '&name=%s' % agency_name)
        response, meta = self.parse_response(request)
        # TODO handle the response
        return response[0] if response else None
        
    def get_routes(self, agency_id):
        # Get CP Routes information
        if not agency_id:
            raise CrawlerError('No Agency ID was provided')
        are_routes_available = True
        api_url = API_ROUTES + '&agency=%s' % agency_id
        while are_routes_available:
            request = requests.get(api_url)
            response, meta = self.parse_response(request)
            # TODO handle the response
            if meta.get('next_page'):
                api_url = OST_API_MAIN_URL + meta['next_page']
            else:
                are_routes_available = False
        
        