import requests
from bs4 import BeautifulSoup
import openai
import smtplib
from email.mime.text import MIMEText
import os

# Your properties list
MY_ADDRESSES = [
    "Kosti Palama 14Α, Thessaloniki 546 30",
    "Str. Mprantouna 3, Thessaloniki 546 26",
    "Tantalidou 6, Thessaloniki 546 26",
    "Leof. Vasilissis Olgas 188, Thessaloniki 546 55"
]

def check_outages():
    # 1. Scrape HEDNO (Electricity)
    hedno_url = "https://www.deddie.gr/en/upiresies/diakopes-reumatos/diakopes-reumatos-ana-nomo-dimo/?municipalityId=60&countyId=18"
    # 2. Scrape EYATH (Water)
    eyath_url = "https://www.eyath.gr/en/water-supply-interruptions/"
    
    content = ""
    for url in [hedno_url, eyath_url]:
        try:
            res = requests.get(url, timeout=15)
            content += f"\nSource: {url}\nContent: {res.text[:4000]}" 
        except Exception as e:
            content += f"\nError fetching {url}: {str(e)}"

    # 3. AI Analysis with Improved Prompt
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    prompt = f"""
    You are a professional Property Management Assistant for apartments in Thessaloniki.
    Your goal is to monitor utility outages (Electricity and Water) to protect guest experience.

    DATA FROM UTILITY COMPANIES:
    {content}

    OUR PROPERTIES:
    {MY_ADDRESSES}

    INSTRUCTIONS:
    1. Check if any of the addresses or their immediate neighborhoods are mentioned in the outage lists.
    2. If an outage is found: Provide a clear report in English including: Property Name/Address, Type (Water/Power), Start/End Time, and Reason.
    3. If NO outage is found: Provide a brief "All Clear" status report in English, confirming that all properties are currently unaffected.
    4. Format the output as a professional email.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    
    report = response.choices[0].message.content
    
    # Send email REGARDLESS of the outcome
    send_email(report)

def send_email(text):
    msg = MIMEText(text)
    msg['Subject'] = "Thessaloniki Utility Status Report - Proliving"
    msg['From'] = "prolivingike@gmail.com"
    msg['To'] = "prolivingike@gmail.com"
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login("prolivingike@gmail.com", os.getenv("EMAIL_PASSWORD"))
            server.send_message(msg)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    check_outages()
