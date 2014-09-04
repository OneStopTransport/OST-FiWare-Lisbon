#!/usr/bin/env python
# encoding: utf-8
import logging

import requests
import simplejson

from utils.constants import AGENCY_QUERY
from utils.constants import API_AGENCIES
from utils.constants import API_ROUTES
from utils.constants import API_STOPS
from utils.constants import API_TRIPS
from utils.constants import API_STOPTIMES
from utils.constants import OST_API_MAIN_URL
from utils.constants import ROUTE
from utils.constants import ROUTE_QUERY
from utils.constants import TRIP
from utils.errors import APIKeyError
from utils.errors import CrawlerError
from utils.errors import OSTError


class Crawler(object):
    """ Crawler to retrieve CP data from OST APIs """
    
    def __init__(self):
        requests_log = logging.getLogger("requests")
        requests_log.setLevel(logging.WARNING)

    @staticmethod
    def validate_key(url):
        """
          Checks if URL contains a key or not.
          If not raises an exception (CrawlerError).
        """
        if '?key=' not in url:
            raise CrawlerError('URL without API Key: ' + url)
        return True

    def parse_response(self, request):
        """
          Parses the OST HTTP responses, checking
          for bad status codes and parsing the JSON.
        """
        # Checks if OST is down for maintenance
        down_for_maintenance = request.status_code == 200 and \
            'Temporarily Down' in request.content
        if request.status_code == 200 and not down_for_maintenance:
            content = simplejson.loads(request.content)
            return content.get('Objects'), content.get('Meta'),
        elif request.status_code == 401:
            # HTTP 401 - Unauthorized
            raise APIKeyError('Invalid key')
        elif request.status_code == 404:
            # HTTP 404 - bad URL (not found or without key)
            if self.validate_key(request.url):
                raise CrawlerError('API not found:\n' + request.url)
        elif request.status_code in [403, 500, 502] or down_for_maintenance:
            # Internal Server Error, Bad Gateway, Down for Maintenance
            raise OSTError('OST is down')
        return None

    def get_agency(self, agency_name):
        """
          Gets an agency's information by its name.
        """
        request = requests.get(API_AGENCIES + '&name=%s' % agency_name)
        response, meta = self.parse_response(request)
        return response[0] if response else None

    def get_data_by_agency(self, agency_id, content_type, extra_params=None):
        """
          Gets all routes belonging to an agency.
        """
        if not agency_id:
            raise CrawlerError('No Agency ID was provided')
        if not content_type:
            raise CrawlerError('No Content type was provided')
        elements = []
        are_elements_available = True
        api_url = (API_ROUTES if content_type == ROUTE else API_STOPS) \
            + (AGENCY_QUERY.format(agency_id=agency_id))
        if extra_params:
            for key, value in extra_params.iteritems():
                api_url = api_url + '&{}={}'.format(key, value)
        while are_elements_available:
            # Iterate over the API's pages
            request = requests.get(api_url)
            response, meta = self.parse_response(request)
            elements.extend(response)
            # Append ?next_page attribute to URL
            if meta.get('next_page'):
                api_url = OST_API_MAIN_URL + meta['next_page']
            else:
                # End of pages, break cycle
                are_elements_available = False
        return elements

    def get_data_from_routes(self, routes_list, content_type):
        """
          Gets all trips belonging to the given routes ids.
        """
        if not routes_list:
            raise CrawlerError('No Routes IDs were provided')
        if not content_type:
            raise CrawlerError('No Content type was provided')
        elements = []
        for route in routes_list:
            are_elements_available = True
            api_url = (API_TRIPS if content_type == TRIP else API_STOPTIMES) \
                + (ROUTE_QUERY.format(route_id=route))
            while are_elements_available:
                # Iterate over the API's pages
                request = requests.get(api_url)
                response, meta = self.parse_response(request)
                if len(response) > 0:
                    elements.extend(response)
                # Append ?next_page attribute to URL
                if meta.get('next_page'):
                    api_url = OST_API_MAIN_URL + meta['next_page']
                else:
                    # End of pages, break cycle
                    are_elements_available = False
        return elements
