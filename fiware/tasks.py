#!/usr/bin/env python
# encoding: utf-8
from celery.task import task
from colorama    import Fore

from .constants  import CP_NAME
from .constants  import AGENCY
from .constants  import ROUTE
from .constants  import STOP
from .constants  import TRIP
from .constants  import STOPTIME
from .constants  import ID
from .exceptions import APIKeyError
from .exceptions import CrawlerError
from .exceptions import OSTError
from .exceptions import FiWareError
from .utils      import Crawler
from .utils      import FiWare
from .utils      import get_error_message


@task(name='transfer_cp', ignore_result=True)
def transfer_cp():
    """
      Fetch CP data from OST APIs and put them on ContextBroker
      # 1st) Agency == CP
      # 2nd) CP Routes
      # 3rd) CP Trips
      # 4th) CP Stops
      # 5th) CP StopTimes
    """
    try:
        # Instantiate the OST Crawler
        crawler = Crawler()
        # And the FiWare data inserter
        fiware = FiWare()
        # Get Data from OST and put into ContextBroker
        print '> Inserting Agency...',
        agency = crawler.get_agency(CP_NAME)
        agency_id = agency.get(ID)    
        fiware.insert_data(agency, content_type=AGENCY)
        print 'Done.'
        # Get routes with agency == CP
        print '> Inserting Routes...',
        routes = crawler.get_routes(agency_id)
        fiware.insert_data(routes, content_type=ROUTE)
        print 'Done.'
        # Get route IDs
        print '> Insertings Trips...',
        route_ids = fiware.get_ids(fiware.get_data(content_type=ROUTE)[1])
        # Get trips which route ID is on the routes list
        trips = crawler.get_trips(route_ids)        
        fiware.insert_data(trips, content_type=TRIP)
        print 'Done.'
    except (APIKeyError, CrawlerError, OSTError, FiWareError) as error:
        message = get_error_message(error)
        print(Fore.RED + str(error) + Fore.RESET + ':' + message)
        
if __name__ == '__main__':
    transfer_cp()