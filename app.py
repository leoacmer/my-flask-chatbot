import os
from flask import Flask, render_template, request, jsonify
import pymysql # 用于连接 TiDB Cloud
from dotenv import load_dotenv

# 加载环境变量（本地开发时用，部署时 Render 会直接提供）
load_dotenv()

app = Flask(__name__)

# TiDB Cloud 数据库连接配置
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 4000))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "test") # 或者你的数据库名

# SSL CA 证书路径 (在 Render 上你需要上传这个文件或使用 Render 的方法处理)
# 本地调试时，如果 ca.pem 在项目根目录
CA_FILE = os.getenv("CA_FILE", "ca.pem") # 部署时可能需要调整路径或方式

def get_db_connection():
    """建立数据库连接"""
    try:
        # 注意：在 Render 部署时，ca.pem 文件的路径和可访问性需要特别处理
        # 常见做法是在 Render 的文件系统或环境变量中提供证书内容
        # 这里先假设 ca.pem 在可访问路径
        conn = pymysql.connect(
            host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
            port=4000,
            user="4JBLBZrFJSoLECC.root",
            password="H3jkklm1eYfkvqi9",
            database="test",
            ssl_verify_cert=True,
            ssl_verify_identity=True,
            ssl_ca='isrgrootx1.pem'
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise

# 简单的对话存储 (替换为实际的智能对话逻辑)
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    # 这里集成你的智能对话模型
    # 例如：response = call_your_llm_model(user_message)
    # 暂时用一个简单的回复
    bot_response = f"你说了: {user_message}"

    # 示例：将对话保存到 TiDB Cloud
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "INSERT INTO conversations (user_message, bot_response) VALUES (%s, %s)"
            cursor.execute(sql, (user_message, bot_response))
        conn.commit()
        conn.close()
        print("对话已保存到数据库")
    except Exception as e:
        print(f"保存对话到数据库失败: {e}")
        # 根据需要处理错误，例如返回错误信息给用户

    return jsonify({'response': bot_response})

if __name__ == '__main__':
    app.run(debug=True)
