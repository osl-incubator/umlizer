# -*- coding: utf-8 -*-
"""Tests for `pyuml` package."""

import pytest
import random

from pyuml import pyuml


@pytest.fixture
def generate_numbers():
    """Sample pytest fixture. Generates list of random integers.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """

    return random.sample(range(100),10)

