"""Asset geométrico original, determinístico e offline; não usa imagem anterior."""

from pathlib import Path
from PIL import Image, ImageDraw

if __name__ == "__main__":
    image = Image.new("RGB", (640, 360), "#14233D")
    draw = ImageDraw.Draw(image)
    for x in range(0, 641, 40):
        draw.line((x, 0, x, 360), fill="#203555")
    for y in range(0, 361, 40):
        draw.line((0, y, 640, y), fill="#203555")
    draw.rounded_rectangle((60, 70, 380, 285), radius=28, fill="#2563EB")
    draw.ellipse((275, 40, 525, 290), fill="#FBBF24")
    draw.rounded_rectangle((420, 210, 580, 320), radius=18, fill="#F6F8FC")
    target = Path("assets/imagem_demo.png")
    target.parent.mkdir(exist_ok=True)
    image.save(target)
