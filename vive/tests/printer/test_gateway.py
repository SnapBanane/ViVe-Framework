import os
import vive.modules.printer.gateway as silent_pdf_printer

# Get absolute path to the sample.pdf in the current directory
pdf_path = os.path.join(os.path.dirname(__file__), "sample.pdf")

# Optional: list available printers
printers = silent_pdf_printer.get_printers()
print("Available printers:", printers)

# Call print function (default printer)
success = silent_pdf_printer.print_pdf(pdf_path)

# Print result
print("Print successful:" if success else "Print failed.")