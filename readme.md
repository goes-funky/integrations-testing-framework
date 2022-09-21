# Integrations Testing Framework
Set of utilities to write tests for HTTP based integrations. 

## Decorators
```
@assert_stdout_matches(file_path)
```
Asserts error if the content written to the stdout from the wrapped method does not match the content from the provided file.

```
@write_stdout(file_path)
```
Redirects the content written to the stdout from the wrapped method to the provided file.

```
@with_sys_args(['arg1', 'arg2', 'arg3'])
```
Sets the supplied system args inside the wrapped function's scope.

```
@intercept_requests(file_path, generate=False, ignore_on_match=None, filter_req_headers=['authorization'],
                    filter_req_params=None, filter_req_data=None, filter_resp_data=None,
                    filter_resp_data_except=None)
```
Intercepts HTTP requests made by the wrapped method.
- **generate:**
  - True: requests made goes to the actual server, requests and their responses are serialized and saved to the provided file.
  - False: requests made are matched and mocked using the content from the provided file.
- **ignore_on_match:** List of request attributes that should be ignored while matching with recorded requests.
- **filter_req_headers:** List of request headers that should be replaced with dummy value before saving/matching request to/from the file.
- **filter_req_params:** List of request query parameters that should be replaced with dummy value before saving/matching request to/from the file.
- **filter_req_data:** List of request body keys that should be replaced with dummy value before saving/matching request to/from the file (for content-type application/json).
- **filter_resp_data:** List of response body keys that should be replaced with dummy values before saving to the file (for content-type application/json). Everything else other than these keys would be preserved. Decorated method would still receive actual response.
- **filter_resp_data_except:** Everything in response body other than these keys should be replaced with dummy value before saving to the file (for content-type application/json). Decorated method would still receive actual response.


## Usage

### Standard Usage
#### Step 1
Run the test making requests to the actual server, record responses and tap output to file.
```
@write_stdout('./output/example.txt')
@intercept_requests('./requests/example.txt', generate=True)
@with_sys_args(['--config', <config_path>, '--catalog', <catalog_path>])
def test_stream_example():
    tap_example.main()
```
#### Step 2
Run the test mocking requests responses from the recorded file, compare tap output with the one recorded in step 1.
```
@assert_stdout_matches('./output/example.txt')
@intercept_requests('./requests/example.txt', generate=False)
@with_sys_args(['--config', <config_path>, '--catalog', <catalog_path>])
def test_stream_example():
    tap_example.main()
```

### Handle Randomness in Request
Requests made with (generate=False) are matched and mocked using the content in the recorded file. If there is some sort of randomness in request (e.g. a UUID in request query parameter that is generated on runtime from tap code), request matching with the recorded data would fail.    
To handle such cases, you can select attributes of the request that should be ignored while matching with recorded requests.
```
# Ignore request query parameters while matching with requests from the recorded file
@assert_stdout_matches('./output/example.txt')
@intercept_requests('./requests/example.txt', generate=False, ignore_on_match=['query'])
@with_sys_args(['--config', <config_path>, '--catalog', <catalog_path>])
def test_stream_example():
    tap_example.main()
```
> **Caution:** Ignoring request attributes might result in multiple matches for a request. In that case next request that has not already been matched would be selected.

### Hide Sensitive Data in Request
You can opt to replace value of certain parameters in requests query parameters, headers and body with dummy value, before saving requests to the file (generate=True).
On request mocking (generate=False) provided request parameters would be replaced with same dummy value before performing request match.
```
# Provide name of parameters through appropriate argument while calling 'intercept_requests' decorator

# For example to replace value of 'client_id' and 'client_secret' query parameters with dummy value
filter_req_params=['client_id', 'client_secret']

# For example to replace value of 'client_id' and 'authorization' headers with dummy value
filter_req_headers=['client_id', 'authorization']

# For example to replace value of 'client_id' and 'client_secret' keys in request body with dummy value
filter_req_data=['client_id', 'client_secret']
```
> **Caution:** Replacing a value that is the only distinction between two requests would result in multiple matches for a request at the time of mocking. In that case next request that has not already been matched would be selected.

### Hide Sensitive Data in Response
You can select to update requests responses before saving them to the file (generate=True).
```
# Provide list of keys in 'filter_resp_data' argument, that should be replaced with dummy data preserving everything else

# Provide list of keys in 'filter_resp_data_except' argument, that should be preserved replacing everting else with dummy data
```

> **Note:** Decorated method still receives actual response.

> **Limitation:** Response update only works for 'content-type: application/json'.

Since decorated method still receives actual response, tap output would still contain sensitive data from response.
To hide sensitive content from tap output, we have to write tests in 3 steps instead of 2.
```
# Step 1
# Run the test making requests to the actual server, record responses to the file.
@intercept_requests('./requests/example.txt', generate=True, filter_resp_data OR filter_resp_data_except)
@with_sys_args(['--config', <config_path>, '--catalog', <catalog_path>])
def test_stream_example():
    tap_example.main()

# Step 2
# Run the test mocking requests responses from the recorded file, save tap output to the file.
@write_stdout('./output/example.txt')
@intercept_requests('./requests/example.txt', generate=False)
@with_sys_args(['--config', <config_path>, '--catalog', <catalog_path>])
def test_stream_example():
    tap_example.main()


# Step 3
# Run the test mocking requests responses from the recorded file, compare tap output with the one recorded in step 2.
@assert_stdout_matches('./output/example.txt')
@intercept_requests('./requests/example.txt', generate=False)
@with_sys_args(['--config', <config_path>, '--catalog', <catalog_path>])
def test_stream_example():
    tap_example.main()
```

## TODO

- [ ] Add interface to allow mocking requests programmatically.
- [ ] Extend response update to more content-types.
- [ ] Add more utils.

## Changelog
- 0.3.0 Multiple enhancement allowing user to:
  - Ignore parts of a request while matching with recorded requests.
  - Replace sensitive data in requests query parameters, headers and body with dummy data.
  - Update response body replacing actual data with dummy data (for content-type application/json).
- 0.2.1 Requests are now saved in yaml format.
- 0.2.0 Replaced Responses with VCR for better compatibility with other libraries that requests and secret masking.


