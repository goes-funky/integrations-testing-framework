import sys
import vcr
import json
import logging
from functools import wraps, partial
from pathlib import Path

LOGGER = logging.getLogger()
LOGGER.addHandler(logging.StreamHandler(sys.stderr))

# Default match
_MATCH_ON = {'method', 'scheme', 'host', 'port', 'path', 'query', 'body'}
# Preserve characters during string update
_PRESERVE_CHARS = set(r'!@#$%^&*_-+=()[]{}\/<>,.?')


def intercept_requests(file_uri: str, generate=False, ignore_on_match=None, filter_req_headers=['authorization'],
                       filter_req_params=None, filter_req_data=None, filter_resp_data=None,
                       filter_resp_data_except=None):
    """
    A decorator that will intercept HTTP calls and depending on the supplied configuration will either save the call
    data to a file or will mock the request with data from the given file.

    :param str file_uri: File path for storing/mocking requests.
    :param bool generate: True: Record requests to the file, False: Mock request from content present in the file.
    :param list ignore_on_match: List of request attributes that should be ignored while matching with recorded
    requests.
        Possible values:
            'method', 'scheme', 'host', 'port', 'path', 'query', 'body'
        Examples:
            Ignore query parameters and body while matching request
            ignore_on_match=['query', 'body']
        Note: If there are multiple matches of a request in the file, first match that has not already been played would
        be selected.
    :param list filter_req_headers: List of request headers that should be replaced with dummy value before
    saving/matching request to/from the file.
        Example:
            Replace 'client-id' and 'client-secret' headers values
            filter_req_headers=['client-id', 'client-secret']
    :param list filter_req_params: List of request query parameters that should be replaced with dummy value before
    saving/matching request to/from the file.
        Example:
            Replace 'client-id' and 'client-secret' values in query parameters
            filter_req_params=['client-id', 'client-secret']
    :param list filter_req_data: List of request post body attributes that should be replaced with dummy value before
    saving/matching request to/from the file.
        Example:
            Replace 'access_token' value in request body
            filter_req_data=['access_token']
        Note: Only works for POST method.
              Might not work well for content-types other than JSON.
    :param list filter_resp_data: List of response body keys that should be replaced with dummy values
    before saving to the file. Everything else other than these keys would be preserved.
        Example:
            Replace 'email' and 'cell_number' with dummy values
            filter_resp_data=['email', 'cell_number']
        Note: Only works for content-type JSON at the moment.
              Decorated method would still receive actual response.
    :param list filter_resp_data_except: Everything in response body other than these keys should be replaced with dummy
    value before saving to the file.
        Example:
            Replace everything in response body with dummy values other than 'id' and 'sync_timestamp' keys
            filter_resp_data_except=['id', 'sync_timestamp']
        Note: Only works for content-type JSON at the moment.
              Decorated method would still receive actual response.
    """
    if filter_resp_data and filter_resp_data_except:
        raise ValueError('One of (filter_resp_data, filter_resp_data_except) can be used at a time')
    record_mode = 'all' if generate else 'none'
    match_on = _MATCH_ON - set(ignore_on_match) if ignore_on_match else _MATCH_ON
    match_on = list(match_on)
    filter_req_data = _to_list_of_tuple(filter_req_data or [])
    filter_req_params = _to_list_of_tuple(filter_req_params or [])
    filter_req_headers = _to_list_of_tuple(filter_req_headers or [])
    configs = {'data_update_keys': filter_resp_data, 'data_skip_keys': filter_resp_data_except}
    update_resp_data = filter_resp_data or filter_resp_data_except
    before_record_response = partial(_before_record_response, **configs) if update_resp_data and generate else None

    def decorator(func):
        @wraps(func)
        def interceptor(*args, **kwargs):
            if generate:
                # Emptying file as vcr does not do this by default
                Path(file_uri).unlink(missing_ok=True)
            with vcr.use_cassette(file_uri,
                                  record_mode=record_mode,
                                  filter_headers=filter_req_headers,
                                  filter_query_parameters=filter_req_params,
                                  filter_post_data_parameters=filter_req_data,
                                  before_record_response=before_record_response,
                                  decode_compressed_response=True,
                                  match_on=match_on) as cass:
                if generate is False:
                    cass.allow_playback_repeats = False
                func(*args, **kwargs)
                if generate is False:
                    assert cass.all_played is True, "not all previously recorded requests were made"
        return interceptor

    return decorator


def _before_record_response(response, **kwargs):
    """
    Callback for processing response before recording to the file.
    """
    # Supported content-types
    supported_content_types = {
        'application/json': _filter_json
    }
    # Replace content in response body, currently works only for JSON
    body = response['body']['string']
    # Read content-type
    content_type = _get_content_type(response)
    if content_type not in supported_content_types:
        LOGGER.warning('Unsupported content-type "%s" for response update', content_type)
        return response
    update_function = supported_content_types[content_type]
    try:
        updated_body = update_function(body,
                                       update_keys=kwargs.get('data_update_keys'),
                                       skip_keys=kwargs.get('data_skip_keys'))
    except ValueError as err:
        raise ValueError('Failed to update response body') from err
    response['body']['string'] = updated_body
    return response


def _get_content_type(response):
    """
    Get content type from response header.
    :param dict response: Response object.
    :return: Content type.
    :type: string
    """
    if 'headers' not in response:
        return None
    content_type = response['headers'].get('Content-Type') or response['headers'].get('content-type')
    if not content_type or not isinstance(content_type, list):
        return None
    content_type = content_type[0]
    content_type = content_type.split(';')[0]
    return content_type.lower().strip()


def _filter_json(data, update_keys=None, skip_keys=None):
    """
    Update values in JSON with dummy data.
    :param string data: JSON data.
    :param list update_keys: Keys that should be updated, rest would be not be altered.
    :param list skip_keys: Keys that should not be altered, rest would be updated.
    :return: Updated JSON.
    :type: string
    :raises ValueError: for invalid JSON.
    """
    update_keys = set(update_keys) if update_keys else {}
    skip_keys = set(skip_keys) if skip_keys else {}
    if update_keys and skip_keys:
        raise ValueError('Only one of (update_keys, skip_keys) can be used at a time')

    def update_data(_data):
        # Simple types
        if _data is None:
            return None
        # Invert bool value
        if isinstance(_data, bool):
            return not _data
        # Add 1 to numbers
        if isinstance(_data, (int, float)):
            return _data + 1
        # Replace characters in string with 'X'
        if isinstance(_data, str):
            return ''.join([x if x in _PRESERVE_CHARS else 'X' for x in _data])
        # Complex types
        if isinstance(_data, list):
            return [update_data(item) for item in _data]
        if isinstance(_data, dict):
            if skip_keys:
                return {key: update_data(value) if isinstance(value, dict) or key not in skip_keys else value
                        for key, value in _data.items()}
            if update_keys:
                return {key: update_data(value) if isinstance(value, dict) or key in update_keys else value
                        for key, value in _data.items()}
            # Update everything
            return {key: update_data(value) for key, value in _data.items()}
    json_data = json.loads(data)
    return json.dumps(update_data(json_data), indent=4)


def _to_list_of_tuple(list_of_strings):
    """
    Covert list of strings to list of tuples.
    :param list list_of_strings: List of strings.
    :return: List of (string, XXXX) tuples.
    :type: list
    """
    return [(string, ''.join(['X' for _ in range(len(string))])) for string in list_of_strings]
