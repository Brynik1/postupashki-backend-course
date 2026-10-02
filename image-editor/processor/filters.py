"""Фильтры изображения для ImageProcessor"""

import io

from PIL import Image, ImageFilter, ImageOps


def negative(image: Image.Image, parameters: dict) -> Image.Image:
    return ImageOps.invert(image.convert("RGB"))


def flip_x(image: Image.Image, parameters: dict) -> Image.Image:
    return image.transpose(Image.FLIP_TOP_BOTTOM)


def blur(image: Image.Image, parameters: dict) -> Image.Image:
    radius = float(parameters.get("radius", 2.0))
    return image.filter(ImageFilter.GaussianBlur(radius))


def sharpen(image: Image.Image, parameters: dict) -> Image.Image:
    percent = int(parameters.get("percent", 150))
    return image.filter(ImageFilter.UnsharpMask(percent=percent))


FILTERS = {
    "Negative": negative,
    "FlipX": flip_x,
    "Blur": blur,
    "Sharpen": sharpen,
}


def apply(name: str, image_bytes: bytes, parameters: dict | None = None) -> bytes:
    """Применяет фильтр; возвращает png-байты"""
    handler = FILTERS.get(name)
    if handler is None:
        raise ValueError(f"unknown filter: {name}")
    image = Image.open(io.BytesIO(image_bytes))
    processed = handler(image, parameters or {})
    buf = io.BytesIO()
    processed.save(buf, format="PNG")
    return buf.getvalue()
