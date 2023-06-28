import pytest


@pytest.fixture(scope="function")
def test_client():
    """test the client fixture to be defined here"""

    yield ''