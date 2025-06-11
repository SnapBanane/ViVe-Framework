import os
import platform
import shutil
import zipfile
import logging
import subprocess
import requests

# Windows-only import
if platform.system() == "Windows":
    import win32print

SUMATRA_URL = "https://www.sumatrapdfreader.org/dl/rel/3.5.2/SumatraPDF-3.5.2-64.zip"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SUMATRA_FOLDER = os.path.join(BASE_DIR, "sumatra")
SUMATRA_EXE = os.path.join(SUMATRA_FOLDER, "SumatraPDF-3.5.2-64.exe")

logging.basicConfig(level=logging.INFO)


def _download_sumatra():
    if os.path.exists(SUMATRA_EXE):
        return

    logging.info("Downloading SumatraPDF...")
    os.makedirs(SUMATRA_FOLDER, exist_ok=True)
    zip_path = os.path.join(SUMATRA_FOLDER, "SumatraPDF.zip")

    with requests.get(SUMATRA_URL, stream=True) as r:
        with open(zip_path, "wb") as f:
            shutil.copyfileobj(r.raw, f)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(SUMATRA_FOLDER)

    os.remove(zip_path)
    logging.info("SumatraPDF installed to %s", SUMATRA_FOLDER)


def get_printers():
    system = platform.system()
    if system == "Windows":
        return [printer[2] for printer in win32print.EnumPrinters(2)]
    elif system == "Darwin":  # macOS
        try:
            output = subprocess.check_output(["lpstat", "-p"]).decode()
            return [line.split()[1] for line in output.strip().split("\n") if line.startswith("printer")]
        except subprocess.CalledProcessError as e:
            logging.error("Failed to list printers: %s", e)
            return []
    else:
        raise NotImplementedError("get_printers is only implemented for Windows and macOS")


def print_pdf(filepath: str, printer_name: str = None) -> bool:
    if not os.path.exists(filepath):
        logging.error(f"File not found: {filepath}")
        return False

    if not filepath.lower().endswith(".pdf"):
        logging.error("Only PDF files are supported.")
        return False

    system = platform.system()

    if system == "Windows":
        _download_sumatra()
        cmd = [SUMATRA_EXE, "-silent"]
        if printer_name:
            cmd += ["-print-to", printer_name]
        else:
            cmd += ["-print-to-default"]
        cmd.append(filepath)
    elif system == "Darwin":
        cmd = ["lp"]
        if printer_name:
            cmd += ["-d", printer_name]
        cmd.append(filepath)
    else:
        raise NotImplementedError("PDF printing is only supported on Windows and macOS")

    try:
        subprocess.run(cmd, check=True)
        logging.info(f"Printed {filepath}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Print command failed: {e}")
        return False
