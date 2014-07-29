#!/usr/bin/env python
# encoding: utf-8
from celery.task import task
from colorama import Fore

from connector import Connector
from errors import CKANError


@task(name='transfer_gtfs_ckan', ignore_result=True)
def transfer_gtfs_ckan(full_gtfs=False):
    # Pass full_gtfs as True if you want to import
    # all the GTFS data to CKAN.
    try:
        print 'Retrieving GTFS data from OST...',
        connector = Connector()
        if full_gtfs:
            connector.fetch_full_gtfs()
            print 'Done.'
            print 'Pushing GTFS files to CKAN\'s DataStore...',
            connector.push_to_ckan()
        else:
            connector.fetch_gtfs_stops()
            print 'Done.'
            print 'Importing Transit Stops to CKAN\'s DataStore...',
            connector.insert_stops_ckan()
            print 'Done.'
    except CKANError as error:
        message = Fore.RED + str(error) + Fore.RESET + ': ' + \
            error.message
        print('\n> ' + message)

if __name__ == '__main__':
    transfer_gtfs_ckan()
