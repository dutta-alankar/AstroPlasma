# -*- coding: utf-8 -*-
"""
Created on Mon Nov 28 14:47:02 2022

@author: alankar
"""

import time
import numpy as np
import os
from itertools import product
import sys
import h5py
from ProgressBar import ProgressBar as pbar

from mpi4py import MPI

## start parallel programming ---------------------------------------- #
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
startTime = time.time()

resume = False
start = 60
run_cloudy = True


def ionFrac(nH=1e-4, temperature=1e6, metallicity=1.0, redshift=0.0, indx=99999):
    command = (
        "./ionization_CIE "
        + f"{nH:.2e} "
        + f"{temperature:.2e} "
        + f"{metallicity:.2e} "
        + f"{redshift:.2f} {indx} "
        + f"> ./auto/auto_CIE_{indx:09}.out"
    )
    os.system(command)
    command = (
        "./ionization_PIE "
        + f"{nH:.2e} "
        + f"{temperature:.2e} "
        + f"{metallicity:.2e} "
        + f"{redshift:.2f} {indx} "
        + f"> ./auto/auto_PIE_{indx:09}.out"
    )
    os.system(command)
    os.system(f"rm -rf ./auto/auto_CIE_{indx:09}.out")
    os.system(f"rm -rf ./auto/auto_PIE_{indx:09}.out")
    return None


make_batch = True
total_size = [25, 25, 15, 5]
batch_dim = [8, 8, 4, 2]

nH = np.logspace(-6, 0, total_size[0])
temperature = np.logspace(3.8, 8, total_size[1])
metallicity = np.logspace(-1, 1, total_size[2])
redshift = np.linspace(0, 2, total_size[3])

batches = int(np.prod(total_size) // np.prod(batch_dim)) + (
    0 if (np.prod(total_size) % np.prod(batch_dim)) == 0 else 1
)

values = list(product(redshift, metallicity, temperature, nH))  # itertools are lazy
offsets = np.hstack(
    (
        np.arange(0, np.prod(total_size), np.prod(batch_dim)),
        [
            len(values),
        ],
    )
)
sys.stdout.flush()
comm.Barrier()

if rank == 0:
    print(f"Data size: {len(values)}", flush=True)
    print(f"Batch size: {int(np.prod(batch_dim))}", flush=True)
    print(f"Total batch count: {batches}", flush=True)
    # if (run_cloudy and make_batch):
    #     print('Don\'t run cloudy scripts and make batches simultaneously!')
    if run_cloudy:
        print("Running of cloudy scripts will be performed.", flush=True)
    if make_batch:
        print(
            "Collecting cloudy outputs to .hdf5 batch files will also be performed.",
            flush=True,
        )


if run_cloudy:
    if rank == 0 and not (resume):
        if os.path.exists("./auto"):
            os.system("rm -rf ./auto")
        os.system("mkdir -p ./auto")
    sys.stdout.flush()
    comm.Barrier()

    if resume and rank == 0:
        print("Resuming from stopped state ... ", flush=True)
    progbar = None
    if rank == 0:
        progbar = pbar()

    start = start - size
    if not (resume) or (start < 0):
        start = 0
    if rank == 0:
        progbar.progress(min(start + rank, len(values)), len(values))
    sys.stdout.flush()
    comm.Barrier()

    for indx in range(start + rank, len(values), size):
        this_val = values[indx]

        i, j, k, m = (
            np.where(nH == this_val[-1])[0][0],
            np.where(temperature == this_val[-2])[0][0],
            np.where(metallicity == this_val[-3])[0][0],
            np.where(redshift == this_val[-4])[0][0],
        )
        counter = (
            (m) * metallicity.shape[0] * temperature.shape[0] * nH.shape[0]
            + (k) * temperature.shape[0] * nH.shape[0]
            + (j) * nH.shape[0]
            + (i)
        )
        # if (resume and (counter<=start)):
        #     if rank==0: progbar.progress(min(indx+size, len(values)), len(values))
        #     continue
        # else:
        ionFrac(*this_val[::-1], counter)
        sys.stdout.flush()
        if rank == 0:
            progbar.progress(min(indx + size, len(values)), len(values))
        sys.stdout.flush()

    if rank == 0:
        progbar.end()
    sys.stdout.flush()
    comm.Barrier()

progbar = None
if rank == 0:
    print("Collecting into .hdf5 batch files ... ", flush=True)
    progbar = pbar()
sys.stdout.flush()

N_max = 30  # element Zinc
if rank <= batches - 1 and make_batch:
    for batch_id in range(rank, batches, size):
        this_batch_size = offsets[batch_id + 1] - offsets[batch_id]
        fracCIE = np.zeros((this_batch_size, int(N_max * (N_max + 3) / 2)))
        fracPIE = np.zeros_like(fracCIE)
        count = 0
        for this_val in values:
            i, j, k, m = (
                np.where(nH == this_val[-1])[0][0],
                np.where(temperature == this_val[-2])[0][0],
                np.where(metallicity == this_val[-3])[0][0],
                np.where(redshift == this_val[-4])[0][0],
            )
            counter = (
                (m) * metallicity.shape[0] * temperature.shape[0] * nH.shape[0]
                + (k) * temperature.shape[0] * nH.shape[0]
                + (j) * nH.shape[0]
                + (i)
            )
            in_this_batch = (
                counter >= offsets[batch_id] and counter < offsets[batch_id + 1]
            )
            if not (in_this_batch):
                continue
            fracCIE[count, :] = np.loadtxt(
                "./auto/ionization_CIE_%09d.txt" % counter, dtype=np.float32
            )
            fracPIE[count, :] = np.loadtxt(
                "./auto/ionization_PIE_%09d.txt" % counter, dtype=np.float32
            )
            count += 1

        # np.save('ionization.npy', data, allow_pickle=True)
        loc = "."
        if not (os.path.exists("%s/data" % loc)):
            os.system("mkdir -p %s/data" % loc)
        with h5py.File("%s/data/ionization.b_%06d.h5" % (loc, batch_id), "w") as hdf:
            hdf.create_dataset("params/nH", data=nH)
            hdf.create_dataset("params/temperature", data=temperature)
            hdf.create_dataset("params/metallicity", data=metallicity)
            hdf.create_dataset("params/redshift", data=redshift)
            hdf.create_dataset("output/fracIon/CIE", data=fracCIE)
            hdf.create_dataset("output/fracIon/PIE", data=fracPIE)
            hdf.create_dataset("header/batch_id", data=batch_id)
            hdf.create_dataset("header/batch_dim", data=batch_dim)
            hdf.create_dataset("header/total_size", data=total_size)

        if rank == 0:
            progbar.progress(min(batch_id + size, batches), batches)
        sys.stdout.flush()
comm.Barrier()
if rank == 0:
    progbar.end()
sys.stdout.flush()
stopTime = time.time()
comm.Barrier()

if rank == 0:
    print("Elapsed: %.2f s" % (stopTime - startTime), flush=True)
    sys.stdout.flush()

comm.Disconnect()
MPI.Finalize()
# sys.exit(0)
