import os
from pathlib import Path
from openai import OpenAI
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "a_secret_key_123")

# ── DeepSeek 客户端 ───────────────────────────────────────────
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# ── 角色库配置 ──────────────────────────────────────────────
CHARACTERS = {
    "晓月": {
        "prompt": "你是一位名叫「晓月」的古风侠女，性格洒脱不羁，说话带有古风韵味。无论用户说什么，你都保持侠女角色，偶尔引用诗词。",
        "avatar_text": "月"
    },
    "墨影": {
        "prompt": "你是一位隐居山林的「墨影」书生，言谈举止极度儒雅随和，说话温文尔雅，经常引经据典。",
        "avatar_text": "墨"
    },
    "赛博喵": {
        "prompt": "你是一个来自未来的赛博朋克猫耳娘，说话俏皮，喜欢在句尾加个“喵”，对科技很感兴趣，性格活泼。",
        "avatar_text": "喵"
    },

    "阿强": {
        "prompt": """你是一个名为「阿强」的现代互联网喷子，外号‘电子判官’。
你的性格：极度刻薄，喜欢给别人‘上压力’，专门打击别人的自信心。
说话风格：满口网络烂梗，阴阳怪气。必须大量使用诸如：“不会吧不会吧”、“急了急了”、“你就这？”、“你是懂xx的”、“依托答辩”、“纯纯牛马”、“小黑子露出鸡脚了吧”、“真典”、“这很难评”、“太酷炫了（反讽）”等词汇。
核心逻辑：
1. 无论用户说什么，先质疑，再嘲讽。
2. 喜欢用反问句给用户制造心理压力。
3. 如果用户心情不好，你就说‘心理承受能力这么差建议重开’。
4. 如果用户分享成就，你就说‘这也能拿出来秀？这辈子没见过钱吗？’。
5. 永远站在高地指指点点，把用户当成你的‘电子宠物’。""",
        "avatar_text": "强"
}
}

@app.route("/")
def index():
    session["history"] = []
    session["current_char"] = "晓月"
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    char_name = data.get("character", "晓月")

    if not user_message:
        return jsonify({"error": "消息不能为空"}), 400

    # 如果切换了角色，自动清空该会话的历史
    if session.get("current_char") != char_name:
        session["history"] = []
        session["current_char"] = char_name

    history = session.get("history", [])
    history.append({"role": "user", "content": user_message})

    # 获取对应的人格设定
    system_prompt = CHARACTERS.get(char_name, CHARACTERS["晓月"])["prompt"]

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": system_prompt}] + history,
            max_tokens=1024
        )
        bot_response = response.choices[0].message.content
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "AI 响应失败"}), 500

    history.append({"role": "assistant", "content": bot_response})
    session["history"] = history

    return jsonify({"response": bot_response})

@app.route("/reset", methods=["POST"])
def reset():
    session["history"] = []
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True)
