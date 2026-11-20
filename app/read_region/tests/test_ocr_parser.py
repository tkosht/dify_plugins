import pytest

from service.core import Failure
from service.ocr import parse_tsv

HEADER = "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"


@pytest.mark.parametrize(
    "data",
    [
        "温度 -12.5 mm\n",
        "",
        HEADER + "5\t1\t1\t1\t1\t1\t0\t0\t10\t10\tnan\ttext\n",
        HEADER + "5\t1\t1\t1\t1\t1\t0\t0\t10\t10\t99\n",
    ],
)
def test_malformed_tsv_never_becomes_no_text(tmp_path, data):
    p = tmp_path / "ocr.tsv"
    p.write_text(data)
    with pytest.raises(Failure, match="OCR_FAILED"):
        parse_tsv(p)


def test_detected_unreadable_word_is_preserved(tmp_path):
    p = tmp_path / "ocr.tsv"
    p.write_text(HEADER + "5\t1\t1\t1\t1\t1\t0\t0\t10\t10\t-1\t\n")
    assert parse_tsv(p)[0]["text"] == ""
    assert parse_tsv(p)[0]["confidence"] is None
