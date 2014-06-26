#!/usr/bin/env python
# encoding: utf-8
from celery.task import task
from colorama    import Fore

from constants  import CP_NAME
from constants  import AGENCY
from constants  import ROUTE
from constants  import STOP
from constants  import TRIP
from constants  import STOPTIME
from constants  import ID
from crawler    import Crawler
from errors     import APIKeyError
from errors     import CrawlerError
from errors     import OSTError
from errors     import FiWareError
from importer   import FiWare
from utils      import get_error_message


@task(name='transfer_gtfs', ignore_result=True)
def transfer_gtfs(agency_name=None):
    """
      Fetch CP data from OST APIs and put them on ContextBroker
      # 1st) Agency == CP
      # 2nd) CP Routes
      # 3rd) CP Stops
      # 4th) CP Trips
      # 5th) CP StopTimes
    """
    try:
        # Instantiate the OST Crawler
        crawler = Crawler()
        # And the FiWare data inserter
        fiware = FiWare()
        # Validate agency_name attribute
        if not agency_name:
            agency_name = CP_NAME
        # Get Data from OST and put into ContextBroker
        print '> Inserting Agency...   ',
        agency = crawler.get_agency(agency_name)
        agency_id = agency.get(ID)
        fiware.insert_data(agency, content_type=AGENCY)
        print 'Done.'
        # Get routes with agency == CP
        print '> Inserting Routes...   ',
        routes = crawler.get_data_by_agency(agency_id, content_type=ROUTE)
        fiware.insert_data(routes, content_type=ROUTE)
        print 'Done:', len(fiware.get_data(content_type=ROUTE)['contextResponses'])
        print '> Inserting Stops...    ',
        # Get trips which route ID is on the routes list
        stops = crawler.get_data_by_agency(agency_id, content_type=STOP)
        fiware.insert_data(stops, content_type=STOP)
        print 'Done:', len(fiware.get_data(content_type=STOP)['contextResponses'])
        # Get route IDs
        route_ids = fiware.get_ids(fiware.get_data(content_type=ROUTE))
        print '> Inserting Trips...    ',
        # Get trips which route ID is on the routes list
        trips = crawler.get_data_from_routes(route_ids, content_type=TRIP)
        fiware.insert_data(trips, content_type=TRIP)
        print 'Done:', len(fiware.get_data(content_type=TRIP)['contextResponses'])
        print '> Inserting StopTimes...',
        # Get stoptimes which route ID is on the routes list
        stoptimes = crawler.get_data_from_routes(route_ids, content_type=STOPTIME)
        fiware.insert_data(stoptimes, content_type=STOPTIME)
        print 'Done:', len(fiware.get_data(content_type=STOPTIME)['contextResponses'])
    except (APIKeyError, CrawlerError, OSTError, FiWareError) as error:
        message = get_error_message(error)
        print(Fore.RED + str(error) + Fore.RESET + ':' + message)
        
if __name__ == '__main__':
    transfer_gtfs()