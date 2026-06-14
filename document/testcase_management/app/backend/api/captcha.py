"""
验证码API
"""
from fastapi import APIRouter
from utils.captcha import generate_captcha

router = APIRouter()


@router.get("")
def get_captcha():
    captcha_id, image_base64, _ = generate_captcha()
    return {
        "code": 200,
        "message": "success",
        "data": {
            "captcha_id": captcha_id,
            "image": f"data:image/png;base64,{image_base64}"
        }
    }
