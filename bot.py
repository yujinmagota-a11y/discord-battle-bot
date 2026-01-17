import discord
import google.generativeai as genai
import os
from flask import Flask
from threading import Thread
import traceback

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

@client.event
async def on_ready():
    print(f'ログインしました: {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # ★デバッグ用コマンド：使えるモデルを全部表示する
    if message.content == '!models':
        try:
            m_list = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    m_list.append(m.name)
            await message.channel.send(f"📋 使用可能なモデル一覧:\n" + "\n".join(m_list))
        except Exception as e:
            await message.channel.send(f"モデル一覧の取得に失敗: {e}")

    if message.content.startswith('!battle'):
        topic = message.content[8:]
        
        # 試すモデルの順番（上から順に使えそうなやつを探す）
        candidate_models = [
            "gemini-2.5-flash", # 最新（もしあれば）
            "gemini-1.5-flash", # 定番
            "gemini-1.5-pro",
            "gemini-pro",       # 旧安定版
            "models/gemini-1.5-flash",
            "models/gemini-pro"
        ]
        
        # 自動検索で見つかったモデルがあれば先頭に追加
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    candidate_models.insert(0, m.name)
                    break 
        except:
            pass

        # 重複を削除
        candidate_models = list(dict.fromkeys(candidate_models))

        await message.channel.send(f"📢 テーマ「{topic}」についてレスバトルを開始します！")
        
        prompt = f"テーマ「{topic}」について、肯定側と否定側に分かれて3往復の議論をし、最後に勝敗を決めてください。"

        # ★ エラーが出たら次のモデルで再挑戦するロジック
        success = False
        last_error = ""

        async with message.channel.typing():
            for model_name in candidate_models:
                try:
                    # モデル名をきれいにする（models/ があるとエラーになる場合があるので調整）
                    clean_name = model_name.replace("models/", "") if "/" in model_name else model_name
                    
                    # 生成トライ
                    model = genai.GenerativeModel(clean_name)
                    response = model.generate_content(prompt)
                    
                    # 成功したら送信してループを抜ける
                    await message.channel.send(f"✅ 成功 (モデル: {clean_name})\n\n{response.text}")
                    success = True
                    break
                
                except Exception as e:
                    # 失敗したら次へ
                    last_error = str(e)
                    print(f"モデル {model_name} で失敗: {e}")
                    continue
            
            if not success:
                await message.channel.send(f"❌ すべてのモデルで失敗しました。\n最後のエラー: {last_error}\n\n`!models` と入力して、使えるモデルがあるか確認してください。")

keep_alive()
client.run(os.environ["DISCORD_TOKEN"])
