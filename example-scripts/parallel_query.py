# -*- coding: utf-8 -*-
"""
Created on Tue Dec  12 11:41:11 2023

@author: alankar

Usage: mpiexec -n <num_procs> python parallel_query.py
"""

# Import AstroPlasma Ionization module
from astro_plasma import Ionization
import numpy as np
from mpi4py import MPI

## start parallel programming ---------------------------------------- #
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

comm.Barrier()
t_start = MPI.Wtime()

## ionization fraction function from Astroplasma --------------------- #
fIon = Ionization.interpolate_ion_frac

nH = 8.0e-03  # Hydrogen number density in cm^-3
temperature = np.logspace(4.0, 6.2, 100)  # Temperature of the plasma in kelvin
metallicity = 0.3  # Metallicity of plasma with respect to solar
redshift = 0.2  # Cosmological redshift
frac_local = np.zeros_like(temperature)

temperature_this_proc = temperature[rank : temperature.shape[0] : size]
frac_local[rank : temperature.shape[0] : size] = np.power(
    10.0,
    fIon(
        nH=nH,
        temperature=temperature_this_proc,
        metallicity=metallicity,
        redshift=redshift,
        element="OVI",
        mode="PIE",
    ),  # This value is in log10
)
comm.Barrier()

frac = np.zeros_like(temperature)
# use MPI to get the totals
comm.Reduce([frac_local, MPI.DOUBLE], [frac, MPI.DOUBLE], op=MPI.SUM, root=0)

comm.Barrier()
t_diff = MPI.Wtime() - t_start
if comm.rank == 0:
    print(frac)
    print("Elasped: ", t_diff)
