import os
import json
import requests
from flask import Flask, render_template, request, jsonify
from difflib import get_close_matches

app = Flask(__name__)

# ===========================
# إعدادات تيليجرام
# ===========================
TELEGRAM_TOKEN = "8526008564:AAH9kAQIzk53HPDTLxosuO2pcA-n2Ihzs_o"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/"
MY_WEBSITE_URL = "https://lime4k.pythonanywhere.com"  # رابط موقعك

# ===========================
# المنطق (Logic) والذاكرة
# ===========================
user_context = {}



def load_knowledge_base():
    # 1. بنجيب مسار المجلد اللي فيه ملف app.py الحالي
    base_path = os.path.dirname(os.path.abspath(__file__))

    # 2. بنلزق فيه اسم ملف الجيسون عشان يبقى مسار كامل
    file_path = os.path.join(base_path, 'knowledge.json')

    # 3. بنفتح الملف بالمسار الكامل
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

knowledge_base = load_knowledge_base()


def get_bot_response(user_input, user_id="web"):
    global user_context
    user_input = user_input.lower()

    # استخدام user_id عشان نفصل ذاكرة كل مستخدم عن التاني (مهم للتيليجرام)
    if user_id not in user_context:
        user_context[user_id] = {}

    # 1. تحديث الذاكرة
    if "موبايل" in user_input or "تطبيق" in user_input:
        user_context[user_id]['topic'] = 'mobile'
    elif "ويب" in user_input or "موقع" in user_input:
        user_context[user_id]['topic'] = 'web'
    elif "تصميم" in user_input or "ui" in user_input:
        user_context[user_id]['topic'] = 'ui'

    # 2. البحث عن الكلمات المفتاحية
    all_patterns = []
    for intent in knowledge_base["intents"]:
        all_patterns.extend(intent["patterns"])

    matches = get_close_matches(user_input, all_patterns, n=1, cutoff=0.6)

    found_intent = None
    if matches:
        best_match = matches[0]
        for intent in knowledge_base["intents"]:
            if best_match in intent["patterns"]:
                found_intent = intent
                break

    # 3. الذكاء السياقي
    current_topic = user_context[user_id].get('topic')

    # A. معالجة الصور
    if found_intent and found_intent["tag"] == "general_work":
        if current_topic == 'mobile':
            return {"text": "نماذج الموبايل:", "image": "/static/images/mobile.png"}
        elif current_topic == 'web':
            return {"text": "نماذج الويب:", "image": "/static/images/web.png"}
        elif current_topic == 'ui':
            return {"text": "تصميمات UI:", "image": "/static/images/ui.png"}

    # B. معالجة الأسعار
    if found_intent and found_intent["tag"] == "general_price":
        if current_topic == 'mobile':
            intent = next((i for i in knowledge_base["intents"] if i["tag"] == "mobile_prices"), None)
            return {"text": intent["responses"][0], "image": None}
        elif current_topic == 'web':
            intent = next((i for i in knowledge_base["intents"] if i["tag"] == "web_prices"), None)
            return {"text": intent["responses"][0], "image": None}

    # 4. الرد الطبيعي
    if found_intent:
        import random
        return {"text": random.choice(found_intent["responses"]), "image": found_intent["image"]}

    else:
        return {
            "text": "عذراً، لم أفهم. 🤔 ممكن توضح؟",
            "image": None
        }


# ===========================
# مسارات الموقع (Routes)
# ===========================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/get_response", methods=["POST"])
def chat():
    msg = request.form["msg"]
    return jsonify(get_bot_response(msg))


# ===========================
# بوابة تيليجرام (الجديدة) 🚀
# ===========================
@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    update = request.get_json()

    if "message" in update:
        chat_id = update["message"]["chat"]["id"]

        # التأكد إن الرسالة نصية
        if "text" in update["message"]:
            text = update["message"]["text"]

            # 1. هات الرد من البوت بتاعنا
            response = get_bot_response(text, str(chat_id))
            reply_text = response['text']
            reply_image = response['image']

            # 2. ابعت النص لتيليجرام
            requests.get(TELEGRAM_API_URL + f"sendMessage?chat_id={chat_id}&text={reply_text}")

            # 3. لو فيه صورة، ابعتها
            if reply_image:
                # لازم نحول المسار المحلي لرابط كامل عشان تيليجرام يشوفه
                full_image_url = MY_WEBSITE_URL + reply_image
                requests.get(TELEGRAM_API_URL + f"sendPhoto?chat_id={chat_id}&photo={full_image_url}")

    return "OK"


if __name__ == "__main__":
    app.run(debug=True)