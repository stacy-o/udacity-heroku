#!/usr/bin/env python3
#
# A *bookmark server* or URI shortener that maintains a mapping (dictionary)
# between short names and long URIs, checking that each new URI added to the
# mapping actually works (i.e. returns a 200 OK).
#
# This server is intended to serve three kinds of requests:
#
#   * A GET request to the / (root) path.  The server returns a form allowing
#     the user to submit a new name/URI pairing.  The form also includes a
#     listing of all the known pairings.
#   * A POST request containing "longuri" and "shortname" fields.  The server
#     checks that the URI is valid (by requesting it), and if so, stores the
#     mapping from shortname to longuri in its dictionary.  The server then
#     redirects back to the root path.
#   * A GET request whose path contains a short name.  The server looks up
#     that short name in its dictionary and redirects to the corresponding
#     long URI.
#
# Your job in this exercise is to finish the server code.
#
# Here are the steps you need to complete:
#
# 1. Write the CheckURI function, which takes a URI and returns True if a
#    request to that URI returns a 200 OK, and False otherwise.
#
# 2. Write the code inside do_GET that sends a 303 redirect to a known name.
#
# 3. Write the code inside do_POST that sends a 400 error if the form fields
#    are missing.
#
# 4. Write the code inside do_POST that sends a 303 redirect to the form
#    after saving a newly submitted URI.
#
# 5. Write the code inside do_POST that sends a 404 error if a URI is not
#    successfully checked (i.e. if CheckURI returns false).
#
# In each step, you'll need to delete a line of code that raises the
# NotImplementedError exception.  These are there as placeholders in the
# starter code.
#
# After writing each step, restart the server and run test.py to test it.

import http.server
import requests
from urllib.parse import unquote, parse_qs

memory = {}

form = '''<!DOCTYPE html>
<title>Bookmark Server</title>
<form method="POST">
    <label>Long URI:
        <input name="longuri">
    </label>
    <br>
    <label>Short name:
        <input name="shortname">
    </label>
    <br>
    <button type="submit">Save it!</button>
</form>
<p>URIs I know about:
<pre>
{}
</pre>
'''

error_page = '''<!DOCTYPE html>
<title>Bookmark Error</title>
<form action="/" method="GET">
    <label>
    {}
    </label>
    <br>
    <br>
    <button type="submit">Return to Bookmark Server</button>
</form>
'''


def CheckURI(uri, timeout=5):
    '''Check whether this URI is reachable, i.e. does it return a 200 OK?

    This function returns True if a GET request to uri returns a 200 OK, and
    False if that GET request returns any other response, or doesn't return
    (i.e. times out).
    '''
    valid = False
    try:
      destination_response = requests.get(uri, timeout=timeout)
      valid = (200 == destination_response.status_code)
    except Exception as e:
      print(e)
      valid = False
    return valid


class Shortener(http.server.BaseHTTPRequestHandler):
    c_type = {'Content-type': 'text/html; charset=utf-8'}

    def my_response(self, my_code, my_header, my_content=''):
      self.send_response(my_code)
      for key in my_header.keys():
          self.send_header(key, my_header[key])
          print("Setting header: "+key+ "=" + my_header[key])
      self.end_headers()
      if my_content:
          self.wfile.write(my_content.encode())

    def do_GET(self):
        # A GET request will either be for / (the root path) or for /some-name.
        # Strip off the / and we have either empty string or a name.
        name = unquote(self.path[1:])

        if name:
            if name in memory:
                # 2. Send a 303 redirect to the long URI in memory[name].
                self.my_response(my_code=303, my_header={'Location': memory[name]})
            else:
                # We don't know that name! Send a 404 error.
                msg = "There is no bookmark '{}'.".format(name)
                self.my_response(404, self.c_type, error_page.format(msg))
        else:
            # Root path.
            # List the known associations in the form.
            known = "\n".join("{} : {}".format(key, memory[key])
                              for key in sorted(memory.keys()))
            # Send the form.
            self.my_response(200, self.c_type, form.format(known))

    def do_POST(self):
        # Decode the form data.
        length = int(self.headers.get('Content-length', 0))
        body = self.rfile.read(length).decode()
        params = parse_qs(body)

        # Check that the user submitted the form fields.
        if "longuri" not in params or "shortname" not in params:
            # 3. Serve a 400 error with a useful message.
            msg = "Values in both fields are needed to successfully add a bookmark"
            self.my_response(400, self.c_type, error_page.format(msg))

        longuri = params["longuri"][0]
        shortname = params["shortname"][0]

        if CheckURI(longuri):
            # This URI is good!  Remember it under the specified name.
            memory[shortname] = longuri

            # 4. Serve a redirect to the root page (the form).
            self.my_response(303, {'Location': '/'})
        else:
            # Didn't successfully fetch the long URI.

            # 5. Send a 404 error with a useful message.
            msg = "Provided long URL ('{}')is not working therefore can't save it as '{}'.".format(longuri, shortname)
            self.my_response(404, self.c_type, error_page.format(msg))

if __name__ == '__main__':
    server_address = ('', 8000)
    httpd = http.server.HTTPServer(server_address, Shortener)
    httpd.serve_forever()
