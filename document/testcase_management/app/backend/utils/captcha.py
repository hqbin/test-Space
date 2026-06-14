"""
验证码工具模块
内存存储验证码，支持图片验证码生成和验证
"""
import io
import random
import string
import time
import threading
import base64
import hashlib
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont


captcha_store = {}
_lock = threading.Lock()

CAPTCHA_EXPIRE_SECONDS = 300
CAPTCHA_LENGTH = 4
CAPTCHA_WIDTH = 120
CAPTCHA_HEIGHT = 40

FONT_SIZES = [28, 30, 32]
COLORS = [
    (0, 0, 0),
    (128, 0, 0),
    (0, 128, 0),
    (0, 0, 128),
    (128, 128, 0),
]


def _generate_code(length: int = CAPTCHA_LENGTH) -> str:
    chars = string.ascii_uppercase + string.digits
    chars = chars.replace('O', '').replace('0', '').replace('I', '').replace('1', '').replace('L', '')
    return ''.join(random.choices(chars, k=length))


def _draw_noise(draw: ImageDraw.ImageDraw, width: int, height: int):
    for _ in range(random.randint(3, 6)):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        color = COLORS[random.randint(0, len(COLORS) - 1)]
        draw.line([(x1, y1), (x2, y2)], fill=color, width=1)

    for _ in range(random.randint(50, 80)):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        color = COLORS[random.randint(0, len(COLORS) - 1)]
        draw.point((x, y), fill=color)


def generate_captcha() -> Tuple[str, str, str]:
    code = _generate_code()
    img = Image.new('RGB', (CAPTCHA_WIDTH, CAPTCHA_HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", FONT_SIZES[0])
    except OSError:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_SIZES[0])
        except OSError:
            font = ImageFont.load_default()

    _draw_noise(draw, CAPTCHA_WIDTH, CAPTCHA_HEIGHT)

    for i, char in enumerate(code):
        x = 10 + i * 25
        y = random.randint(2, 8)
        color = COLORS[random.randint(0, len(COLORS) - 1)]
        draw.text((x, y), char, font=font, fill=color)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    captcha_id = hashlib.md5(f"{code}{time.time()}{random.random()}".encode()).hexdigest()

    with _lock:
        captcha_store[captcha_id] = {
            'code': code.upper(),
            'expire_at': time.time() + CAPTCHA_EXPIRE_SECONDS,
        }
        _cleanup_expired()

    return captcha_id, img_base64, code


def verify_captcha(captcha_id: str, user_input: str) -> bool:
    if not captcha_id or not user_input:
        return False

    with _lock:
        entry = captcha_store.get(captcha_id)
        if not entry:
            return False

        if time.time() > entry['expire_at']:
            del captcha_store[captcha_id]
            return False

        if entry['code'].upper() == user_input.upper():
            del captcha_store[captcha_id]
            return True

        return False


def _cleanup_expired():
    now = time.time()
    expired_keys = [
        k for k, v in captcha_store.items()
        if now > v['expire_at']
    ]
    for k in expired_keys:
        del captcha_store[k]
