# ipo_monitor.py
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

# ============== CONFIGURATION ==============
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")  # Get free key at finnhub.io
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")  # Gmail App Password
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")
OFFER_AMOUNT_THRESHOLD = 200_000_000  # USD 200 million

# ============== FETCH IPO DATA ==============
def get_todays_ipos():
    """Fetch IPOs from Finnhub API"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    url = f"https://finnhub.io/api/v1/calendar/ipo?from={today}&to={today}&token={FINNHUB_API_KEY}"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get("ipoCalendar", [])
    else:
        print(f"Error fetching IPO data: {response.status_code}")
        return []

# ============== FILTER IPOs ==============
def filter_large_ipos(ipos):
    """Filter IPOs with offer amount > USD 200 million"""
    qualifying_ipos = []
    
    for ipo in ipos:
        # Calculate offer amount: IPO price × shares offered
        price = ipo.get("price") or 0
        shares = ipo.get("numberOfShares") or 0
        
        # Handle price range (e.g., "15-17" -> take midpoint)
        if isinstance(price, str) and "-" in price:
            low, high = price.split("-")
            price = (float(low) + float(high)) / 2
        else:
            price = float(price) if price else 0
        
        shares = int(shares) if shares else 0
        offer_amount = price * shares
        
        if offer_amount >= OFFER_AMOUNT_THRESHOLD:
            qualifying_ipos.append({
                "symbol": ipo.get("symbol"),
                "company": ipo.get("name"),
                "date": ipo.get("date"),
                "price": price,
                "shares": shares,
                "offer_amount": offer_amount,
                "exchange": ipo.get("exchange")
            })
    
    return qualifying_ipos

# ============== SEND EMAIL ==============
def send_email(qualifying_ipos):
    """Send email notification with qualifying IPOs"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    if not qualifying_ipos:
        subject = f"IPO Monitor - No Large IPOs Today ({today})"
        body = "No IPOs with offer amount above USD 200 million are scheduled for today."
    else:
        subject = f"IPO Alert - {len(qualifying_ipos)} Large IPO(s) Today ({today})"
        body = "The following IPOs meet the criteria (Offer Amount > USD 200M):\n\n"
        
        for ipo in qualifying_ipos:
            body += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ticker: {ipo['symbol']}
Company: {ipo['company']}
IPO Date: {ipo['date']}
Price: ${ipo['price']:.2f}
Shares Offered: {ipo['shares']:,}
Offer Amount: ${ipo['offer_amount']:,.2f}
Exchange: {ipo['exchange']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    # Create email
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    
    # Send via Gmail SMTP
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        print(f"Email sent successfully to {EMAIL_RECEIVER}")
    except Exception as e:
        print(f"Failed to send email: {e}")

# ============== MAIN ==============
def main():
    print(f"Running IPO Monitor at {datetime.now()}")
    print("=" * 50)
    
    # Step 1: Fetch today's IPOs
    ipos = get_todays_ipos()
    print(f"Found {len(ipos)} IPO(s) scheduled for today")
    
    # Step 2: Filter by offer amount > $200M
    qualifying_ipos = filter_large_ipos(ipos)
    print(f"Found {len(qualifying_ipos)} IPO(s) above $200M threshold")
    
    # Step 3: Send email
    send_email(qualifying_ipos)
    
    print("=" * 50)
    print("IPO Monitor completed successfully")

if __name__ == "__main__":
    main()
