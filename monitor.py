import requests
from bs4 import BeautifulSoup
import openai
import smtplib
from email.mime.text import MIMEText
import os

# הגדרות הכתובות שלך
MY_ADDRESSES = [
    "Kosti Palama 14Α, Thessaloniki",
    "Str. Mprantouna 3, Thessaloniki",
    "Tantalidou 6, Thessaloniki",
    "Leof. Vasilissis Olgas 188, Thessaloniki"
]

def check_outages():
    # 1. סריקת אתר חברת החשמל (HEDNO) - מחוז סלוניקי
    hedno_url = "https://www.deddie.gr/en/upiresies/diakopes-reumatos/diakopes-reumatos-ana-nomo-dimo/?municipalityId=60&countyId=18"
    # 2. סריקת אתר חברת המים (EYATH)
    eyath_url = "https://www.eyath.gr/en/water-supply-interruptions/"
    
    # שליפת הטקסט מהאתרים (קוד פשוט לדוגמה)
    content = ""
    for url in [hedno_url, eyath_url]:
        try:
            res = requests.get(url, timeout=10)
            content += res.text[:5000] # לוקחים חלק מהטקסט לניתוח
        except:
            continue

    # 3. ניתוח באמצעות AI (OpenAI API)
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"Here are utility outages in Thessaloniki: {content}. Our addresses are: {MY_ADDRESSES}. Are any of these addresses affected or nearby? Answer ONLY with a short report if yes, or 'No' if not."
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    
    analysis = response.choices[0].message.content
    
    if "No" not in analysis:
        send_email(analysis)

def send_email(text):
    msg = MIMEText(text)
    msg['Subject'] = "התראת תשתית - סלוניקי"
    msg['From'] = "prolivingike@gmail.com"
    msg['To'] = "prolivingike@gmail.com"
    
    # התחברות לשרת Gmail (דורש App Password)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login("prolivingike@gmail.com", os.getenv("EMAIL_PASSWORD"))
        server.send_message(msg)

if __name__ == "__main__":
    check_outages()
