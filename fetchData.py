#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  9 20:28:15 2023

@author: alankar
"""

import requests
import os
import sys

_verbose = False

def fetch(fileType='ionization', batch_id=0 , ip='localhost', port=8000):
    path = os.path.join(os.path.dirname(__file__), 'cloudy-data', 'ionization')
    os.system('mkdir -p %s'%path)
    path = os.path.join(os.path.dirname(__file__), 'cloudy-data', 'emission')
    os.system('mkdir -p %s'%path)
    filename='/%s/%s.b_%06d.h5'%(fileType,fileType,batch_id)
    
    if (os.path.exists(os.path.join(os.path.dirname(__file__), 'cloudy-data',filename[1:]))): 
        if(_verbose): print('File exists!')
        return
    # Set the server address and port
    server_address = f'http://{ip}:{port}'
    
    # Send a GET request to the server 
    response = requests.get(server_address + filename)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Save the file to disk
        filename = os.path.join(os.path.dirname(__file__), 'cloudy-data', filename[1:])
        if(_verbose): print('Saving file at: %s'%filename)
        with open(filename, 'wb') as file:
            file.write(response.content)
        if(_verbose): print('File saved to disk')
    else:
        print('Failed to fetch file')
        sys.exit(1)
