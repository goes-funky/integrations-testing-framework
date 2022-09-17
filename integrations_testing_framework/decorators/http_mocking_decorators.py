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
# Preserve characters during string anonymization
_ANON_PRESERVE_CHARS = set(r'!@#$%^&*_-+=()[]{}\/<>,.?')


def intercept_requests(file_uri: str, generate=False, ignore_on_match=None, replace_req_headers=['authorization'],
                       replace_req_params=None, replace_req_data=None, anonymize_resp_data=False,
                       anonymize_resp_data_skip_keys=None):
    """
    A decorator that will intercept HTTP calls and depending on the supplied configuration will either save the call
    data to a file or will mock the request with data from the given file.

    :param str file_uri: file path for storing/mocking requests.
    :param bool generate: True: Record requests to the file, False: Mock request from data present in the file.
    :param list ignore_on_match: Ignore attributes of the request while matching with recorded requests.
        Possible values:
            'method', 'scheme', 'host', 'port', 'path', 'query', 'body'
        Examples:
            Ignore query parameters and body while matching request
            ignore_on_match=['query', 'body']
        Note: If there are multiple matches of a request in the file, first match that has not already been played would
        be selected.
    :param list replace_req_headers: List of request headers to be replaced with dummy values before saving/matching request to/from the file.
        Example:
            Replace 'client-id' and 'client-secret' headers value
            replace_req_headers=['client-id', 'client-secret']
    :param list replace_req_params: List of request query parameters to be replaced with dummy values before saving/matching request to/from the file.
        Example:
            Replace 'client-id' and 'client-secret' values in query parameters
            replace_req_params=['client-id', 'client-secret']
    :param list replace_req_data: List of request post body attributes to be replaced with dummy values before saving/matching request to/from the file.
        Example:
            Replace 'access_token' value in request body
            replace_req_data=['access_token']
        Note: Only works for POST method.
              Might not work well for content-types other than JSON.
    :param bool anonymize_resp_data: Anonymize response body before saving to file.
        Note: Only works for content-type JSON at the moment.
              Decorated method would still receive actual response.
    :param list anonymize_resp_data_skip_keys: List of attributes to be preserved while anonymizing response body.
        Example:
            Don't anonymize value of 'id' and 'sync_timestamp' fields in response body
            anonymize_resp_data_skip_keys=['id', 'sync_timestamp']
    """
    record_mode = 'all' if generate else 'none'
    match_on = _MATCH_ON - set(ignore_on_match) if ignore_on_match else _MATCH_ON
    match_on = list(match_on)
    replace_req_data = _to_list_of_tuple(replace_req_data or [])
    replace_req_params = _to_list_of_tuple(replace_req_params or [])
    replace_req_headers = _to_list_of_tuple(replace_req_headers or [])
    kwargs = {'anon_data_skip_keys': anonymize_resp_data_skip_keys}
    before_record_response = partial(_before_record_response, **kwargs) if anonymize_resp_data and generate else None

    def decorator(func):
        @wraps(func)
        def interceptor(*args, **kwargs):
            if generate:
                # Emptying file as vcr does not do this by default
                Path(file_uri).unlink(missing_ok=True)
            with vcr.use_cassette(file_uri,
                                  record_mode=record_mode,
                                  filter_headers=replace_req_headers,
                                  filter_query_parameters=replace_req_params,
                                  filter_post_data_parameters=replace_req_data,
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
    Callback for processing response before recording to file.
    """
    # Supported content-types for response body anonymization
    anon_supported_content_types = {
        'application/json': _anonymize_json
    }
    # Anonymize response body, currently works only for JSON
    body = response['body']['string']
    # Read content-type
    content_type = _get_content_type(response)
    if content_type not in anon_supported_content_types:
        LOGGER.warning('Unsupported content-type "%s" for anonymization', content_type)
        return response
    anon_function = anon_supported_content_types[content_type]
    try:
        anon_body = anon_function(body, skip_keys=kwargs.get('anon_data_skip_keys'))
    except ValueError as err:
        raise ValueError('Failed to anonymize response body') from err
    response['body']['string'] = anon_body
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


def _anonymize_json(data, skip_keys=None):
    """
    Anonymize JSON.
    :param string data: JSON data.
    :param list skip_keys: Keys to be skiped.
    :return: Anonymized JSON.
    :type: string
    :raises ValueError: for invalid JSON.
    """
    skip_keys = set(skip_keys) if skip_keys else {}

    def anonymize_data(_data):
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
            return ''.join([x if x in _ANON_PRESERVE_CHARS else 'X' for x in _data])
        # Complex types
        if isinstance(_data, list):
            return [anonymize_data(item) for item in _data]
        if isinstance(_data, dict):
            return {key: value if key in skip_keys else anonymize_data(value) for key, value in _data.items()}
    json_data = json.loads(data)
    return json.dumps(anonymize_data(json_data), indent=4)


def _to_list_of_tuple(list_of_strings):
    """
    Covert list of strings to list of tuples.
    :param list list_of_strings: List of strings.
    :return: List of (string, XXXX) tuples.
    :type: list
    """
    return [(string, ''.join(['X' for _ in range(len(string))])) for string in list_of_strings]
