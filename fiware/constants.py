import os

from exceptions import FiWareError

# FI-WARE Host and Operations
FIWARE_IP = os.environ.get('FI_WARE_IP')

def get_fiware_api(update=False):
    if not FIWARE_IP:
        raise FiWareError('No Fi-Ware IP')
    if update:
        return 'http://' + FIWARE_IP + '/ngsi10/updateContext'   
    return 'http://' + FIWARE_IP + '/ngsi10/queryContext'
    
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