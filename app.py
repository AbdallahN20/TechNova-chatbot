import json
from flask import Flask, render_template, request, jsonify
from difflib import get_close_matches

app = Flask(__name__)

# متغير عالمي لحفظ سياق الحديث (الذاكرة)
# في المشاريع الكبيرة بنستخدم Database أو Session، بس هنا ده كافي جداً
user_context = {}


def load_knowledge_base():
    with open('knowledge.json', 'r', encoding='utf-8') as file:
        return json.load(file)


knowledge_base = load_knowledge_base()


def get_bot_response(user_input):
    global user_context
    user_input = user_input.lower()

    # 1. تحديث الذاكرة (Context)
    if "موبايل" in user_input or "تطبيق" in user_input:
        user_context['topic'] = 'mobile'
    elif "ويب" in user_input or "موقع" in user_input:
        user_context['topic'] = 'web'
    elif "تصميم" in user_input or "ui" in user_input:
        user_context['topic'] = 'ui'

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

    # ========================================================
    # 3. الذكاء السياقي (Context Intelligence) - التعديل هنا
    # ========================================================

    current_topic = user_context.get('topic')

    # A. معالجة سؤال "الصور/النماذج" بناءً على السياق
    if found_intent and found_intent["tag"] == "general_work":
        if current_topic == 'mobile':
            return {"text": "بما إننا بنتكلم عن الموبايل، دي نماذج شغلنا:", "image": "/static/images/mobile.png"}
        elif current_topic == 'web':
            return {"text": "دي أحدث المواقع اللي صممناها:", "image": "/static/images/web.png"}
        elif current_topic == 'ui':
            return {"text": "دي تصميمات الـ UI/UX:", "image": "/static/images/ui.png"}

    # B. معالجة سؤال "الأسعار" بناءً على السياق (الجديد 🔥)
    if found_intent and found_intent["tag"] == "general_price":
        if current_topic == 'mobile':
            # نجيب نص السعر من قسم mobile_prices
            mobile_intent = next((i for i in knowledge_base["intents"] if i["tag"] == "mobile_prices"), None)
            return {"text": mobile_intent["responses"][0], "image": None}

        elif current_topic == 'web':
            # نجيب نص السعر من قسم web_prices
            web_intent = next((i for i in knowledge_base["intents"] if i["tag"] == "web_prices"), None)
            return {"text": web_intent["responses"][0], "image": None}

        elif current_topic == 'ui':
            # نجيب نص السعر من قسم ui_prices
            ui_intent = next((i for i in knowledge_base["intents"] if i["tag"] == "ui_prices"), None)
            return {"text": ui_intent["responses"][0], "image": None}

    # 4. الرد الطبيعي
    if found_intent:
        import random
        return {"text": random.choice(found_intent["responses"]), "image": found_intent["image"]}

    else:
        return {
            "text": "عذراً، لم أفهم بدقة. 🤔\nممكن توضح؟ (مثلاً: 'أسعار الموبايل'، 'نماذج الويب').",
            "image": None
        }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/get_response", methods=["POST"])
def chat():
    msg = request.form["msg"]
    return jsonify(get_bot_response(msg))


if __name__ == "__main__":
    app.run(debug=True)