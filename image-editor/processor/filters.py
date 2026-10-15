import io

from PIL import Image, ImageFilter


def negative(image: Image.Image, parameters: dict) -> Image.Image:
    # свой инверт попиксельно; инвертируются только RGB-каналы, альфа остается
    rgba = image.convert("RGBA")
    r, g, b, a = rgba.split()
    return Image.merge(
        "RGBA",
        (
            r.point(lambda v: 255 - v),
            g.point(lambda v: 255 - v),
            b.point(lambda v: 255 - v),
            a,
        ),
    )


def flip_x(image: Image.Image, parameters: dict) -> Image.Image:
    # свое отражение относительно оси X, попиксельно
    rgba = image.convert("RGBA")
    w, h = rgba.size
    src = rgba.load()
    flipped = Image.new("RGBA", (w, h))
    dst = flipped.load()
    for y in range(h):
        for x in range(w):
            dst[x, y] = src[x, h - 1 - y]
    return flipped


def blur(image: Image.Image, parameters: dict) -> Image.Image:
    radius = float((parameters or {}).get("radius", 2.0))
    return image.filter(ImageFilter.GaussianBlur(radius))


def sharpen(image: Image.Image, parameters: dict) -> Image.Image:
    percent = int((parameters or {}).get("percent", 150))
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
