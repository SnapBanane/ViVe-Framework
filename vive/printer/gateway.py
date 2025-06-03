import os
import subprocess
import logging
import shutil
import zipfile
import tempfile
import win32print  # type: ignore
import requests

# Setup colorful, structured logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("🖨️ PDFPrinter")

SUMATRA_ZIP_URL = "https://www.sumatrapdfreader.org/dl/rel/3.5.2/SumatraPDF-3.5.2-64.zip"
SUMATRA_FOLDER = os.path.join(os.path.dirname(__file__), "sumatrapdf")
SUMATRA_EXE = os.path.join(SUMATRA_FOLDER, "SumatraPDF.exe")


def ensure_sumatra() -> str:
    """Ensures SumatraPDF is downloaded and ready to use."""
    if os.path.isfile(SUMATRA_EXE):
        logger.debug(f"SumatraPDF already exists at: {SUMATRA_EXE}")
        return SUMATRA_EXE

    logger.info("📦 SumatraPDF not found – starting download...")
    os.makedirs(SUMATRA_FOLDER, exist_ok=True)

    zip_path = os.path.join(tempfile.gettempdir(), "sumatra_tmp.zip")

    logger.info(f"⬇️  Downloading from: {SUMATRA_ZIP_URL}")
    response = requests.get(SUMATRA_ZIP_URL, stream=True)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to download SumatraPDF: HTTP {response.status_code}")

    with open(zip_path, "wb") as f:
        shutil.copyfileobj(response.raw, f)

    logger.info(f"✅ Download complete. Saved to temp: {zip_path}")
    logger.info("📂 Extracting files...")

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(SUMATRA_FOLDER)

    os.remove(zip_path)
    logger.info(f"🧰 SumatraPDF extracted to: {SUMATRA_FOLDER}")
    return SUMATRA_EXE


def get_default_printer() -> str:
    """Returns the system's default printer name."""
    printer = win32print.GetDefaultPrinter()
    logger.info(f"🖨️  Default printer detected: {printer}")
    return printer


def print_pdf(pdf_path: str, printer: str = None):
    """Prints a PDF using SumatraPDF silently."""
    if not os.path.isfile(pdf_path):
        logger.error(f"🚫 PDF file not found: {pdf_path}")
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    sumatra_exe = ensure_sumatra()
    cmd = [sumatra_exe]

    if printer:
        cmd += ["-print-to", printer]
        logger.info(f"📠 Printing to specified printer: {printer}")
    else:
        cmd += ["-print-to-default"]
        logger.info("📠 Printing to default printer.")

    cmd.append(pdf_path)

    logger.debug(f"🛠️  Executing command: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        logger.info("✅ Print job sent successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Print job failed: {e}")
        raise
