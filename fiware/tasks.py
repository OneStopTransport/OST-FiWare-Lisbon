#!/usr/bin/env python
# encoding: utf-8
from celery.task import task
from colorama    import Fore

from .constants  import CP_NAME
from .exceptions import APIKeyError
from .exceptions import CrawlerError
from .exceptions import OSTError
from .utils      import Crawler


@task(name='transfer_cp', ignore_result=True)
def transfer_cp():
    """
      Fetch CP data from OST APIs and put them on ContextBroker
    """
    try:
        crawler = Crawler()
        agency = crawler.get_agency(CP_NAME)
        # TODO insert into fiware Context Broker
        routes = crawler.get_routes(agency.get('id'))
        # TODO ""
    except (APIKeyError, CrawlerError, OSTError) as e:
        error_type = "OSTError" if type(e) == OSTError else "APIKeyError"
        message = crawler.get_error_message(e)
        print(Fore.RED + error_type + Fore.RESET + ':' + message)
        
if __name__ == '__main__':
    transfer_cp()