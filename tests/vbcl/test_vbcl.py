import pytest

# global function _() is required by the vbcl module
import i18n
i18n.install('en')

from vbcl import *

def test_empty_file():
    assert parse_file('/dev/null') == {}

def test_empty():
    assert parse('') == {}

def test_defaults():
    assert parse('', defaults={'key': '1'}) == {'key': '1'}
    assert parse('key: 2', defaults={'key': '1'}) == {'key': '2'}

def test_mandatory_key_missing():
    with pytest.raises(ValueError, match=r'VBCL Error: Missing mandatory key'):
        parse('', mandatory_keys=['key'])

def test_mandatory_key_default():
    # mandatory key must be in the input data, can't be supplied by defaults
    key = 'key'
    with pytest.raises(ValueError, match=r'VBCL Error: Missing mandatory key'):
        parse('', mandatory_keys=[key], defaults={key: '1'})

def test_comment():
    assert parse('# this is a comment') == {}
    assert parse('  # this is a comment') == {}

    # comments at the end of meaningful lines are not supported
    assert parse('key: my value # not a comment') == {'key': 'my value # not a comment'}

def test_one_line_value():
    assert parse('key: my value') == {'key': 'my value'}

    # empty value
    assert parse('key:') == {}
    assert parse('key: ') == {'key': ''}
    assert parse('key:  ') == {'key': ''}

def test_long_value():
    assert parse("key: <\nLong\ntext value\n>") == {'key': "Long\ntext value"}

    # empty value
    assert parse("key: <>") == {}
    assert parse("key: < >") == {}
    assert parse("key: <\n>") == {'key': ''}
    assert parse("key: <\n\n>") == {'key': ''}

def test_long_value_whitespace():
    assert parse("key: <  \n  Long  \n  \n  text value  \n  >  \n") == {'key': "Long\n\ntext value"}

def test_list():
    assert parse("key: [\napples\n]") == {'key': ['apples']}
    assert parse("key: [\napples\nbananas\n]") == {'key': ['apples', 'bananas']}

    # empty value
    assert parse("key: []") == {}
    assert parse("key: [ ]") == {}
    assert parse("key: [\n]") == {'key': []}
    assert parse("key: [\n\n]") == {'key': ['']}

def test_list_whitespace():
    assert parse("key: [  \n  apples  \n  \n  bananas  \n  ]  \n") == {'key': ['apples', '', 'bananas']}

def test_full_example():
    config = '''
# this is a comment

extension-name: Sample Extension
description: <
  Long
  text value
  spanning multiple lines
  >
dependencies: [
  boilerplate
]
version: 0.0.1
    '''

    expected = {
        'extension-name': 'Sample Extension',
        'description': "Long\ntext value\nspanning multiple lines",
        'dependencies': ['boilerplate'],
        'version': '0.0.1'
    }

    assert parse(config) == expected
