import os

import tempfile

import subprocess
from pdfplumber.display import PageImage


# image = page.to_image()
# show_image(image.reset().debug_tablefinder())
def show_image(img: PageImage):
    """show_image(page.to_image())."""
    file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    file.close()
    filename = file.name
    img.save(filename)
    subprocess.call(["open", filename])
    input("[press enter when done]")
    os.unlink(filename)
