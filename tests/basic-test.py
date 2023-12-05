# -*- coding: utf-8 -*-
"""
Created on Tue Dec  5 18:27:11 2023

@author: alankar
"""

def test_import():
    try:
        import astro_plasma
    except:
        raise AssertionError
