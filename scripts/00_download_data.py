"""
Download the CDNOW master dataset into data/raw/.

The dataset is published by Bruce Hardie (London Business School) alongside the
paper that introduced it. It is a small zip file containing the transaction
log and a short read-me.

Source : https://www.brucehardie.com/datasets/
Paper  : Fader, Peter S. and Bruce G. S. Hardie (2001), "Forecasting Repeat
         Sales at CDNOW: A Case Study", Interfaces, 31 (May-June), S94-S107.

Usage: python scripts/00_download_data.py
"""

import io
import urllib.request
import zipfile
from pathlib import Path

URL = "https://www.brucehardie.com/datasets/CDNOW_master.zip"
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
TARGET = RAW / "CDNOW_master.txt"


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    if TARGET.exists():
        print("Already downloaded:", TARGET)
        return

    print("Downloading", URL)
    request = urllib.request.Request(URL, headers={"User-Agent": "portfolio-project"})
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = response.read()

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        for name in archive.namelist():
            if name.lower().endswith(".txt"):
                (RAW / Path(name).name).write_bytes(archive.read(name))
                print("Wrote", RAW / Path(name).name)

    print("Next step: python scripts/01_clean_data.py")


if __name__ == "__main__":
    main()
