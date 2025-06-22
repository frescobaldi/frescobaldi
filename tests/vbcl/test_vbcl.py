import pytest

from vbcl import *

def test_empty():
    assert parse('') == {}

def test_empty_file():
    assert parse_file('/dev/null') == {}
