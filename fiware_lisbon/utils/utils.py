#!/usr/bin/env python
# encoding: utf-8
from itertools import izip_longest
import os

from colorama import Fore

from .errors import CKANError
from .errors import FiWareError


CKAN_TYPES = ['datastore', 'package', 'resource']

CKAN_URLS = {
    'create': '/api/action/{type}_create',
    'delete': '/api/action/{type}_delete',
    'search': '/api/action/{type}_search',
    'show': '/api/action/{type}_show',
    'upsert': '/api/action/{type}_upsert',
    'package_list': '/api/action/package_list',
}


def grouper(iterable, n, fillvalue=None):
    """ Collect data into fixed-length chunks or blocks """
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)


def get_file_path(dataset_name, file_name, file_ext):
    """ Returns the file directory of a data file """
    file_header = 'file://'
    data_dir = ''.join([os.getcwd(), '/ckan/data/', dataset_name, '/'])
    return ''.join([file_header, data_dir, file_name, file_ext])


def get_extension(file_format):
    """ Returns the file extension of a given format """
    from utils.constants import GTFS_EXTENSION
    if file_format:
        file_format = file_format.replace('.', '')
        return ''.join(('.', file_format.lower()))
    return GTFS_EXTENSION


def get_ckan_api(ckan_host, ckan_type, ckan_action):
    """
      Gets the best API URL to be used with CKAN
    """
    if not ckan_host:
        raise CKANError('No CKAN Host')
    if not ckan_type or ckan_type not in CKAN_TYPES:
        raise CKANError('No CKAN type or Invalid CKAN type')
    if ckan_host.endswith('/'):
        ckan_host = ckan_host[:-1]
    url = ckan_host + CKAN_URLS[ckan_action] if CKAN_URLS.get(ckan_action) \
        else ckan_host + CKAN_URLS['package_list']
    return url.format(type=ckan_type)


def get_ckan_error(error, api_url):
    """
      Returns a string with the error type, name and the url
    """
    error_type, error_name = '', ''
    for key, value in error.iteritems():
        if key == '__type':
            error_type = value
        else:
            error_name = value[0] if type(value) == type(list()) else value
    error = ''.join([error_type, ' - ', error_name, ' - ', api_url])
    return error


def get_error_message(error):
    """
      Generic method that pretty prints an error message
      when fiware's crawler/updater fails
    """
    message_get = ' Unable to fetch data, '
    message_put = ' Unable to insert data, '
    if 'No API Key was provided' in error.message:
        message = message_get + \
            'please check if you have an API key on your ' + \
            'environment by executing the following command: ' + \
            Fore.GREEN + 'echo $OST_SERVER_KEY'
    elif 'Invalid key' in error.message:
        message = message_get + \
            ' Please check if your key is a valid Server Key on www.ost.pt'
    elif 'OST is down' in error.message:
        message = message_get + \
            ' We\'re sorry but www.ost.pt seems to be down'
    elif 'No Agency ID' in error.message:
        message = message_get + \
            ' There was some problem retrieving data about CP'
    elif 'update unsuccessful' in error.message:
        message = message_put + error.message
    else:
        message = message_get + error.message
    return message


def get_fiware_api(fiware_host, update=False):
    """
      Gets the correct URL to fetch or insert data
      from/to the Orion Context Broker
    """
    if not fiware_host:
        raise FiWareError('No Fi-Ware Host')
    if fiware_host.endswith('/'):
        fiware_host = fiware_host[:-1]
    if 'http://' not in fiware_host:
        fiware_host = 'http://' + fiware_host
    if update:
        return fiware_host + '/ngsi10/updateContext'
    return fiware_host + '/ngsi10/queryContext'


def get_ost_api(api, model_name, api_key, params=None):
    """
      Gets the correct URL to fetch data
      from OST depending on the model_name
    """
    if api and model_name and api_key:
        key = '?key={key}'.format(key=api_key)
        api = ''.join([api, model_name, key])
        if params is not None:
            for key, value in params.iteritems():
                api = ''.join([api, '&', key, '=', value])
    return api


def get_string_type(attribute):
    """
      Receives a string and checks if it's an integer
      or a float, returning 'string' by default
    """
    try:
        if attribute.isdigit():
            return 'int'
        elif float(attribute):
            return 'float'
    except (ValueError, AttributeError):
        return 'string'
