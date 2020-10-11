def pytest_addoption(parser):
    parser.addoption("--bucket", action="store")
    parser.addoption("--function_name", action="store")


def pytest_generate_tests(metafunc):
    if "bucket" in metafunc.fixturenames and metafunc.config.option.bucket is not None:
        metafunc.parametrize("bucket", [metafunc.config.option.bucket])
    if "function_name" in metafunc.fixturenames and metafunc.config.option.function_name is not None:
        metafunc.parametrize("function_name", [metafunc.config.option.function_name])
