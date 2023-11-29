# -*- coding: utf-8 -*-
"""
Created on Tue Nov 22 11:34:06 2022

@author: alankar
"""
import time
import numpy as np
import os
from itertools import product
import matplotlib.pyplot as plt
import sys
import h5py
from ProgressBar import ProgressBar as pbar

from mpi4py import MPI

## initialize parallel programming environment --------- #
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
startTime = time.time()

run_cloudy = False
make_batch = True
resume = False
start = 60
if not (run_cloudy):
    resume = True

flag = 0


def emmisivity(nH=1e-4, temperature=1e6, metallicity=1.0, redshift=0.0, indx=None, mode="PIE"):
    plotIt = False
    global flag

    # print(f'Inside emm br: {rank} {indx} {mode}', flush=True)

    if (mode != "CIE") and (mode != "PIE"):
        if rank == 0:
            print("Problem!", flush=True)
        comm.Disconnect()
        sys.exit(1)

    pc = 3.0856775807e18
    kpc = 1e3 * pc

    background = f"\ntable HM12 redshift {redshift:.2f}" if mode == "PIE" else ""
    tmp_filename = "emission_%s_%09d.lin" % (mode, 1000000 + rank) if indx is None else "emission_%s_%09d.lin" % (mode, indx)
    stream = f"""
# ----------- Auto generated from generateCloudyScript.py -----------------
#Created on {time.ctime()}
#
#@author: alankar
#
CMB redshift {redshift:.2f}{background}
sphere
radius 150 to 151 linear kiloparsec
##table ISM
abundances "solar_GASS10.abn"
metals {metallicity:.2e} linear
hden {np.log10(nH):.2f} log
constant temperature, T={temperature:.2e} K linear
stop zone 1
iterate convergence
age 1e9 years
##save continuum "spectra.lin" units keV no isotropic
save diffuse continuum "{tmp_filename}" units keV
    """
    stream = stream[1:]

    if rank == 0 and flag == 0:
        if not (os.path.exists("./auto")):
            os.system("mkdir -p ./auto")
        if not (os.path.isfile("./auto/cloudy.exe")):
            os.system("cp ./cloudy.exe ./auto")
        if not (os.path.isfile("./auto/libcloudy.so")):
            os.system("cp ./libcloudy.so ./auto")

    if flag == 0:
        comm.Barrier()
        flag = 1
    if indx is not None:
        filename = "autoGenScript_%s_%09d.in" % (mode, indx)
    else:
        filename = "autoGenScript_%s_%09d.in" % (mode, 1000000 + rank)

    with open("./auto/%s" % filename, "w") as text_file:
        text_file.write(stream)

    # process = subprocess.check_call(["./cloudy.exe",
    #                                  "-r %s"%filename[:-3]],
    #                                  shell=True, cwd='./auto/')
    # process.wait()

    # pid = os.fork()
    # if pid:
    #    status = os.wait()
    # else:
    #    os.system("cd ./auto && ./cloudy.exe -r %s"%filename[:-3])

    os.system("cd ./auto && ./cloudy.exe -r %s" % filename[:-3])
    # if (indx!=None):
    #    if(indx>=60): print(f'Inside emm ar: {rank} {indx} {mode}', flush=True)

    data = np.loadtxt("./auto/emission_%s_%09d.lin" % (mode, 1000000 + rank) if indx is None else "./auto/emission_%s_%09d.lin" % (mode, indx))
    if indx is None:
        os.system("rm -rf ./auto/emission_%s_%09d.lin" % (mode, 1000000 + rank))
        os.system("rm -rf ./auto/%s" % filename)
    os.system("rm -rf ./auto/%s.out" % filename[:-3])

    if plotIt:
        delV = 4 * np.pi * (150 * kpc) ** 2 * (151 - 150) * kpc
        fig = plt.figure(figsize=(13, 10))
        ax = plt.gca()
        plt.loglog(data[:, 0], data[:, -1] / data[:, 0] * delV / (4 * np.pi))
        ax.grid()
        ax.tick_params(
            axis="both",
            which="major",
            labelsize=24,
            direction="out",
            pad=5,
            labelcolor="black",
        )
        ax.tick_params(
            axis="both",
            which="minor",
            labelsize=24,
            direction="out",
            pad=5,
            labelcolor="black",
        )
        ax.set_ylabel(r"erg/s/keV/sr", size=28, color="black")
        ax.set_xlabel(r"E (keV)", size=28, color="black")
        ax.set_xlim(xmin=5e-3, xmax=2e1)
        ax.set_ylim(ymin=1e29, ymax=1e44)
        # lgnd = ax.legend(loc='lower left',
        #                  framealpha=0.3, prop={'size': 20},
        #                  title_fontsize=24),
        #                  bbox_to_anchor=(0.88, 0))
        # lgnd.set_title(r'$\rm R_{cl}$')
        fig.tight_layout()
        # plt.savefig('./plots-res-rho.png', transparent=True, bbox_inches='tight')
        plt.show()
        plt.close(fig)
    # if (data.ndim<2): print(data, flush=True)
    return np.vstack((data[:, 0], data[:, -1])).T


