#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  9 19:54:37 2023

@author: alankar
"""

import http.server
import os
import ssl

class MyHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        try:
            # Check if the file exists in the directory
            if os.path.exists(self.path[1:]):
                # Open the file in binary mode
                f = open(self.path[1:], 'rb')
                # Set the headers
                self.send_response(200)
                self.send_header('Content-type', 'application/octet-stream')
                self.end_headers()
                # Send the file content
                self.wfile.write(f.read())
                f.close()
            else:
                # Send a 404 error if the file does not exist
                self.send_error(404, 'File Not Found: %s' % self.path)
        except OSError:
            self.send_error(404, 'File Not Found: %s' % self.path)

def run():
    # Set the server address and port
    server_address = ('0.0.0.0', 4443)
    # Create the server
    httpd = http.server.HTTPServer(server_address, MyHTTPRequestHandler)
    # Load the SSL certificate and key
    httpd.socket = ssl.wrap_socket(httpd.socket, certfile='cert.pem', keyfile='key.pem', server_side=True)
    print('Starting server, use <Ctrl-C> to stop')
    # Run the server forever
    httpd.serve_forever()

run()