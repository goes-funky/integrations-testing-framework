import json


def assert_matching_file_contents(file_1, file_2):
    i = 0
    for line in file_1:
        expected = line.rstrip()
        actual = file_2.readline().rstrip()

        error_msg = f'Output does not match between files.\n\nExpected: \n{expected}\nActual: \n{actual}'
        assert expected == actual, error_msg
        i += 1

    if i == 0:
        raise Exception("File is empty.")

        
def select_schema(catalog_path: str, stream_name: str, stream_key: str = 'name') -> str:
    """
    Creates a catalog file with the stream_name selected.
    Example: @with_sys_args(['--config', config_path, '--catalog', utils.select_schema('all-streams.json', 'epics')])

    :param str catalog_path: a path of a catalog
    :param str stream_name: the name of the stream to be modified
    :param str stream_key: the key that is using for stream dict to select the desired stream
    :return: the path of the catalog created as string
    :rtype: str
    """
    f = open(catalog_path, "r")
    catalog = f.read()
    f.close()

    catalog = json.loads(catalog)

    for stream in catalog['streams']:
        if stream[stream_key] == stream_name:
            stream['metadata'][0]['metadata']['selected'] = True

    # Open the file for writing.
    f = open(f"tests/catalogs/{stream_name}.json", "w")
    f.write(json.dumps(catalog))
    f.close()

    return f"tests/catalogs/{stream_name}.json"
