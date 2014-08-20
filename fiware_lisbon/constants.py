#!/usr/bin/env python
# encoding: utf-8
import os
import socket

from utils import get_ost_api

# CKAN API Key and URL
CKAN_API_KEY = os.environ.get('FULLIT_CKAN_API_KEY')
# CKAN_API_KEY = os.environ.get('CKAN_API_KEY')
CKAN_AUTHORIZATION = {
    'content-type': 'application/x-www-form-urlencoded',
    'Authorization': CKAN_API_KEY,
}

CKAN_DATASET_NAME = 'fiware-lisbon-case'
CKAN_DATASET = {
    'name': CKAN_DATASET_NAME,
    'notes': 'Lisbon Places from OST, CitySDK and MyNeighbourhood'
}
CKAN_RESOURCE_NAME = 'FiwarePlace'
CKAN_HOST = os.environ.get('FULLIT_CKAN_HOST')
# CKAN_HOST = os.environ.get('CKAN_HOST')
CKAN_PWD = 'ckan/data/'

# MyNeighbourhood constants
JSON = 'json'
BUS = 'Bus'
TRAIN = 'Train'
PLACE_BODY = '{} {} station called {}'
TRANSPORTATION_CATEGORY = 'Transportation'

# FI-WARE Host and Status
FIWARE_HOST = os.environ.get('FIWARE_HOST')
FIWARE_GOOD_STATUS = {
    'code': '200',
    'reasonPhrase': 'OK',
}

GTFS_RESOURCES = {
    'agency',
    'calendar_dates',
    'calendar',
    'frequencies',
    'routes',
    'shapes',
    'stop_times',
    'stops',
    'trips',
}
GTFS_EXTENSION = '.txt'

# OST API URLs and API Key
OST_API_MAIN_URL = 'https://api.ost.pt/'
OST_API_KEY = os.environ.get('OST_SERVER_KEY')
OST_GTFS_PARAMS = {'publisher_name': 'ComboiosPortugal,Carris'}

# GTFS APIs
API_AGENCIES = get_ost_api(OST_API_MAIN_URL, 'agencies', OST_API_KEY)
API_ROUTES = get_ost_api(OST_API_MAIN_URL, 'routes', OST_API_KEY)
API_STOPS = get_ost_api(OST_API_MAIN_URL, 'stops', OST_API_KEY)
API_TRIPS = get_ost_api(OST_API_MAIN_URL, 'trips', OST_API_KEY)
API_STOPTIMES = get_ost_api(OST_API_MAIN_URL, 'stoptimes', OST_API_KEY)

# GTFS API Operators
AGENCY_QUERY = '&agency={agency_id}'
ROUTE_QUERY = '&route={route_id}'

# GTFS Constants
CP_NAME = 'CP - Comboios de Portugal'
CP_URL = 'http://www.cp.pt'
CARRIS_NAME = 'CARRIS'
CARRIS_URL = 'http://www.carris.pt'
AGENCY = 'Agency'
ROUTE = 'Route'
TRIP = 'Trip'
STOP = 'Stop'
STOPTIME = 'StopTime'
ID = 'id'

# RabbitMQ & Celery
if socket.gethostname().endswith('ost.pt'):
    MQ_HOST = os.environ.get('MQ_HOST_PROD')
else:
    MQ_HOST = os.environ.get('MQ_HOST_TEST')
MQ_USER = os.environ.get('MQ_USER')
MQ_PASSWORD = os.environ.get('MQ_PASSWORD')
MQ_VHOST = os.environ.get('MQ_VHOST')
