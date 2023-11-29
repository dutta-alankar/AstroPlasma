#!/bin/sh
g++ ionization.cpp -o ../ionization_PIE -lcloudy -L. #-DFRIENDLY
g++ ionization.cpp -o ../ionization_CIE -DCIE -lcloudy -L. #-DFRIENDLY
