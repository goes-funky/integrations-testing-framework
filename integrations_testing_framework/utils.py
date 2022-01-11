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