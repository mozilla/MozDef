def pytest_generate_tests(metafunc):
    metafunc.parametrize("test_case", metafunc.cls.test_cases, scope="class")