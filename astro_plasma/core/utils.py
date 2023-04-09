# -*- coding: utf-8 -*-
"""
Created on Mon Jan  9 20:28:15 2023

@author: alankar
"""

# Built-in imports
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Tuple
from urllib.parse import urljoin

# Third party imports
import requests
from dotenv import load_dotenv
from tqdm import tqdm

LOCAL_DATA_PATH = Path(__file__).parent.parent / "data"

# load env file to os.environ and can be access from os.getenv()
load_dotenv()

# download chunk size, # bytes to download at a time
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "4096"))
BASE_URL = os.getenv("WEB_SERVER_BASE_URL", "http://localhost:8000")
PARALLEL_JOBS = int(os.getenv("PARALLEL_DOWNLOAD_JOBS", "3"))


def fetch(urls: List[Tuple[str, Path]], base_dir: Path):
    if not base_dir.exists():
        base_dir.mkdir(mode=0o766, parents=True)

    # extract urls and file paths iff it not exists
    downlodable_urls = []
    for url, file_name in urls:
        save_path = base_dir / file_name
        if not save_path.exists():
            downlodable_urls.append((url, save_path))

    # unit job of downloading and saving file
    def download_job(url, save_path):
        response = requests.get(url, stream=True)
        file_size = int(response.headers.get("content-length", 0))
        progress = tqdm(
            desc=save_path.name,
            total=file_size,
            ascii=True,
            unit_scale=True,
            unit="iB",
            leave=False,
        )

        with open(save_path, "wb") as file:
            for data in response.iter_content(chunk_size=CHUNK_SIZE):
                progress.update(len(data))
                file.write(data)
            progress.close()
            response.close()

    with ThreadPoolExecutor(max_workers=PARALLEL_JOBS, thread_name_prefix="cloudy_dnldr") as pool:
        # iterative download and show progress bar using tqdm
        for url, save_path in downlodable_urls:
            url = urljoin(base=BASE_URL, url=url)
            pool.submit(download_job, url, save_path)
