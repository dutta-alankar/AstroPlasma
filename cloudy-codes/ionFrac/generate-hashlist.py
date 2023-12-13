# -*- coding: utf-8 -*-
"""
Created on Wed Dec  13 10:14:15 2023

@author: alankar
"""
import hashlib
import os
from pathlib import Path
from typing import Union


# Taken from: https://stackoverflow.com/questions/16874598/how-do-i-calculate-the-md5-checksum-of-a-file-in-python
def blake2bsum(filename: Union[str, Path]) -> str:
    chunk_size = 8192
    with open(filename, "rb") as f:
        file_hash = hashlib.blake2b()
        while chunk := f.read(chunk_size):
            file_hash.update(chunk)
    return file_hash.hexdigest()


if __name__ == "__main__":
    hashlist = []
    root_path = Path("./data")
    all_files = os.listdir(root_path)
    all_files = sorted(all_files)
    # print(all_files)
    for this_file in all_files:
        if os.path.isfile(root_path / Path(this_file)) and str(this_file).endswith(".h5"):
            print(this_file, end="\r")
            hashlist.append(blake2bsum(root_path / Path(this_file)))
    with open(root_path / Path("hashlist.txt"), "w") as hashfile:
        for indx, hashval in enumerate(hashlist):
            hashfile.write(hashval + "\n" if indx < (len(hashlist) - 1) else "")
