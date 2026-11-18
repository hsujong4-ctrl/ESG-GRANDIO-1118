"""重新產生 PWA 圖示（選用）。
用法：pip install pillow numpy && python tools/make_icons.py
輸出位置：static/icons/
"""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "static", "icons")
os.makedirs(OUT, exist_ok=True)

BLUE = (37, 99, 235, 255)
WHITE = (255, 255, 255, 255)
LIGHT = (191, 219, 254, 255)


def draw_city(img, scale=1.0, offset=0.0):
    """畫簡單的城市剪影（代表資料與城市）"""
    d = ImageDraw.Draw(img)
    s = img.size[0]
    def p(x, y):
        return (offset + s * (0.5 + (x - 0.5) * scale), offset + s * (0.5 + (y - 0.5) * scale))
    buildings = [
        (0.18, 0.50, 0.32, 0.80, WHITE),
        (0.34, 0.34, 0.50, 0.80, WHITE),
        (0.52, 0.22, 0.66, 0.80, WHITE),
        (0.68, 0.44, 0.82, 0.80, WHITE),
    ]
    for x1, y1, x2, y2, c in buildings:
        d.rectangle([*p(x1, y1), *p(x2, y2)], fill=c)
    # 窗戶
    for x1, y1, x2, y2, _ in buildings:
        for ry in (y1 + 0.06, y1 + 0.16):
            for rx in (x1 + 0.03, x2 - 0.07):
                d.rectangle([*p(rx, ry), *p(rx + 0.04, ry + 0.05)], fill=BLUE)
    # 地面線
    d.rectangle([*p(0.12, 0.80), *p(0.88, 0.84)], fill=LIGHT)


def rounded_icon(size, path):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.22), fill=BLUE)
    draw_city(img, scale=0.9)
    img.save(path)


def maskable_icon(size, path):
    # 安全區為中央 80%，內容縮小以免被系統遮罩裁切
    img = Image.new("RGBA", (size, size), BLUE)
    draw_city(img, scale=0.7)
    img.save(path)


def svg_icon(path):
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="112" fill="#2563eb"/>
  <rect x="92" y="256" width="92" height="160" fill="#fff"/>
  <rect x="184" y="170" width="92" height="246" fill="#fff"/>
  <rect x="276" y="112" width="92" height="304" fill="#fff"/>
  <rect x="368" y="220" width="60" height="196" fill="#fff"/>
  <rect x="64" y="416" width="384" height="16" fill="#bfdbfe"/>
</svg>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)


if __name__ == "__main__":
    rounded_icon(192, os.path.join(OUT, "icon-192.png"))
    rounded_icon(512, os.path.join(OUT, "icon-512.png"))
    rounded_icon(180, os.path.join(OUT, "apple-touch-icon.png"))
    maskable_icon(512, os.path.join(OUT, "icon-maskable-512.png"))
    svg_icon(os.path.join(OUT, "icon.svg"))
    print("圖示已產生於", os.path.abspath(OUT))
