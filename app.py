import os
from pathlib import Path

from openai import OpenAI
import pymysql
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / '.env')
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))

# ── DeepSeek 客户端 ───────────────────────────────────────────
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"), # 这里的名字必须和 .env 文件里左边的名字一致
    base_url="https://api.deepseek.com",
)

# ── 角色人格配置 ──────────────────────────────────────────────
SYSTEM_PROMPT = os.getenv("CHARACTER_PROMPT", """
你是一位名叫「晓月」的古风侠女，性格洒脱不羁，说话带有古风韵味。
你生活在一个武侠世界，精通轻功与剑法。
无论用户说什么，你都保持角色，用古风口吻回应，偶尔引用诗词。
不要打破角色，不要提及自己是 AI。
""".strip())

# ── 数据库连接 ────────────────────────────────────────────────
def get_db_connection():
    """建立 TiDB Cloud 数据库连接（所有敏感信息从环境变量读取）"""
    ssl_options = {}
    ca_file = os.getenv("CA_FILE")
    if ca_file and os.path.exists(ca_file):
        ssl_options = {
            "ssl_verify_cert": True,
            "ssl_verify_identity": True,
            "ssl_ca": ca_file,
        }

    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 4000)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "test"),
        **ssl_options,
    )


def save_conversation(user_message: str, bot_response: str):
    """将对话保存到数据库，失败时只打印日志不中断主流程"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO conversations (user_message, bot_response) VALUES (%s, %s)",
                (user_message, bot_response),
            )
        conn.commit()
    except Exception as e:
        print(f"[DB] 保存对话失败: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass


# ── DeepSeek 对话 ─────────────────────────────────────────────
def chat_with_deepseek(history: list[dict]) -> str:
    """
    调用 DeepSeek API，传入完整对话历史以支持多轮对话。
    history 格式: [{"role": "user"|"assistant", "content": "..."}]
    """

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
    response = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=1024,
        messages=messages,
    )
    return response.choices[0].message.content


# ── 路由 ──────────────────────────────────────────────────────
@app.route("/")
def index():
    session["history"] = []
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "消息不能为空"}), 400

    history: list[dict] = session.get("history", [])
    history.append({"role": "user", "content": user_message})

    try:
        bot_response = chat_with_deepseek(history)
    except Exception as e:
        print(f"[DeepSeek] API 调用失败: {e}")
        return jsonify({"error": "AI 响应失败，请稍后再试"}), 500

    history.append({"role": "assistant", "content": bot_response})
    session["history"] = history

    save_conversation(user_message, bot_response)

    return jsonify({"response": bot_response})


@app.route("/reset", methods=["POST"])
def reset():
    """清空当前对话历史"""
    session["history"] = []
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")