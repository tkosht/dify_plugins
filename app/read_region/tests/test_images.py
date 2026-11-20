import io
from dataclasses import replace

import pytest
from PIL import Image

from vision_core.images import ImageFailure, Limits, box_from_parameters, view


def original():
    image = Image.new("RGB", (2048, 1536))
    image.putdata(
        [
            ((x % 251), (y % 253), ((x + y) % 247))
            for y in range(1536)
            for x in range(2048)
        ]
    )
    data = io.BytesIO()
    image.save(data, format="PNG")
    return image, data.getvalue()


def test_full_image_source_pixels_are_unchanged():
    source, data = original()
    output, meta = view(data, box_from_parameters({}))
    with Image.open(io.BytesIO(output)) as result:
        assert (
            result.size == (2048, 1536)
            and result.tobytes() == source.tobytes()
        )
    assert meta["resized"] is False and meta["crop_pixels"] == [
        0,
        0,
        2048,
        1536,
    ]


def test_native_400_by_300_region_is_exact_original_roi():
    source, data = original()
    output, meta = view(data, [0.125, 0.125, 0.3203125, 0.3203125])
    with Image.open(io.BytesIO(output)) as result:
        assert result.size == (400, 300)
        assert result.tobytes() == source.crop((256, 192, 656, 492)).tobytes()
    assert meta["crop_pixels"] == [256, 192, 656, 492]


@pytest.mark.parametrize(
    "value", [True, "0.5", None, float("nan"), float("inf"), -0.1, 1.1]
)
def test_invalid_coordinate_is_rejected(value):
    with pytest.raises(ImageFailure):
        box_from_parameters(
            {"x_min": value, "y_min": 0, "x_max": 1, "y_max": 1}
        )


def test_output_cap_and_malformed_input():
    with pytest.raises(ImageFailure, match="INVALID_IMAGE"):
        view(b"invalid", [0, 0, 1, 1])
    source, data = original()
    with pytest.raises(ImageFailure, match="OUTPUT_LIMIT_EXCEEDED"):
        view(data, [0, 0, 1, 1], replace(Limits(), output_bytes=32))
