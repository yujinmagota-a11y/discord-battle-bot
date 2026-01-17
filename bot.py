import discord
import google.generativeai as genai
import os
import asyncio
from flask import Flask
from threading import Thread

# --- 24時間稼働させるためのWebサーバー機能 ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Battle Bot is Alive"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# ----------------------------------

# 設定を読み込む（後でRender側で設定します）
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Geminiの設定
genai.configure(api_key=GEMINI_API_KEY)
# 高速で無料枠の多いモデルを使用
model = genai.GenerativeModel("gemini-pro")

# Discordの設定
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# ----------------------------------
#  レスバトル進行用システム
# ----------------------------------

async def run_battle(channel, topic):
    # 会話の履歴を保存しておくリスト
    history = []
    
    # 1. 審判：立場の振り分け
    await channel.send(f"📢 **これより、テーマ「{topic}」についてレスバトルを開始します！**")
    async with channel.typing():
        judge_prompt = f"""
        あなたはディベートの審判です。
        テーマ: 「{topic}」
        
        以下の役割を行ってください：
        1. このテーマについて対立する2つの強力な立場（AとB）を定義してください。
        2. 観客に向けて、それぞれの立場を簡潔に紹介し、バトルの開始を宣言してください。
        
        出力は日本語で行ってください。
        """
        try:
            response = model.generate_content(judge_prompt)
            judge_text = response.text
        except Exception as e:
            await channel.send(f"エラーが発生しました: {e}")
            return

        await channel.send(f"⚖️ **審判**: {judge_text}")
        history.append(f"審判の宣言: {judge_text}")
        await asyncio.sleep(2) 

    # バトルのターン数（往復回数）
    rounds = 2 

    for i in range(rounds):
        # --- 選手Aのターン ---
        async with channel.typing():
            prompt_a = f"""
            これまでの議論の流れ: {history}
            
            あなたの役割: 「{topic}」における【立場A（先行）】の論客。
            
            指示:
            1. 審判が定義した【立場A】を擁護してください。
            2. 相手（立場B）の発言があれば、論理的かつ攻撃的に反論してください。
            3. 200文字以内で鋭く主張してください。ですます調は使わず、断定的に話してください。
            """
            response_a = model.generate_content(prompt_a)
            text_a = response_a.text
            
            await channel.send(f"🔴 **選手A**: {text_a}")
            history.append(f"選手Aの主張: {text_a}")
            await asyncio.sleep(4)

        # --- 選手Bのターン ---
        async with channel.typing():
            prompt_b = f"""
            これまでの議論の流れ: {history}
            
            あなたの役割: 「{topic}」における【立場B（後攻）】の論客。
            
            指示:
            1. 審判が定義した【立場B】を擁護してください。
            2. 直前の【選手A】の発言の矛盾点を突き、痛烈に反論してください。
            3. 200文字以内でユーモアを交えて論破してください。ですます調は使わず、断定的に話してください。
            """
            response_b = model.generate_content(prompt_b)
            text_b = response_b.text
            
            await channel.send(f"🔵 **選手B**: {text_b}")
            history.append(f"選手Bの反論: {text_b}")
            await asyncio.sleep(4)

    # 3. 審判：判定
    async with channel.typing():
        judge_final_prompt = f"""
        これまでの議論の流れ: {history}
        
        あなたはディベートの審判です。
        議論を聞いた上で、以下の手順で締めくくってください。
        
        1. 両者の良かった点を短く評価する。
        2. 独断と偏見で「勝者」を決定し、その理由を述べる。
        3. 最後に「勝者：〇〇」と高らかに宣言する。
        """
        response_final = model.generate_content(judge_final_prompt)
        await channel.send(f"⚖️ **審判**: {response_final.text}")


# ----------------------------------
#  ボットの起動設定
# ----------------------------------

@client.event
async def on_ready():
    print(f'{client.user} としてログインしました！')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # 「!battle テーマ」というコマンドで開始
    if message.content.startswith('!battle '):
        topic = message.content.replace('!battle ', '').strip()
        if not topic:
            await message.channel.send("テーマを入力してください。（例: `!battle 犬 vs 猫`）")
            return
            
        await run_battle(message.channel, topic)

# サーバー機能とボット機能を同時に起動
keep_alive()
client.run(DISCORD_TOKEN)
