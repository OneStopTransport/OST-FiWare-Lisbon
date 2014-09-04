#!/usr/bin/env python
# encoding: utf-8
from celery.task import task
from colorama import Fore

from utils.constants import CP_NAME
from utils.constants import AGENCY
from utils.constants import ROUTE
from utils.constants import STOP
from utils.constants import TRIP
from utils.constants import STOPTIME
from utils.constants import ID
from utils.errors import APIKeyError
from utils.errors import CrawlerError
from utils.errors import OSTError
from utils.errors import FiWareError
from utils.utils import get_error_message
from crawler import Crawler
from importer import FiWare


@task(name='transfer_gtfs_cb', ignore_result=True)
def transfer_gtfs_cb(agency_name=None):
    """
      Fetches CP data from OST APIs and puts it on ContextBroker
      Uses the Crawler to fetch data and FiWare to import it.
      # 1st) Agency == CP
      # 2nd) CP Routes
      # 3rd) CP Stops
      # 4th) CP Trips
      # 5th) CP StopTimes
    """
    try:
        crawler = Crawler()
        fiware = FiWare()
        if agency_name is None:
            agency_name = CP_NAME
        print '> Inserting Agency...   ',
        agency = crawler.get_agency(agency_name)
        agency_id = agency.get(ID)
        fiware.insert_data(agency, content_type=AGENCY)
        print 'Done.'
        # ROUTES
        print '> Inserting Routes...   ',
        routes = crawler.get_data_by_agency(agency_id, content_type=ROUTE)
        fiware.insert_data(routes, content_type=ROUTE)
        routes_cb = fiware.get_data(content_type=ROUTE)['contextResponses']
        print 'Done:', len(routes_cb)
        # STOPS
        print '> Inserting Stops...    ',
        stops = crawler.get_data_by_agency(agency_id, content_type=STOP)
        fiware.insert_data(stops, content_type=STOP)
        stops_cb = fiware.get_data(content_type=STOP)['contextResponses']
        print 'Done:', len(stops_cb)
        # TRIPS
        route_ids = fiware.get_ids(fiware.get_data(content_type=ROUTE))
        print '> Inserting Trips...    ',
        trips = crawler.get_data_from_routes(route_ids, content_type=TRIP)
        fiware.insert_data(trips, content_type=TRIP)
        trips_cb = fiware.get_data(content_type=TRIP)['contextResponses']
        print 'Done:', len(trips_cb)
        # STOPTIMES
        print '> Inserting StopTimes...',
        times = crawler.get_data_from_routes(route_ids, content_type=STOPTIME)
        fiware.insert_data(times, content_type=STOPTIME)
        times_cb = fiware.get_data(content_type=STOPTIME)['contextResponses']
        print 'Done:', len(times_cb)
    except (APIKeyError, CrawlerError, OSTError, FiWareError) as error:
        message = get_error_message(error)
        print(Fore.RED + str(error) + Fore.RESET + ':' + message)

if __name__ == '__main__':
    transfer_gtfs_cb()
