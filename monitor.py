import requests
import json
import openai
import smtplib
from email.mime.text import MIMEText
import os
from datetime import datetime

# Properties list
MY_ADDRESSES = [
    "Kosti Palama 14Α, Thessaloniki 546 30",
    "Str. Mprantouna 3, Thessaloniki 546 26",
    "Tantalidou 6, Thessaloniki 546 26",
    "Leof. Vasilissis Olgas 188, Thessaloniki 546 55"
]

STATE_FILE = "last_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"active_outages": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def check_outages():
    current_hour = datetime.now().hour
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # 1. Scrape Websites
    content = ""
    for url in ["https://www.deddie.gr/en/upiresies/diakopes-reumatos/diakopes-reumatos-ana-nomo-dimo/?municipalityId=60&countyId=18", 
                "https://www.eyath.gr/en/water-supply-interruptions/"]:
        try:
            res = requests.get(url, timeout=15)
            content += f"\nSource: {url}\nContent: {res.text[:4000]}"
        except: continue

    # 2. AI Analysis
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    last_state = load_state()
    
    prompt = f"""
    Current Time: {datetime.now().strftime("%Y-%m-%d %H:%M")}
    Properties: {MY_ADDRESSES}
    Last Reported Outages: {last_state['active_outages']}
    
    Website Data: {content}

    TASK:
    1. Identify outages affecting our properties or neighborhoods.
    2. Logic:
       - EMERGENCY (Unplanned): Always report every hour.
       - PLANNED (Future date): Only report if current hour is 8 AM.
       - PLANNED (Today): Report every hour.
       - RESTORED: If an outage from 'Last Reported Outages' is no longer in the website data, mark as 'Restored'.
    
    3. EMAIL FORMAT (If notification needed):
       Subject: Outage in [Type] at [Property]
       Body: 
       Type: [Electricity/Water] near [Property]
       Date: [Date]
       Expected Restoration: [Time]
       
       (If Restored):
       Subject: FIXED: [Type] restored at [Property]
       Body: The utility issue at [Property] has been resolved.

    If no new notification is needed based on the logic, reply ONLY with 'No'.
    Otherwise, provide the email(s). If multiple, separate with '---'.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    
    answer = response.choices[0].message.content
    
    if "No" not in answer:
        emails = answer.split('---')
        for email_content in emails:
            send_email(email_content.strip())
        
        # Update state (This part is simplified for AI to handle)
        # In a real scenario, we'd extract IDs, but here we'll let the AI's next run handle it.
        # We save a dummy state to trigger 'Restored' logic next time.
        save_state({"active_outages": [answer[:100]]}) 

def send_email(text):
    # Extract subject from first line
    lines = text.split('\n')
    subject = lines[0].replace("Subject: ", "")
    body = "\n".join(lines[1:])

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = "prolivingike@gmail.com"
    msg['To'] = "prolivingike@gmail.com"
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login("prolivingike@gmail.com", os.getenv("EMAIL_PASSWORD"))
            server.send_message(msg)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_outages()
