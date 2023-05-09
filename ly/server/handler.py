# This file is part of python-ly, https://pypi.python.org/pypi/python-ly
#
# Copyright (c) 2014 - 2015 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.

"""
HTTP request handler
"""

from __future__ import unicode_literals
try:
    from BaseHTTPServer import BaseHTTPRequestHandler
except ImportError:
    from http.server import BaseHTTPRequestHandler

import json
import copy

# Prototype (in JavaScript sense) from which each command copies its options
default_opts = None

class RequestHandler(BaseHTTPRequestHandler):
    
    def create_command(self, cmd):
        """
        Parse one command from the JSON data, plus optionally some commands to
        set variables. Returns an array with command._command instances.
        Raises exceptions upon faulty data.
        """
        from . import command
        
        result = []
        
        # set variables before executing the command
        if 'variables' in cmd:
            for v in cmd['variables']:
                result.append(command.set_variable(
                    v + "=" + cmd['variables'][v]))
        
        # instantiate the command.
        if not 'command' in cmd:
            raise ValueError("Malformed JSON data in request body (missing 'command' field).\n" +
                            "Object:\n" + json.dumps(cmd))
        cmd_name = cmd['command'].replace('-', '_')
        if not cmd_name in command.known_commands:
            raise ValueError("unknown command: " + cmd_name)
        
        # add arguments to command if present.
        args = cmd.get('args', '')
        args = [args] if args else []
        try:
            result.append(getattr(command, cmd_name)(*args))
        except TypeError as ae:
            raise ValueError("Error creating command {cmd} with args {args}.\n{msg}".format(
                            cmd = cmd_name,
                            args = ", ".join(args),
                            msg = str(ae)))
        return result
        

    def process_options(self, opts):
        """
        Instantiate a copy of the default options and
        update with the given opts
        """
        result = copy.deepcopy(default_opts)
        for opt in opts:
            # handle special case where option name doesn't match CL interface
            if opt == 'language':
                result.set_variable('default-language', opts[opt])
            else:
                result.set_variable(opt, opts[opt])
        return result
        
        
    def process_json_request(self, request):
        """
        Configure the action(s) to be taken, based on the JSON object.
        Raise errors when the JSON object can't be properly understood.
        Run the commands and return a string (from cursor.text() ).
        """

        # set up an Options object and
        # override defaults with given options
        opts = self.process_options(request.get('options', []))
        
        # set up commands
        commands = []
        for c in request['commands']:
            commands.extend(self.create_command(c))        
        
        # create document from passed data
        import ly.document
        doc = ly.document.Document(request['data'], opts.mode)
        doc.filename = ""

        # data structure for the results
        data = {
            'doc': {
                'commands': [],
                'content': ly.document.Cursor(doc)
            },
            'info': [],
            'exports': []
        }
        
        # run commands, which modify data in-place
        for c in commands:
            c.run(opts, data)
        
        data['doc']['content'] = data['doc']['content'].text()
        return data

        
    def read_json_request(self):
        """
        Returns the message body parsed to a dictionary
        from JSON data. Raises 
        - RuntimeWarning when no JSON data is present
        - ValueError when JSON parsing fails
        """
        
        content_len = int(self.headers['content-length'])
        if content_len == 0:
            #TODO: When testing is over remove (or comment out)
            # the following two lines and raise the exception instead.
            from . import testjson
            return testjson.test_request
            raise RuntimeWarning("No JSON data in request body")
        
        req_body = self.rfile.read(content_len)
        # Python2 has string, Python3 has bytestream
        if not isinstance(req_body, str):
            req_body = req_body.decode('utf-8')

        # parse body, initial validation
        try:
            request = json.loads(req_body)
        except Exception as e:
            raise ValueError("Malformed JSON data in request body:\n" + str(e))
        if not 'commands' in request:
            raise ValueError("Malformed JSON request. Missing 'commands' property")
        if not 'data' in request:
            raise ValueError("Malformed JSON request. Missing 'data' property")
        return request


    
    ########################
    ### Request handlers ###
    ########################

    def do_POST(self):
        """
        A POST request is expected to contain the task to be executed 
        as a JSON object in the request body.
        The POST handler (currently) ignores the URL.
        """
        try:
            request = self.read_json_request()
            result = self.process_json_request(request)
        except Exception as e:
            # TODO: should we disambiguate (ValueError, RuntimeWarning, others)?
            # use HTML templates
            self.send_error(400, format(e))
            return
        
        # Send successful response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        res_body = json.dumps(result)
        if isinstance(res_body, str):
            res_body = res_body.encode()
        self.wfile.write(res_body)
