import vcr
from functools import wraps


def intercept_requests(file_uri: str, generate=False):
    """
    A decorator that will intercept HTTP calls made through the requests module and depending on the
    supplied configuration will either save the call data to a file or will mock the request with data
    from the given file.

    Each HTTP call is represented by an instance of the HttpRequest class.
    Each line in written/read from the file contains a serialized HttpCall object for each request.
    """

    record_mode = 'all' if generate else 'none'

    def decorator(func):
        @wraps(func)
        def interceptor(*args, **kwargs):
            with vcr.use_cassette(file_uri, record_mode=record_mode, filter_headers=['authorization']) as cass:
                cass.allow_playback_repeats = False
                func(*args, **kwargs)
                assert cass.all_played is True, "not all previously recorded requests were made"
        return interceptor

    return decorator
