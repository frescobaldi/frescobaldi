# test dataset for simpler handling of JSON request during testing phase

test_request = {
    'commands': [
        {
            'command': 'transpose',
            'args': 'c d'
        },
        { 'command': 'reformat' },
        {
            'command': 'highlight',
            'variables': { 'full-html': 'false' }
        },
        { 'command': 'musicxml' },
        { 'command': 'mode' },
        { 'command': 'version' }
    ],
    'options': {
        'encoding': 'UTF-16',
        'language': "deutsch"
    },
    'data': "%No JSON data supplied. This is a test request.\n" +
            "\\relative c' {\nc4 ( d e )\n}"
}
