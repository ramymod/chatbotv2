import os
import json
import logging
from typing import Dict, Any

import google.generativeai as genai
import config

logger = logging.getLogger(__name__)

genai.configure(api_key=config.API_KEY)

chat_model = genai.GenerativeModel(
    'gemini-2.5-flash',
    system_instruction=config.SYSTEM_PROMPT
)

profiler_model = genai.GenerativeModel('gemini-2.5-flash')

class GeminiBrain:
    def __init__(self) -> None:
        """Initializes the GeminiBrain, ensuring the history file exists."""
        if not os.path.exists(config.HISTORY_FILE):
            logger.info(f"Creating new history file at {config.HISTORY_FILE}")
            with open(config.HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump({}, f)

    def load_data(self) -> Dict[str, Any]:
        """Loads user data from the local JSON history file."""
        try:
            with open(config.HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading data from {config.HISTORY_FILE}: {e}")
            return {}

    def save_data(self, data: Dict[str, Any]) -> None:
        """Saves user data back to the local JSON history file."""
        try:
            with open(config.HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving data to {config.HISTORY_FILE}: {e}")

    def update_child_profile(self, current_profile: str, user_text: str, bot_text: str) -> str:
        """
        وظيفة هذا الجزء: استخراج الحقائق فقط (العمر، الحالة، المشكلة) وتجاهل باقي الكلام.
        """
        prompt = f"""
        أنت مسؤول عن تحديث "ملف حالة الطفل".
        لديك البيانات السابقة، ومعلومات جديدة من المحادثة الحالية.
        
        المهمة: قم بدمج المعلومات الجديدة لتحديث ملف الطفل.
        
        البيانات السابقة: {current_profile}
        كلام الأب/الأم الجديد: {user_text}
        نصيحة الخبير (أنت): {bot_text}
        
        القواعد الصارمة للحفظ:
        1. استخرج اسم الطفل وعمره إن وجدوا.
        2. صف حالة الطفل السلوكية بدقة (عنيد، ذكي، كثير الحركة، إلخ).
        3. لخص المشكلة الحالية في جملة واحدة.
        4. لا تكتب المحادثة حرفياً، اكتب فقط الحقائق المستنتجة عن الطفل.
        
        اكتب التقرير المحدث باللغة العربية:
        """
        try:
            response = profiler_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Failed to update child profile, falling back to current profile: {e}")
            return current_profile

    def ask_gemini(self, user_id: str, message: str) -> str:
        """Processes a chat message from a user and returns Gemini's response."""
        data = self.load_data()
        child_profile = data.get(user_id, "")
        
        if not child_profile:
            child_profile = "لا توجد معلومات سابقة عن الطفل. هذه أول محادثة."

        history_for_model = [
            {"role": "user", "parts": [f"ملف بيانات الطفل الحالية: {child_profile}"]},
            {"role": "model", "parts": ["فهمت الحالة. سأبني نصيحتي بناءً على هذا الملف."]}
        ]

        try:
            # 3. بدء المحادثة
            chat = chat_model.start_chat(history=history_for_model)
            response = chat.send_message(message)
            bot_reply = response.text

            # Update profile silently without stopping the main reply
            new_profile = self.update_child_profile(child_profile, message, bot_reply)
            
            data[user_id] = new_profile
            self.save_data(data)
            
            return bot_reply
        except Exception as e:
            logger.error(f"Error communicating with Gemini model for user {user_id}: {e}", exc_info=True)
            raise RuntimeError("حدث خطأ أثناء معالجة طلبك") from e