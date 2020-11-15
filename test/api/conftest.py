import os

import yaml
import pytest


@pytest.fixture
def cases():
    with open(f'{os.path.dirname(__file__)}/assets/testcases_api.yaml', 'r') as yml:
        cases = yaml.load(yml, Loader=yaml.FullLoader)
    yield cases
