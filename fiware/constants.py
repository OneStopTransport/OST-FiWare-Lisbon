import os

OST_API_MAIN_URL = "https://api.ost.pt/"
OST_API_KEY = os.environ.get('OST_SERVER_KEY')

def get_api(model_name, api_key):
    if model_name and api_key:
        return OST_API_MAIN_URL + model_name + "?key=%s" % api_key
    return OST_API_MAIN_URL

# GTFS APIs
API_AGENCIES    = get_api("agencies",   OST_API_KEY)
API_ROUTES      = get_api("routes",     OST_API_KEY)
API_STOPS       = get_api("stops",      OST_API_KEY)
API_TRIPS       = get_api("trips",      OST_API_KEY)
API_STOPTIMES   = get_api("stoptimes",  OST_API_KEY)

# GTFS Constants
CP_NAME = "CP - Comboios de Portugal"