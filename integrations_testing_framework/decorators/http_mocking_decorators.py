import json
import os
from functools import wraps
import responses
from requests.adapters import HTTPAdapter

from integrations_testing_framework.models import HttpRequest

original_http_send = HTTPAdapter.send

try:
    from unittest import mock as std_mock
except ImportError:
    import mock as std_mock


def _register_mock_response(req: HttpRequest):
    content_type_header = 'Content-Type'
    content_type = req.response_headers[content_type_header] if content_type_header in req.response_headers else 'application/json'
    responses.add(
        method=req.request_method,
        url=req.request_url,

        body=req.response_body,
        status=req.response_status,
        content_type=content_type,
    )


def intercept_requests(file_uri: str, generate=False):
    """
    A decorator that will intercept HTTP calls made through the requests module and depending on the
    supplied configuration will either save the call data to a file or will mock the request with data
    from the given file.

    Each HTTP call is represented by an instance of the HttpRequest class.
    Each line in written/read from the file contains a serialized HttpCall object for each request.
    """
    target_send = "requests.adapters.HTTPAdapter.send"

    def intercept_and_write_response(adapter, request, **kwargs):
        response = original_http_send(adapter, request, **kwargs)
        req = HttpRequest.from_http_response(response)
        with open(file_uri, 'a') as file:
            file.write(req.to_json() + '\n')
        return response

    def intercept_responses(func):
        try:
            os.remove(file_uri)
        except:
            pass
        patcher = std_mock.patch(target=target_send, new=intercept_and_write_response)
        try:
            patcher.start()
            func()
        finally:
            patcher.stop()

    def mock_responses(func):
        with open(file_uri, 'r') as file:
            lines = file.readlines()
            for line in lines:
                req = HttpRequest.from_dict(json.loads(line))
                _register_mock_response(req)

        @responses.activate
        def wrapper():
            func()

        wrapper()

    def decorator(func):
        @wraps(func)
        def interceptor():
            if generate:
                intercept_responses(func)
            else:
                mock_responses(func)

        return interceptor

    return decorator
