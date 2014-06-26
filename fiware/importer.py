#!/usr/bin/env python
# encoding: utf-8
import requests
import simplejson

from constants  import get_fiware_api
from constants  import FIWARE_GOOD_STATUS
from errors     import FiWareError


class FiWare(object):
    """ Helper to insert CP data into Context Broker """

    def wrap_content(self, content, content_type):
        """
          ContextBroker requires a specific JSON schema
          when inserting data. This method wraps the
          data to be inserted with that schema.
        """
        # This is the schema to be received by the ContextBroker
        fiware_content = {'contextElements': [], 'updateAction': 'APPEND'}
        try:
            # Element has id, act normally
            element_id = content.get('id', '')
            if not element_id:
                # There is no id but we can replace it with resource_uri
                element_id = [int(string) for string in \
                              value['resource_uri'].split('/') \
                              if string.isdigit()][0]
            element = {
                'type': content_type,
                'isPattern': 'false',
                'id': element_id,
                'attributes': [],
            }
            content.pop('resource_uri')
        except KeyError:
            print content, content_type
        for key, value in content.iteritems():
            if type(value) == type(dict()) and not key == 'point':
                keys = value.keys()
                if 'id' not in keys and 'resource_uri' in keys:
                    # No id but we can replace it with resource_uri
                    value = [int(string) for string in \
                             value['resource_uri'].split('/') \
                             if string.isdigit()][0]
                    key = 'id'
                else:
                    value = value.get('id')
            if key == 'point':
                # Coordinates are in latitude,longitude format
                coordinates = str(value['coordinates'][1]) + ',' \
                            + str(value['coordinates'][0])
                attribute = {
                    'name': 'coordinates',
                    'type': 'coords',
                    'value': coordinates,
                    'metadatas': [
                      {
                        'name': 'location',
                        'type': 'string',
                        'value': 'WSG84',
                      },
                    ],
                }
                element['attributes'].append(attribute)
                continue
            attribute = {
                'name': key,
                'value': value,
            }
            element['attributes'].append(attribute)
        fiware_content['contextElements'].append(element)
        # print simplejson.dumps(fiware_content, indent=' ' * 4) # DEBUG
        return simplejson.dumps(fiware_content)

    def handle_response(self, response):
        """
          Checks if the FiWare ContextBroker response
          contains errors, returning True if not and
          False if something went wrong.
        """
        fiware_error = 'FiWare returned:\n\n'
        if response.status_code != 200:
            return False, fiware_error + response.content
        content = simplejson.loads(response.content)
        if 'errorCode' in content.keys():
            return False, fiware_error + response.content
        if content['contextResponses'][0]['statusCode'] == FIWARE_GOOD_STATUS:
            return True, content

    def get_data(self, content_type, attributes=None):
        """
          Method to query data from the FiWare
          ContextBroker instance.
          - content_type = Entity type name
          - attributes = List of attributes to query
        """
        # Get the API URL and set Headers
        api_url = get_fiware_api()
        headers = {
                    'content-type': 'application/json',
                    'accept': 'application/json',
                  }
        json_data = {
            'entities': [
                {
                    'type': content_type,
                    'isPattern': 'true',
                    'id': '.*',
                },
            ],
        }
        # If the method received a list of attributes
        if attributes and type(attributes) == type(list()):
            json_data['attributes'] = attributes
        response = requests.post(\
                        api_url,
                        data=simplejson.dumps(json_data),
                        headers=headers,
                   )
        all_ok, response_content = self.handle_response(response)
        return response_content

    def get_ids(self, content):
        """
          Gets the list of ids of a query response
        """
        id_list = []
        if content:
            id_list = [each.get('contextElement')['id'] \
                        for each in content.get('contextResponses')]
        return id_list

    def insert_data(self, content, content_type):
        """
          Method to insert data into the FiWare
          ContextBroker instance.
        """
        # Get the API URL and set Headers
        api_url = get_fiware_api(update=True)
        headers = {
                    'content-type': 'application/json',
                    'accept': 'application/json',
                  }
        if type(content) == type(dict()):
            # Just one element, convert to a list
            content = [content]
        # Wrap the content with ContextBroker expected syntax
        for each in content:
            # Change the content to match ContextBroker expected JSON
            json_content = self.wrap_content(each, content_type)
            # Post the data
            response = requests.post( \
                                        api_url,
                                        data=json_content,
                                        headers=headers,
                                    )
            all_ok, response_content = self.handle_response(response)
            if all_ok is not True:
                response = simplejson.dumps(response_content)
                template = '{type} update unsuccessful.\n\n{resp}'
                message = template.format(type=content_type, resp=response)
                raise FiWareError(message)
        return all_ok
