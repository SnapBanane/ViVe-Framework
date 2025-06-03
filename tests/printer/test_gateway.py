import os
from vive.printer.gateway import print_pdf, get_default_printer

if __name__ == "__main__":
    sample_pdf = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tests", "printer", "sample.pdf"))
    printer = get_default_printer()
    print(f"Using printer: {printer}")
    print_pdf(sample_pdf)
