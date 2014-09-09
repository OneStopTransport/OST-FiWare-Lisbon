#!/usr/bin/env python
# encoding: utf-8
import os
import socket

from .utils import get_ost_api


##########################################################################
###################     CKAN AND MYNEIGHBOURHOOD     #####################
##########################################################################

# CKAN API Key and URL
CKAN_API_KEY = os.environ.get('CKAN_API_KEY')
CKAN_AUTHORIZATION = {
    'content-type': 'application/x-www-form-urlencoded',
    'Authorization': CKAN_API_KEY,
}
CKAN_HOST = os.environ.get('CKAN_HOST')
CKAN_PWD = 'ckan/data/'

# CKAN Datasets
# MyNeighbourhood Places - OST Stops as POIs
CKAN_RESOURCE_NAME = 'OST Places'
CKAN_DATASET_NAME = 'fiware-ost-lisbon-case'
CKAN_DATASET = {
    'name': CKAN_DATASET_NAME,
    'notes': 'Lisbon Places from OST (bus and train stops)',
}
# Carris Dataset - Carris Stops as POIs
CKAN_CARRIS_DATASET_NAME = 'fiware-gtfs-carris'
CKAN_CARRIS_DATASET = {
    'name': CKAN_CARRIS_DATASET_NAME,
    'notes': 'GTFS for Carris',
}
# CP Dataset - CP Stops as POIs
CKAN_CP_DATASET_NAME = 'fiware-gtfs-cp'
CKAN_CP_DATASET = {
    'name': CKAN_CP_DATASET_NAME,
    'notes': 'GTFS for CP',
}

CKAN_DATASET_FIELDS = [
    {"id": "field_poi_id", "type": "integer"},
    {"id": "field_neighbourhood", "type": "text"},
    {"id": "field_title", "type": "text"},
    {"id": "field_category_places", "type": "text"},
    {"id": "field_body", "type": "text"},
    {"id": "field_photographs", "type": "json"},
    {"id": "field_website", "type": "text"},
    {"id": "field_email", "type": "text"},
    {"id": "field_phone", "type": "text"},
    {"id": "field_location_latitude", "type": "float"},
    {"id": "field_location_longitude", "type": "float"},
    {"id": "field_location_address_first_line", "type": "text"},
    {"id": "field_location_address_second_line", "type": "text"},
    {"id": "field_location_city", "type": "text"},
    {"id": "field_location_country", "type": "text"}
]


# MyNeighbourhood constants
JSON = 'json'
BUS = 'Bus'
TRAIN = 'Train'
PLACE_BODY = '{} {} station called {}'
TRANSPORTATION_CATEGORY = 'Transportation'

##########################################################################
########################     FIWARE AND OST     ##########################
##########################################################################

# FI-WARE Host and Status
FIWARE_HOST = os.environ.get('FIWARE_HOST')
FIWARE_GOOD_STATUS = {
    'code': '200',
    'reasonPhrase': 'OK',
}

# GTFS file names
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
OST_GTFS_PARAMS_CARRIS = {'publisher_name': 'Carris'}
OST_GTFS_PARAMS_CP = {'publisher_name': 'ComboiosPortugal'}
OST_LOGIN_URL = 'https://www.ost.pt/login'
OST_RECEPTION_API = os.environ.get('OST_RECEPTION_API')
OST_RECEPTION_COORDS = {
    CKAN_CP_DATASET_NAME: (
        os.environ.get('OST_CP_USERNAME'),
        os.environ.get('OST_CP_PASSWORD'),
    ),
    CKAN_CARRIS_DATASET_NAME: (
        os.environ.get('OST_CARRIS_USERNAME'),
        os.environ.get('OST_CARRIS_PASSWORD'),
    ),
}

DATASETS_NAMES = {
    OST_GTFS_PARAMS_CARRIS['publisher_name']: CKAN_CARRIS_DATASET_NAME,
    OST_GTFS_PARAMS_CP['publisher_name']: CKAN_CP_DATASET_NAME,
}

# GTFS APIs
API_AGENCIES = get_ost_api(OST_API_MAIN_URL, 'agencies', OST_API_KEY)
API_ROUTES = get_ost_api(OST_API_MAIN_URL, 'routes', OST_API_KEY)
API_STOPS = get_ost_api(OST_API_MAIN_URL, 'stops', OST_API_KEY)
API_TRIPS = get_ost_api(OST_API_MAIN_URL, 'trips', OST_API_KEY)
API_STOPTIMES = get_ost_api(OST_API_MAIN_URL, 'stoptimes', OST_API_KEY)

# GTFS API Operators
AGENCY_QUERY = '&agency={agency_id}'
ROUTE_QUERY = '&route={route_id}'

# GTFS Constants - CP and CARRIS
CP_NAME = 'CP - Comboios de Portugal'
CP_URL = 'http://www.cp.pt'
CP_OST_PARAMS = {'publisher_name': 'ComboiosPortugal'}
CARRIS_NAME = 'CARRIS'
CARRIS_URL = 'http://www.carris.pt'
CARRIS_OST_PARAMS = {'publisher_name': 'Carris'}

# GTFS Variables
AGENCY = 'Agency'
ROUTE = 'Route'
TRIP = 'Trip'
STOP = 'Stop'
STOPTIME = 'StopTime'
ID = 'id'

##########################################################################
######################     RABBITMQ AND CELERY     #######################
##########################################################################

if socket.gethostname().endswith('ost.pt'):
    MQ_HOST = os.environ.get('MQ_HOST_PROD')
else:
    MQ_HOST = os.environ.get('MQ_HOST_TEST')
MQ_USER = os.environ.get('MQ_USER')
MQ_PASSWORD = os.environ.get('MQ_PASSWORD')
MQ_VHOST = os.environ.get('MQ_VHOST')
