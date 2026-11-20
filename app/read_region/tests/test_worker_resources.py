import io
import random
import time

from PIL import Image

from service.core import Limits
from service.ocr import run


def worker_without_native_ocr(*args):
    import service.ocr as ocr

    def save_input(image, work, *unused):
        image.save(work / "input.png", format="PNG")
        return []

    ocr.tesseract = save_input
    ocr.worker(*args)


def test_large_valid_noisy_png_not_rejected_by_worker_fsize(tmp_path):
    # 9.7 MiB, below the 15 MiB upload and 40M pixel limits. Native OCR is
    # excluded here: this regression isolates decode/crop/temp-file capacity.
    raw = random.Random(17).randbytes(1800 * 1800 * 3)
    image = Image.frombytes("RGB", (1800, 1800), raw)
    data = io.BytesIO()
    image.save(data, format="PNG")
    assert 8 * 1024**2 < len(data.getvalue()) < 15 * 1024**2
    result = run(
        "register",
        data.getvalue(),
        "image/png",
        [0, 0, 1, 1],
        1,
        Limits(),
        tmp_path,
        time.monotonic() + 15,
        target=worker_without_native_ocr,
    )
    assert result["geometry"]["source_size"] == {"width": 1800, "height": 1800}
