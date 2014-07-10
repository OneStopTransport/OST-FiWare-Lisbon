#!/usr/bin/env python
# encoding: utf-8
from celery.task import task
from colorama import Fore

from connector import Connector
from errors import CKANError


@task(name='transfer_gtfs_ckan', ignore_result=True)
def transfer_gtfs_ckan():
    try:
        print 'Retrieving GTFS data from OST...',
        connector = Connector()
        connector.fetch_gtfs()
        print 'Done.'
        print 'Pushing GTFS files to CKAN\'s DataStore...',
        connector.push_to_ckan()
        print 'Done.'
    except CKANError as error:
        message = Fore.RED + str(error) + Fore.RESET + ': ' + \
            error.message
        print('\n> ' + message)

if __name__ == '__main__':
    transfer_gtfs_ckan()
