import os
import json
import google.generativeai as genai
import config

genai.configure(api_key=config.API_KEY)

chat_model = genai.GenerativeModel(
    'gemini-2.5-flash',
    system_instruction=config.SYSTEM_PROMPT
)

profiler_model = genai.GenerativeModel('gemini-2.5-flash')

class GeminiBrain:
    def __init__(self):
        if not os.path.exists(config.HISTORY_FILE):
            with open(config.HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump({}, f)

    def load_data(self):
        try:
            with open(config.HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {}

    def save_data(self, data):
        with open(config.HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def update_child_profile(self, current_profile, user_text, bot_text):
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
        except:
            return current_profile

    def ask_gemini(self, user_id, message):
        data = self.load_data()
        child_profile = data.get(user_id, "")
        
        if not child_profile:
            child_profile = "لا توجد معلومات سابقة عن الطفل. هذه أول محادثة."

       
        history_for_model = [
            {"role": "user", "parts": [f"ملف بيانات الطفل الحالية: {child_profile}"]},
            {"role": "model", "parts": ["فهمت الحالة. سأبني نصيحتي بناءً على هذا الملف."]}
        ]

        # 3. بدء المحادثة
        chat = chat_model.start_chat(history=history_for_model)
        response = chat.send_message(message)
        bot_reply = response.text

     
        new_profile = self.update_child_profile(child_profile, message, bot_reply)
        
        data[user_id] = new_profile
        self.save_data(data)
        
        return bot_reply