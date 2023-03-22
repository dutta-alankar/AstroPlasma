#!/bin/sh
g++ ionization.cpp -o ../ionization_PIE -lcloudy #-DFRIENDLY
g++ ionization.cpp -o ../ionization_CIE -DCIE -lcloudy #-DFRIENDLY
