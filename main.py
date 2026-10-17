import base64
import os
import time
from email.message import EmailMessage
from typing import Any, Dict, List

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import gspread
from openai import OpenAI
from pydantic import BaseModel

# ---------------- LOAD ENVIRONMENT VARIABLES ----------------
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY is not set. Please check your .env file.")

client = OpenAI(api_key=api_key)

# ---------------- CONFIGURATION ----------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.send",
]

# Spreadsheet configuration
SPREADSHEET_ID = "1O5_bg3R_tnEHfYqU0-CqunzwYWUqYAEBQn3EB3daWg0"
WORKSHEET_NAME = "Sheet1"


# ---------------- DATA SCHEMA ----------------
class StudentReportEmail(BaseModel):
    subject: str
    body_text: str
    body_html: str


# ---------------- 1. AUTHENTICATION ----------------
def get_credentials():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                raise FileNotFoundError(
                    "credentials.json not found! Please place credentials.json in this directory."
                )
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


# ---------------- 2. FETCH ALL STUDENT ROWS ----------------
def fetch_student_records(creds, spreadsheet_id: str) -> List[Dict[str, Any]]:
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(spreadsheet_id)
    try:
        worksheet = sh.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        # Fallback to the first available worksheet if tab name doesn't match
        worksheet = sh.get_worksheet(0)
    return worksheet.get_all_records()


# ---------------- 3. GENERATE PERSONALIZED EMAIL ----------------
def generate_student_email(student: Dict[str, Any]) -> StudentReportEmail:
    # Normalize dictionary keys for case/whitespace insensitivity
    norm_student = {str(k).strip().lower().replace(" ", "_"): v for k, v in student.items()}

    student_name = norm_student.get("student_name") or norm_student.get("name") or "Student"
    course = norm_student.get("course", "Academic Program")
    midterm = norm_student.get("midterm_score", "N/A")
    final = norm_student.get("final_score", "N/A")
    attendance = norm_student.get("attendance_rate", "N/A")
    grade = norm_student.get("grade", "N/A")
    status = norm_student.get("status", "N/A")

    prompt = f"""
    You are Malini, the School Principal, writing an individual academic progress report to the parent of {student_name}.

    Student Academic Record:
    - Student Name: {student_name}
    - Course: {course}
    - Midterm Score: {midterm}
    - Final Score: {final}
    - Attendance Rate: {attendance}
    - Grade: {grade}
    - Current Status: {status}

    Instructions:
    1. Subject Line: Create a clean, official subject line (e.g., "Academic Progress Report: {student_name} - {course}").
    2. Tone:
       - If Status is 'Passing' or Grade is A/B: Warm, encouraging, praising specific achievements.
       - If Status is 'Needs Support' or 'At Risk': Empathetic, supportive, constructive, and offering clear guidance or extra help sessions.
    
    3. Performance Summary Card (Mandatory HTML Structure):
       In 'body_html', you MUST present the student's metrics inside an inline CSS box/card styled exactly like this:
       
       <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px 20px; margin: 20px 0; max-width: 500px; font-family: sans-serif;">
         <h3 style="margin-top: 0; color: #1e293b; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px;">Performance Summary</h3>
         <table style="width: 100%; border-collapse: collapse; font-size: 14px; color: #334155;">
           <tr><td style="padding: 6px 0;"><strong>Course:</strong></td><td>{course}</td></tr>
           <tr><td style="padding: 6px 0;"><strong>Midterm Score:</strong></td><td>{midterm}/100</td></tr>
           <tr><td style="padding: 6px 0;"><strong>Final Score:</strong></td><td>{final}/100</td></tr>
           <tr><td style="padding: 6px 0;"><strong>Attendance:</strong></td><td>{attendance}</td></tr>
           <tr><td style="padding: 6px 0;"><strong>Overall Grade:</strong></td><td><span style="font-weight: bold; color: #0284c7;">{grade}</span></td></tr>
           <tr><td style="padding: 6px 0;"><strong>Academic Standing:</strong></td><td><strong>{status}</strong></td></tr>
         </table>
       </div>

    4. Mandatory Sign-off Requirement:
       At the very end of both 'body_text' and 'body_html', you MUST close the letter with exactly:

       Best regards,
       Malini
       School Principal

       In 'body_html', format it with line breaks:
       <p style="margin-top: 24px; color: #334155;">Best regards,<br><strong>Malini</strong><br>School Principal</p>

    5. Plain Text Version:
       Ensure 'body_text' includes the opening paragraph, a clear textual breakdown of scores, your constructive feedback, and the exact signature.
    """

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are Malini, a professional and caring School Principal communicating student progress with parents."},
            {"role": "user", "content": prompt},
        ],
        response_format=StudentReportEmail,
    )
    return completion.choices[0].message.parsed
    
    # ---------------- 4. DISPATCH EMAIL ----------------
def send_gmail_message(service, recipient: str, email_content: StudentReportEmail) -> str:
    message = EmailMessage()
    message["To"] = recipient
    message["From"] = "me"
    message["Subject"] = email_content.subject

    message.set_content(email_content.body_text)
    message.add_alternative(email_content.body_html, subtype="html")

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    result = service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
    return result.get("id")


# ---------------- MAIN ITERATION WORKFLOW ----------------
def run_batch_dispatch():
    print("Authenticating with Google Services...")
    creds = get_credentials()
    gmail_service = build("gmail", "v1", credentials=creds)

    print("Retrieving student records from Google Sheet...")
    records = fetch_student_records(creds, SPREADSHEET_ID)
    print(f"Loaded {len(records)} records.")

    for idx, raw_student in enumerate(records, start=1):
        # Normalize dictionary keys to handle variations like 'Parent Email', 'parent_email', 'Email'
        student = {str(k).strip().lower().replace(" ", "_"): v for k, v in raw_student.items()}

        parent_email = (
            student.get("parent_email")
            or student.get("email")
            or student.get("parent_mail")
            or student.get("email_address")
            or ""
        )
        parent_email = str(parent_email).strip()

        student_name = (
            student.get("student_name")
            or student.get("name")
            or student.get("student")
            or f"Row #{idx}"
        )

        if not parent_email or "@" not in parent_email:
            print(f"[{idx}/{len(records)}] Skipping {student_name}: Invalid or missing email ('{parent_email}').")
            continue

        print(f"\n[{idx}/{len(records)}] Processing {student_name}...")
        print(f"Generating personalized report for: {parent_email}")

        email_data = generate_student_email(raw_student)

        message_id = send_gmail_message(gmail_service, parent_email, email_data)
        print(f"Sent! Subject: '{email_data.subject}' (Gmail ID: {message_id})")

        # Small pause to avoid API rate-limit spikes
        time.sleep(1.2)

    print("\nAll progress reports have been processed and dispatched!")


if __name__ == "__main__":
    run_batch_dispatch()