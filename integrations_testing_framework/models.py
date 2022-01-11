import json
import requests


class HttpRequest:
    request_body: str
    request_headers: dict[str]
    request_method: str
    request_path_url: str
    request_url: str

    response_body: str
    response_headers: dict[str]
    response_status: int

    def __init__(self,
                 request_body: str,
                 request_headers: dict[str],
                 request_method: str,
                 request_path_url: str,
                 request_url: str,
                 response_body: str,
                 response_headers: dict[str],
                 response_status: int):
        self.request_body = request_body
        self.request_headers = request_headers
        self.request_method = request_method
        self.request_path_url = request_path_url
        self.request_url = request_url
        self.response_body = response_body
        self.response_headers = response_headers
        self.response_status = response_status

    @staticmethod
    def from_http_response(response: requests.Response):
        request = response.request

        return HttpRequest(
            request_body=request.body,
            request_headers=dict(request.headers),
            request_method=request.method,
            request_path_url=request.path_url,
            request_url=request.url,
            response_body=response.text,
            response_headers=dict(response.headers),
            response_status=response.status_code
        )

    @staticmethod
    def from_dict(dictionary: dict):
        return HttpRequest(
            request_body=dictionary['request_body'],
            request_headers=dictionary['request_headers'],
            request_method=dictionary['request_method'],
            request_path_url=dictionary['request_path_url'],
            request_url=dictionary['request_url'],
            response_body=dictionary['response_body'],
            response_headers=dictionary['response_headers'],
            response_status=dictionary['response_status'],
        )

    def to_json(self):
        return json.dumps(self, default=lambda o: vars(o), sort_keys=True)
