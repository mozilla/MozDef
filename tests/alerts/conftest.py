def pytest_generate_tests(metafunc):
    if hasattr(metafunc.cls, 'test_cases'):
        metafunc.parametrize("test_case", metafunc.cls.test_cases, scope="class")
