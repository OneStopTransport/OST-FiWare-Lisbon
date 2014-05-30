from colorama   import Fore

def get_error_message(error):
    """ Generic method for pretty printing an error message when crawler/updater fails """
    message_get = ' Unable to fetch data, '
    message_put = ' Unable to insert data, '
    if 'No API Key was provided' in error.message:
        message = message_get + 'please check if you have an API key on your ' + \
        'environment by executing the following command: ' + \
        Fore.GREEN + 'echo $OST_SERVER_KEY'
    elif 'URL without API Key' in error.message:
        message = message_get + error.message
    elif 'API not found' in error.message:
        message = message_get + error.message
    elif 'Invalid key' in error.message:
        message = message_get + ' Please check if your key is a valid Server Key on www.ost.pt'
    elif 'OST is down' in error.message:
        message = message_get + ' We\'re sorry but www.ost.pt seems to be down'
    elif 'No Agency ID' in error.message:
        message = message_get + ' There was some problem retrieving data about CP'
    elif 'update unsuccessful' in error.message:
        message = message_put + error.message
    return message