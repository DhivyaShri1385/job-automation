import os, smtplib, requests, datetime
from email.message import EmailMessage

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

SMTP_HOST = os.getenv("EMAIL_SMTP_HOST")
SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
SMTP_USER = os.getenv("EMAIL_SMTP_USER")
SMTP_PASS = os.getenv("EMAIL_SMTP_PASS")

EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_FROM = os.getenv("EMAIL_FROM")

SEARCH_QUERY = (
    '"data analyst" OR "data analytics" '
    'AND ("entry" OR "junior" OR "associate" OR "intern" OR "graduate")'
)

COUNTRY = "in"
RESULTS = 30

ENTRY_KEYWORDS = ["entry", "junior", "associate", "intern", "graduate"]

STARTUP_HINTS = [
    "labs", "ventures", "technologies", "tech", "solutions",
    "systems", "innovations", "analytics", "ai", "data"
]

BIG_COMPANY_BLOCKLIST = [
    "tcs", "infosys", "wipro", "accenture", "cognizant",
    "ibm", "capgemini", "deloitte"
]

def fetch_jobs():
    url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/1"
    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "what": SEARCH_QUERY,
        "results_per_page": RESULTS,
    }

    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def looks_entry_level(text):
    text = text.lower()
    return any(k in text for k in ENTRY_KEYWORDS)

def looks_like_startup(company):
    if not company:
        return False

    name = company.lower()

    if any(big in name for big in BIG_COMPANY_BLOCKLIST):
        return False

    if any(hint in name for hint in STARTUP_HINTS):
        return True

    if len(company.split()) <= 3:
        return True

    return False

def filter_jobs(data):
    jobs = []

    for j in data.get("results", []):
        title = j.get("title", "")
        company = j.get("company", {}).get("display_name", "")
        location = j.get("location", {}).get("display_name", "")
        url = j.get("redirect_url", "")

        combined_text = f"{title} {j.get('description','')}"

        if not looks_entry_level(combined_text):
            continue

        if not looks_like_startup(company):
            continue

        jobs.append({
            "title": title,
            "company": company,
            "location": location,
            "url": url
        })

    return jobs

def deduplicate(jobs):
    seen = set()
    unique = []

    for j in jobs:
        if j["url"] in seen:
            continue
        seen.add(j["url"])
        unique.append(j)

    return unique

def format_email(jobs):
    today = datetime.date.today().isoformat()

    if not jobs:
        return f"No matching startup entry-level roles found today ({today})."

    body = f"Daily Startup Data Analytics Jobs — {today}\n\n"

    for i, j in enumerate(jobs, 1):
        body += (
            f"{i}. {j['title']}\n"
            f"   Company: {j['company']}\n"
            f"   Location: {j['location']}\n"
            f"   Apply: {j['url']}\n\n"
        )

    return body

def send_email(subject, body):

    print("SMTP_HOST =", repr(SMTP_HOST))
    print("SMTP_PORT =", repr(SMTP_PORT))

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=60) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)

def main():
    try:
        raw = fetch_jobs()
        jobs = filter_jobs(raw)
        jobs = deduplicate(jobs)

        email_body = format_email(jobs[:25])

        send_email(
            subject="Daily Entry-Level Data Analytics Jobs",
            body=email_body
        )

    except Exception as e:
        send_email(
            subject="Job Automation Error",
            body=str(e)
        )

if __name__ == "__main__":
    main()
