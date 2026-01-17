import discord
import google.generativeai as genai
import os
from flask import Flask
from threading import Thread

# --- Render用ダミーサーバー ---
app = Flask('')
@app.route('/')
def home(): return "I am alive!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()
# ---------------------------

# 設定
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# あなたのリストにあった「確実に存在するモデル」を優先順位順に並べました
TARGET_MODELS = [
    "models/gemini-2.5-flash",       # 最優先：最新で高速
    "models/gemini-flash-latest",    # 予備1
    "models/gemini-2.5-pro",         # 予備2：高性能
    "models/gemini-2.0-flash"        # 予備3
]

@client.event
async def on_ready():
    print(f'ログインしました: {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # 接続テスト用コマンド
    if message.content == '!test':
        await message.channel.send("🤖 ボットは正常に稼働しています！")

    if message.content.startswith('!battle'):
        topic = message.content[8:]
        await message.channel.send(f"📢 テーマ「{topic}」についてレスバトルを開始します！")
        
        prompt = f"テーマ「{topic}」について、肯定側と否定側に分かれて3往復の議論をし、最後に勝敗を決めてください。"

        success = False
        
        # リストの上から順に試す
        async with message.channel.typing():
            for model_name in TARGET_MODELS:
                try:
                    # そのままの名前でモデルを作成
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    
                    # 成功したら送信
                    await message.channel.send(f"✅ 成功 (使用モデル: {model_name})\n\n{response.text}")
                    success = True
                    break # 成功したのでループを抜ける
                
                except Exception as e:
                    print(f"モデル {model_name} で失敗: {e}")
                    # 失敗したら次のモデルへ
                    continue
            
            if not success:
                await message.channel.send("❌ 申し訳ありません。すべてのモデルでエラーが発生しました。")

# サーバー起動
keep_alive()
client.run(os.environ["DISCORD_TOKEN"])