if rank == 0 and not (resume):
    if os.path.exists("./auto"):
        os.system("rm -rf ./auto")
comm.Barrier()

total_size = [25, 25, 15, 5]

nH = np.logspace(-6, 0, total_size[0])
temperature = np.logspace(3.8, 8, total_size[1])
metallicity = np.logspace(-1, 1, total_size[2])
redshift = np.linspace(0, 2, total_size[3])

batch_dim = [8, 8, 4, 2]
batches = int(np.prod(total_size) // np.prod(batch_dim)) + (0 if (np.prod(total_size) % np.prod(batch_dim)) == 0 else 1)

values = list(product(redshift, metallicity, temperature, nH))  # itertools are lazy
sample = emmisivity(indx=None)
energy = sample[:, 0]
till = np.where(energy == energy[0])[0][1]
energy = energy[:till]

offsets = np.hstack(
    (
        np.arange(0, np.prod(total_size), np.prod(batch_dim)),
        [
            len(values),
        ],
    )
)
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


if rank == 0 and not (resume):
    os.system("rm -rf ./auto")
if resume and rank == 0:
    print("Resuming from stopped state ... ", flush=True)
if not (run_cloudy) and rank == 0:
    print("Not running cloudy. Assuming all text data already generated!", flush=True)

# print("Before cloudy run", rank, flush=True)

progbar = None
if rank == 0:
    progbar = pbar()

start = start - size
# extra = (len(values)-start)%size
# start = start - extra
if not (resume) or (start < 0):
    start = 0
if rank == 0:
    progbar.progress(min(start + rank, len(values)), len(values))

comm.Barrier()

if run_cloudy:
    if rank == 0:
        if not (os.path.exists("./auto")):
            os.system("mkdir -p ./auto")
        if not (os.path.isfile("./auto/cloudy.exe")):
            os.system("cp ./cloudy.exe ./auto")
        if not (os.path.isfile("./auto/libcloudy.so")):
            os.system("cp ./libcloudy.so ./auto")
    comm.Barrier()
    for indx in range(start + rank, len(values), size):
        this_val = values[indx]

        i, j, k, m = (
            np.where(nH == this_val[-1])[0][0],
            np.where(temperature == this_val[-2])[0][0],
            np.where(metallicity == this_val[-3])[0][0],
            np.where(redshift == this_val[-4])[0][0],
        )
        counter = (m) * metallicity.shape[0] * temperature.shape[0] * nH.shape[0] + (k) * temperature.shape[0] * nH.shape[0] + (j) * nH.shape[0] + (i)

        # if (counter>=len(values)):
        #     print(f'Rank {rank}: Problem: index {counter} overflow!', flush=True)
        #     comm.Disconnect()
        #     MPI.Finalize()
        #     sys.exit(1)
        # print("Before run", rank, counter, flush=True)
        # if (resume and (counter<start)):
        #     #if rank==0: progbar.progress(min(indx+size, len(values)), len(values))
        #     continue
        # else:
        # print(f"before emm call {rank} {counter}", flush=True)
        # if(rank==0): print(f'{i} {j} {k} {l} {indx}')
        spectrum = emmisivity(*this_val[::-1], counter, "CIE")
        spectrum = emmisivity(*this_val[::-1], counter, "PIE")
        # print(f"after emm call {rank} {counter}", flush=True)
        # if (counter+rank >= len(values)):
        #     dummy = emmisivity(*this_val[::-1], None, 'CIE')
        #     dummy = emmisivity(*this_val[::-1], None, 'PIE')
        # print("After run", rank, counter, flush=True)
        if rank == 0:
            progbar.progress(min(indx + size, len(values)), len(values))
        # print(f"for block {rank} {counter}", flush=True)

    if rank == 0:
        progbar.end()
    comm.Barrier()

"""
randNum = np.zeros(1)
if (rank!=0):
    status = MPI.Status()
    comm.Send(randNum, dest=0, tag=rank)
    comm.Recv(randNum, source=0, tag=MPI.ANY_TAG, status=status)
else:
    recv_count = 0
    while(recv_count<(size-1)):
        #print('Received ',recv_count, flush=True)
        status = MPI.Status()
        comm.Recv(randNum, source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
        comm.Send(randNum, dest=status.Get_source(), tag=status.Get_source())
        recv_count += 1
#print('Waiting ', rank, flush=True)
"""

comm.Barrier()
if rank <= batches - 1 and make_batch:
    progbar = None
    if rank == 0:
        print("Collecting into .hdf5 batch files ... ", flush=True)
        progbar = pbar()

    for batch_id in range(rank, batches, size):
        this_batch_size = offsets[batch_id + 1] - offsets[batch_id]
        tot_emm_CIE = np.zeros((this_batch_size, energy.shape[0]))
        cont_emm_CIE = np.zeros_like(tot_emm_CIE)
        tot_emm_PIE = np.zeros((this_batch_size, energy.shape[0]))
        cont_emm_PIE = np.zeros_like(tot_emm_PIE)
        count = 0
        for this_val in values:
            i, j, k, m = (
                np.where(nH == this_val[-1])[0][0],
                np.where(temperature == this_val[-2])[0][0],
                np.where(metallicity == this_val[-3])[0][0],
                np.where(redshift == this_val[-4])[0][0],
            )
            counter = (m) * metallicity.shape[0] * temperature.shape[0] * nH.shape[0] + (k) * temperature.shape[0] * nH.shape[0] + (j) * nH.shape[0] + (i)
            if counter >= len(values):
                print(f"Rank {rank}: Problem: index {counter} overflow!", flush=True)
                # comm.Disconnect()
                # MPI.Finalize()
                # sys.exit(1)
            in_this_batch = counter >= offsets[batch_id] and counter < offsets[batch_id + 1]
            if not (in_this_batch):
                continue
            spectrum_CIE = np.loadtxt("./auto/emission_CIE_%09d.lin" % counter, dtype=np.float32)
            while spectrum_CIE.ndim < 2:
                try:
                    spectrum_CIE = np.loadtxt("./auto/emission_PIE_%09d.lin" % counter, dtype=np.float32)
                except (OSError, ValueError):
                    print("Retry", flush=True)
                    time.sleep(2)
            tot_emm_CIE[count, :] = spectrum_CIE[:, -1][:till]
            cont_emm_CIE[count, :] = spectrum_CIE[:, 1][:till]

            spectrum_PIE = np.loadtxt("./auto/emission_PIE_%09d.lin" % counter, dtype=np.float32)
            while spectrum_PIE.ndim < 2:
                try:
                    spectrum_PIE = np.loadtxt("./auto/emission_PIE_%09d.lin" % counter, dtype=np.float32)
                except (OSError, ValueError):
                    print("Retry", flush=True)
                    time.sleep(2)
            tot_emm_PIE[count, :] = spectrum_PIE[:, -1][:till]
            cont_emm_PIE[count, :] = spectrum_PIE[:, 1][:till]

            count += 1

        # np.save('emission.npy', data, allow_pickle=True)
        loc = "."
        if not (os.path.exists("%s/data" % loc)):
            os.system("mkdir -p %s/data" % loc)
        with h5py.File("%s/data/emission.b_%06d.h5" % (loc, batch_id), "w") as hdf:
            hdf.create_dataset("params/nH", data=nH)
            hdf.create_dataset("params/temperature", data=temperature)
            hdf.create_dataset("params/metallicity", data=metallicity)
            hdf.create_dataset("params/redshift", data=redshift)
            hdf.create_dataset("output/emission/CIE/continuum", data=cont_emm_CIE)
            hdf.create_dataset("output/emission/CIE/total", data=tot_emm_CIE)
            hdf.create_dataset("output/emission/PIE/continuum", data=cont_emm_PIE)
            hdf.create_dataset("output/emission/PIE/total", data=tot_emm_PIE)
            hdf.create_dataset("output/energy", data=energy)
            hdf.create_dataset("header/batch_id", data=batch_id)
            hdf.create_dataset("header/batch_dim", data=batch_dim)
            hdf.create_dataset("header/total_size", data=total_size)

        if rank == 0:
            progbar.progress(min(batch_id + size, batches), batches)

    if rank == 0:
        progbar.end()

comm.Barrier()
stopTime = time.time()
if rank == 0:
    print("Elapsed: %.2f s" % (stopTime - startTime), flush=True)

comm.Disconnect()
MPI.Finalize()
# sys.exit(0)
