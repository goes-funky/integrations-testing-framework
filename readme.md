# Integrations Testing Framework

### Decorators
```
@assert_stdout_matches(file_path)
```
Asserts that the content written to the stdout from the wrapped method 
matches the content from the provided file.

```
@write_stdout(file_path)
```
Redirects the content written to the stdout from the wrapped method to 
the provided file.

```
@intercept_requests(file_path, generate=False)
```
Intercepts requests made through python's requests module.

If generate=True, the request data is serialized and written to the provided file.

If generate=False, the requuest data is loaded and mocked from the provided file.
```
@with_sys_args(['args'])
```
Sets the supplied system args inside the wrapped function's scope.

### Usage

Example test:
```
@assert_stdout_matches('./files/output.txt')
@intercept_requests('./files/requests.yaml', generate=False)
@with_sys_args(['--config', config_path, '--catalog', catalog_path])
def test_full_table_sync_spaces_and_teams():
    tap_clickup.main()
```

Example test generation:
```
@write_stdout('./files/output.txt')
@intercept_requests('./files/requests.yaml', generate=True)
@with_sys_args(['--config', config_path, '--catalog', catalog_path])
def test_full_table_sync_spaces_and_teams():
    tap_clickup.main()
```

### TODO

- [ ] Complete documentation
- [ ] Implement sensitive data masking
- [ ] Add custom request matchers
- [ ] Add more examples
- [ ] Add more utils

### Changelog
- 0.2.0 Replaced Responses with VCR for better compatibility with other libraries that requests and secret masking
  - Requests are now saved in yaml format
