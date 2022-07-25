import vcr
from functools import wraps
from pathlib import Path


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
            if generate:
                # Emptying file as vcr does not do this by default
                Path(file_uri).unlink(missing_ok=True)
            with vcr.use_cassette(file_uri,
                                  record_mode=record_mode,
                                  filter_headers=['authorization'],
                                  decode_compressed_response=True,
                                  match_on=['method', 'scheme', 'host', 'port', 'path', 'query', 'body']) as cass:
                if generate is False:
                    cass.allow_playback_repeats = False
                func(*args, **kwargs)
                if generate is False:
                    assert cass.all_played is True, "not all previously recorded requests were made"
        return interceptor

    return decorator
