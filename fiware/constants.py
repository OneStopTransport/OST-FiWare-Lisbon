#!/usr/bin/env python
# encoding: utf-8
import os
import socket

from exceptions import FiWareError


# FI-WARE Host and Operations
FIWARE_HOST = os.environ.get('FIWARE_HOST')

def get_fiware_api(update=False):
    global FIWARE_HOST
    if not FIWARE_HOST:
        raise FiWareError('No Fi-Ware Host')
    if 'http://' not in FIWARE_HOST:
        FIWARE_HOST = 'http://' + FIWARE_HOST
    if update:
        return FIWARE_HOST + '/ngsi10/updateContext'   
    return FIWARE_HOST + '/ngsi10/queryContext'
    
FIWARE_GOOD_STATUS = {
    'code' : '200',
    'reasonPhrase' : 'OK'
}

# OST API URLs and API Key  
OST_API_MAIN_URL = 'https://api.ost.pt/'
OST_API_KEY = os.environ.get('OST_SERVER_KEY')

def get_ost_api(model_name, api_key):
    if model_name and api_key:
        return OST_API_MAIN_URL + model_name + '?key=%s' % api_key
    return OST_API_MAIN_URL

# GTFS APIs
API_AGENCIES    = get_ost_api('agencies',   OST_API_KEY)
API_ROUTES      = get_ost_api('routes',     OST_API_KEY)
API_STOPS       = get_ost_api('stops',      OST_API_KEY)
API_TRIPS       = get_ost_api('trips',      OST_API_KEY)
API_STOPTIMES   = get_ost_api('stoptimes',  OST_API_KEY)

AGENCY_QUERY = '&agency=%s'
ROUTE_QUERY = '&route=%s'

# GTFS Constants
CP_NAME  = 'CP - Comboios de Portugal'
AGENCY   = 'Agency'
ROUTE    = 'Route'
TRIP     = 'Trip'
STOP     = 'Stop'
STOPTIME = 'StopTime'
ID       = 'id'


# RabbitMQ & Celery
if socket.gethostname().endswith('ost.pt'):
    MQ_HOST     = os.environ.get('MQ_HOST_PROD')
else:
    MQ_HOST     = os.environ.get('MQ_HOST_TEST')
MQ_USER     = os.environ.get('MQ_USER')
MQ_PASSWORD = os.environ.get('MQ_PASSWORD')
MQ_VHOST    = os.environ.get('MQ_VHOST')

