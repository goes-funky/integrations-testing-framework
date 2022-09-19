import urllib.request

from vcr.errors import CannotOverwriteExistingCassetteException

from integrations_testing_framework.decorators.http_mocking_decorators import intercept_requests
import pytest
import requests


@intercept_requests('tests/cassette', generate=False)
def test_request():
    response = urllib.request.urlopen('https://www.iana.org/domains/reserved').read()
    assert 'domains' in response.decode('utf8')


def test_auth_removal():
    @intercept_requests('tests/cassette2', generate=True)
    def test_auth_request():
        request = urllib.request.Request('https://www.iana.org/domains/reserved', method='GET')
        request.add_header("Authorization", "Bearer " + 'some Test token');
        response = urllib.request.urlopen(request).read()
        assert 'domains' in response.decode('utf8')
    test_auth_request()
    with open('tests/cassette2', 'r') as cassette2:
        text = cassette2.read()
        assert 'some Test token' not in text


def test_too_few_requests():
    @intercept_requests('tests/cassette3', generate=False)
    def test_request_cassette_with_two_requests():
        response = urllib.request.urlopen('https://www.iana.org/domains/reserved').read()
        assert 'domains' in response.decode('utf8')

    with pytest.raises(AssertionError) as err:
        test_request_cassette_with_two_requests()
    assert "not all previously recorded requests were made" in str(err.value)


def test_too_many_requests():
    @intercept_requests('tests/cassette3', generate=False)
    def test_three_request_for_cassette_with_two_requests():
        urllib.request.urlopen('https://www.iana.org/domains/reserved').read()
        urllib.request.urlopen('https://www.iana.org/domains/reserved').read()
        urllib.request.urlopen('https://www.iana.org/domains/reserved').read()

    with pytest.raises(CannotOverwriteExistingCassetteException):
        test_three_request_for_cassette_with_two_requests()


def test_ignore_on_match():
    """
    Test 'ignore_on_match'.
    """
    @intercept_requests('tests/test_cassette', generate=True)
    def actual_request():
        requests.get('https://httpbin.org/anything',
                     params={'param1': 'value1'},
                     timeout=10)

    @intercept_requests('tests/test_cassette', generate=False, ignore_on_match=['query'])
    def mocked_request():
        requests.get('https://httpbin.org/anything',
                     params={'param1': 'value1_new'},
                     timeout=10)

    actual_request()
    mocked_request()


def test_filter_request_params():
    """
    Test 'filter_req_params'.
    """
    @intercept_requests('tests/test_cassette', generate=True, filter_req_params=['param1'])
    def actual_request():
        requests.get('https://httpbin.org/anything',
                     params={'param1': 'value1'},
                     timeout=10)

    @intercept_requests('tests/test_cassette', generate=False, filter_req_params=['param1'])
    def mocked_request():
        requests.get('https://httpbin.org/anything',
                     params={'param1': 'value123'},
                     timeout=10)

    actual_request()
    mocked_request()


def test_filter_request_data():
    """
    Test 'filter_req_data'.
    """
    @intercept_requests('tests/test_cassette', generate=True, filter_req_data=['key1'])
    def actual_request():
        requests.post('https://httpbin.org/anything',
                      json={'key1': 'value1'},
                      timeout=10)

    @intercept_requests('tests/test_cassette', generate=False, filter_req_data=['key1'])
    def mocked_request():
        requests.post('https://httpbin.org/anything',
                      json={'key1': 'value123'},
                      timeout=10)

    actual_request()
    mocked_request()


def test_filter_response_data():
    """
    Test 'filter_resp_data'.
    """
    @intercept_requests('tests/test_cassette', generate=True, filter_resp_data=['key1'])
    def actual_request():
        requests.post('https://httpbin.org/anything',
                      json={'key1': 'value1', 'key2': 'value2'},
                      timeout=10)

    @intercept_requests('tests/test_cassette', generate=False)
    def mocked_request():
        response = requests.post('https://httpbin.org/anything',
                                 json={'key1': 'value1', 'key2': 'value2'},
                                 timeout=10)
        json_response = response.json()['json']
        assert json_response['key1'] != 'value1' and json_response['key2'] == 'value2'

    actual_request()
    mocked_request()


def test_filter_response_data_except():
    """
    Test 'filter_resp_data_except'.
    """
    @intercept_requests('tests/test_cassette1', generate=True, filter_resp_data_except=['key1'])
    def actual_request():
        requests.post('https://httpbin.org/anything',
                      json={'key1': 'value1', 'key2': 'value2'},
                      timeout=10)

    @intercept_requests('tests/test_cassette1', generate=False)
    def mocked_request():
        response = requests.post('https://httpbin.org/anything',
                                 json={'key1': 'value1', 'key2': 'value2'},
                                 timeout=10)
        json_response = response.json()['json']
        assert json_response['key1'] == 'value1' and json_response['key2'] != 'value2'

    actual_request()
    mocked_request()
