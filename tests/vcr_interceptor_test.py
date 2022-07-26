import urllib.request

from vcr.errors import CannotOverwriteExistingCassetteException

from integrations_testing_framework.decorators.http_mocking_decorators import intercept_requests
import pytest


@intercept_requests('cassette', generate=False)
def test_request():
    response = urllib.request.urlopen('http://www.iana.org/domains/reserved').read()
    assert 'domains' in response.decode('utf8')


def test_auth_removal():
    @intercept_requests('cassette2', generate=True)
    def test_auth_request():
        request = urllib.request.Request('http://www.iana.org/domains/reserved', method='GET')
        request.add_header("Authorization", "Bearer " + 'some Test token');
        response = urllib.request.urlopen(request).read()
        assert 'domains' in response.decode('utf8')
    test_auth_request()
    with open('cassette2', 'r') as cassette2:
        text = cassette2.read()
        assert 'some Test token' not in text


def test_too_few_requests():
    @intercept_requests('cassette3', generate=False)
    def test_request_cassette_with_two_requests():
        response = urllib.request.urlopen('http://www.iana.org/domains/reserved').read()
        assert 'domains' in response.decode('utf8')

    with pytest.raises(AssertionError) as err:
        test_request_cassette_with_two_requests()
    assert "not all previously recorded requests were made" in str(err.value)


def test_too_many_requests():
    @intercept_requests('cassette3', generate=False)
    def test_three_request_for_cassette_with_two_requests():
        urllib.request.urlopen('http://www.iana.org/domains/reserved').read()
        urllib.request.urlopen('http://www.iana.org/domains/reserved').read()
        urllib.request.urlopen('http://www.iana.org/domains/reserved').read()

    with pytest.raises(CannotOverwriteExistingCassetteException):
        test_three_request_for_cassette_with_two_requests()