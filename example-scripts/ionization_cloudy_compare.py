# -*- coding: utf-8 -*-
"""
Created on Thu Apr  6 17:55:34 2023

@author: alankar

Usage: mpiexec -n <num_procs> python ionization_cloudy_compare.py
"""

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import time
from scipy import interpolate
from astro_plasma import Ionization

_parallel = True

if _parallel:
    from mpi4py import MPI

    ## start parallel programming ---------------------------------------- #
    t_start = MPI.Wtime()
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    comm.Barrier()
else:
    t_start = time.time()
    rank = 0
    size = 1

element = 8

fIon = Ionization.interpolate_ion_frac
Temp = np.logspace(4.2, 7.2, 500)

f_Oxygen = np.zeros((Temp.shape[0], element + 1))

if _parallel:
    f_Oxygen_local = np.zeros_like(f_Oxygen)
    Temp_this_proc = Temp[rank : Temp.shape[0] : size]
    f_Oxygen_local[slice(rank, Temp.shape[0], size), :] = np.power(
        10.0,
        fIon(
            temperature=Temp_this_proc,
            metallicity=0.99,
            redshift=0.001,
            element=element,
            mode="CIE",
        ),
    )
    comm.Barrier()
else:
    f_Oxygen[:, :] = np.power(
        10.0,
        fIon(
            temperature=Temp,
            metallicity=0.99,
            redshift=0.001,
            element=element,
            mode="CIE",
        ),
    )
if _parallel:
    # use MPI to get the totals
    f_Oxygen = f_Oxygen.flatten()
    comm.Reduce([f_Oxygen_local.flatten(), MPI.DOUBLE], [f_Oxygen, MPI.DOUBLE], op=MPI.SUM, root=0)
    f_Oxygen = f_Oxygen.reshape((Temp.shape[0], element + 1))
    comm.Barrier()

## Plot Styling
matplotlib.rcParams["xtick.direction"] = "in"
matplotlib.rcParams["ytick.direction"] = "in"
matplotlib.rcParams["xtick.top"] = True
matplotlib.rcParams["ytick.right"] = True
matplotlib.rcParams["xtick.minor.visible"] = True
matplotlib.rcParams["ytick.minor.visible"] = True
matplotlib.rcParams["axes.grid"] = True
matplotlib.rcParams["lines.dash_capstyle"] = "round"
matplotlib.rcParams["lines.solid_capstyle"] = "round"
matplotlib.rcParams["legend.handletextpad"] = 0.4
matplotlib.rcParams["axes.linewidth"] = 0.8
matplotlib.rcParams["lines.linewidth"] = 3.0
matplotlib.rcParams["ytick.major.width"] = 0.6
matplotlib.rcParams["xtick.major.width"] = 0.6
matplotlib.rcParams["ytick.minor.width"] = 0.45
matplotlib.rcParams["xtick.minor.width"] = 0.45
matplotlib.rcParams["ytick.major.size"] = 4.0
matplotlib.rcParams["xtick.major.size"] = 4.0
matplotlib.rcParams["ytick.minor.size"] = 2.0
matplotlib.rcParams["xtick.minor.size"] = 2.0
matplotlib.rcParams["legend.handlelength"] = 2
matplotlib.rcParams["figure.dpi"] = 200
matplotlib.rcParams["axes.axisbelow"] = True

if rank == 0:
    # Cloudy data
    frac = np.loadtxt(
        "ion-frac-Oxygen.txt",
        skiprows=1,
        converters={i + 1: lambda x: -30 if x == b"--" else x for i in range(element + 1)},
    )

    ions = [r"$f_{OV}$", r"$f_{OVI}$", r"$f_{OVI}$", r"$f_{OVIII}$"]

    fig = plt.figure()
    ax = fig.add_subplot(111)

    for indx, ion in enumerate(range(5, 9)):
        p = plt.loglog(Temp, f_Oxygen[:, ion - 1], label=ions[indx], alpha=0.6)
        f_cloudy = interpolate.interp1d(frac[:, 0], frac[:, ion])  # temperature and ion fraction in log10
        plt.loglog(
            Temp,
            10.0 ** f_cloudy(np.log10(Temp)),
            linestyle="--",
            color=p[0].get_color(),
            linewidth=1.5,
        )

    plt.title("Broken: Cloudy provided vs Solid: Our interpolator")
    plt.ylabel(r"Ionization fraction")
    plt.xlabel("Temperature [K]")
    plt.legend(loc="upper left")
    ax.yaxis.set_ticks_position("both")
    ax.set_ylim(ymin=1e-10, ymax=1.3)
    ax.set_xlim(xmin=4e4)
    plt.savefig("ionization-test.png", transparent=True)
    if _parallel:
        t_stop = MPI.Wtime()
    else:
        t_stop = time.time()
    print("Elapsed: ", (t_stop - t_start))
    plt.show()
