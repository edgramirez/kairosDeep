import time
import requests
import codecs, json
from datetime import datetime, timedelta
import lib.common as com


def get_supported_actions():
    return ('GET', 'POST', 'PUT', 'DELETE')


def send_json(header, payload, action, url=None, **options):
    if action not in get_supported_actions() or url is None:
        raise Exception('Requested action: ({}) not supported. valid options are:'.
                        format(action, get_supported_actions()))

    retries = options.get('retries', 2)
    sleep_time = options.get('sleep_time', 1)
    expected_response = options.get('expected_response', 200)
    abort_if_exception = options.get('abort_if_exception', True)

    data = json.dumps(payload)

    for retry in range(retries):
        try:
            if action == 'GET':
                r = requests.get(url, data=data, headers=header)
            elif action == 'POST':
                r = requests.post(url, data=data, headers=header)
            elif action == 'PUT':
                r = requests.put(url, data=data, headers=header)
            else:
                r = requests.delete(url, data=data, headers=header)
            # com.log_debug('status: {}'.format(r.status_code))
            return r
        except requests.exceptions.ConnectionError as e:
            time.sleep(sleep_time)
            if retry == retries - 1 and abort_if_exception:
                raise Exception("Unable to Connect to server after {} retries\n. Exception: {}".format(retry, str(e)))
        except requests.exceptions.HTTPError as e:
            time.sleep(sleep_time)
            if retry == retries - 1 and abort_if_exception:
                raise Exception("Invalid HTTP response in {} retries\n. Original exception: {}".format(retry, str(e)))
        except requests.exceptions.Timeout as e:
            time.sleep(sleep_time)
            if retry == retries - 1 and abort_if_exception:
                raise Exception("Timeout reach in {} retries\n. Original exception: {}".format(retry, str(e)))
        except requests.exceptions.TooManyRedirects as e:
            time.sleep(sleep_time)
            if retry == retries - 1 and abort_if_exception:
                raise Exception("Too many redirection in {} retries\n. Original exception: {}".format(retry, str(e)))
