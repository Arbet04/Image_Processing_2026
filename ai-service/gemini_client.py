"""
Gemini Client — ตัวกลางของ chatbot
====================================
หน้าที่: รับข้อความจาก user แล้วให้ Gemini ตัดสินใจเองว่า
  - ถ้าเป็นคำถามทั่วไป → ตอบเป็นข้อความ
  - ถ้าเป็นคำขอสร้างรูป (เช่น "อยากได้รูปหมาสีดำ") → เรียก generate_image()
    ที่ไปสั่ง Forge Neo อีกที (ผ่าน forge_client.py เดิม)

ใช้เทคนิคที่เรียกว่า "Function Calling" — เราบอก Gemini ว่ามีเครื่องมือ
ชื่อ generate_image ใช้ทำอะไรได้ แล้ว Gemini จะตัดสินใจเองว่าเมื่อไหร่ควรเรียก
ไม่ต้องเขียน if-else เช็คคำในข้อความเอง
"""

import asyncio
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL
from queue_manager import enqueue_generate
from forge_client import ForgeConnectionError, ForgeGenerationError
from models import GenerateRequest

_client = genai.Client(api_key=GEMINI_API_KEY)

# ประกาศเครื่องมือให้ Gemini รู้จัก — คำอธิบาย (description) สำคัญมาก
# เพราะ Gemini ใช้ตรงนี้ตัดสินใจว่าจะเรียกใช้เมื่อไหร่
GENERATE_IMAGE_TOOL = {
    "name": "generate_image",
    "description": (
        "สร้างรูปภาพจากคำอธิบาย ใช้ฟังก์ชันนี้เมื่อ user ขอให้วาดรูป สร้างรูป "
        "หรือขอเห็นภาพอะไรบางอย่าง (เช่น 'อยากได้รูปหมาสีดำ', 'วาดรูปทะเลให้หน่อย')"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": (
                    "คำอธิบายรูปเป็นภาษาอังกฤษ แปลความหมายจากสิ่งที่ user ขอ "
                    "เพิ่มรายละเอียดสั้นๆ ให้ AI วาดรูปเข้าใจง่าย "
                    "เช่น 'a black dog, high quality, detailed photo'"
                ),
            },
        },
        "required": ["prompt"],
    },
}

_chat_config = types.GenerateContentConfig(
    tools=[types.Tool(function_declarations=[GENERATE_IMAGE_TOOL])]
)

# เก็บ session การคุยไว้ใน memory ง่ายๆ ก่อน (คนละคน คนละบทสนทนา)
# ข้อจำกัด: ถ้า restart service ประวัติจะหายหมด — ทำ Queue/DB ทีหลังค่อยแก้จุดนี้
_chat_sessions: dict[str, any] = {}


def _get_or_create_chat(session_id: str):
    if session_id not in _chat_sessions:
        _chat_sessions[session_id] = _client.chats.create(
            model=GEMINI_MODEL,
            config=_chat_config,
        )
    return _chat_sessions[session_id]


async def handle_chat_message(session_id: str, message: str) -> dict:
    """
    จุดเริ่มต้นหลัก — รับข้อความ user คืนค่าเป็น dict {text, image_base64}
    """
    chat = _get_or_create_chat(session_id)

    # google-genai SDK เป็น sync ล้วน ถ้าเรียกตรงๆ ใน FastAPI (async) จะบล็อก
    # event loop ทั้งหมด เลยต้องรันใน thread แยกด้วย asyncio.to_thread
    response = await asyncio.to_thread(chat.send_message, message)

    part = response.candidates[0].content.parts[0]

    # กรณีที่ 1: Gemini ตัดสินใจว่าต้องเรียกฟังก์ชันสร้างรูป
    if part.function_call and part.function_call.name == "generate_image":
        image_prompt = part.function_call.args.get("prompt", message)

        try:
            forge_req = GenerateRequest(prompt=image_prompt)
            image_result = await enqueue_generate(forge_req)

        except (ForgeConnectionError, ForgeGenerationError) as e:
            # สร้างรูปไม่สำเร็จ — บอก Gemini ให้ช่วยตอบ user อย่างสุภาพแทนที่จะโยน error ดิบๆ
            follow_up = await asyncio.to_thread(
                chat.send_message,
                f"[ระบบแจ้ง] สร้างรูปไม่สำเร็จ เพราะ: {str(e)} "
                "ช่วยตอบ user สั้นๆ อย่างสุภาพว่าตอนนี้สร้างรูปไม่ได้",
            )
            return {"text": follow_up.text, "image_base64": None}

        # สร้างรูปสำเร็จ — แจ้ง Gemini เพื่อให้สรุปคำตอบเป็นข้อความธรรมชาติ
        follow_up = await asyncio.to_thread(
            chat.send_message,
            "[ระบบแจ้ง] สร้างรูปสำเร็จแล้ว ช่วยตอบ user สั้นๆ ว่าทำเสร็จแล้ว",
        )

        return {
            "text": follow_up.text,
            "image_base64": image_result["image_base64"],
        }

    # กรณีที่ 2: คำถามทั่วไป ไม่เกี่ยวกับการสร้างรูป — ตอบข้อความปกติ
    return {"text": response.text, "image_base64": None}
