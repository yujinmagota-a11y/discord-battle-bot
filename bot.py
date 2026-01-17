import discord
import google.generativeai as genai
import os

# Discordの準備
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Geminiの準備
GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# ---------------------------------------------------------
# ★ここが改良版：使えるモデルを自動で探して設定する機能
# ---------------------------------------------------------
target_model = "gemini-1.5-flash" # 第一希望

try:
    print("--- 利用可能なモデルを探しています ---")
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)
            print(f"発見: {m.name}")

    # 第一希望がリストにあるか確認（'models/'が付いている場合も考慮）
    if "models/gemini-1.5-flash" in available_models or "gemini-1.5-flash" in available_models:
        target_model = "gemini-1.5-flash"
    elif "models/gemini-pro" in available_models or "gemini-pro" in available_models:
        target_model = "gemini-pro"
    elif len(available_models) > 0:
        # どうしても見つからない場合、リストの先頭にあるやつを強制的に使う
        target_model = available_models[0].replace("models/", "")
    
    print(f"--- 決定: 【{target_model}】を使用します ---")

except Exception as e:
    print(f"モデル検索に失敗しました: {e}")
    # 失敗した場合はproをとりあえず設定
    target_model = "gemini-pro"

# モデルを設定
model = genai.GenerativeModel(target_model)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!battle'):
        topic = message.content[8:]
        # どのモデルを使っているかユーザーにも教える
        await message.channel.send(f"📢 テーマ「{topic}」についてレスバトルを開始します！\n(使用モデル: {target_model})")
        
        prompt = f"あなたはプロのディベーターです。以下のテーマについて、肯定側と否定側に分かれて激論を交わしてください。\nテーマ: {topic}\n\n形式:\n肯定側: [意見]\n否定側: [意見]\n（これを3往復）\n最後に勝敗を判定してください。"
        
        try:
            async with message.channel.typing():
                response = model.generate_content(prompt)
                await message.channel.send(response.text)
        except Exception as e:
            await message.channel.send(f"エラーが発生しました: {e}")

client.run(os.environ["DISCORD_TOKEN"])
