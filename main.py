from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
from bs4 import BeautifulSoup
import os
from scrapper import *
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TOKEN")
chat_id = os.getenv('CHAT_ID')


    
async def scrape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # check args
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /scrape <url> <keyword>")
        return

    url = context.args[0]
    keyword = " ".join(context.args[1:])  # allow multi-word keywords

    try:
        # run scraper
        html = fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")
        articles = extract_articles_from_soup(soup, url)
        filtered = filter_by_keywords(articles, [keyword])
        message = format_articles_message(filtered, keyword=keyword)

        # Telegram 4096 char limit safeguard
        if len(message) > 4000:
            chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
            for chunk in chunks:
                await update.message.reply_text(chunk)
        else:
            await update.message.reply_text(message)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")
        
def main():
    app = Application.builder().token(token).build()

    # command: /scrape <url> <keyword>
    app.add_handler(CommandHandler("scrape", scrape))

    print("✅ Bot is running… send /scrape <url> <keyword>")
    app.run_polling()

if __name__ == "__main__":
    main()