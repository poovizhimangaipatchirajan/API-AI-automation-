# 🎓 AI-Powered Student Progress Email Automation

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![API](https://img.shields.io/badge/Google%20Sheets%20API-v4-green.svg)](https://developers.google.com/sheets/api)
[![API](https://img.shields.io/badge/Gmail%20API-v1-red.svg)](https://developers.google.com/gmail/api)
[![OpenAI](https://img.shields.io/badge/OpenAI-Structured%20Outputs-orange.svg)](https://platform.openai.com/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

An automated Python pipeline that reads student performance records from a **Google Sheet**, formats tailored, empathetic academic evaluations using **OpenAI (Structured Outputs)**, and delivers stylized HTML reports directly to parents via the **Gmail API**.

---

## 🌟 Key Features

- **Automated Sheet Ingestion:** Connects directly to Google Sheets via `gspread` and pulls real-time student grades, attendance, and contact information.
- **Robust Key Normalization:** Automatically adapts to varied column naming schemes (e.g., `Parent Email`, `parent_email`, `Email`).
- **Context-Aware AI Drafting:** Dynamically adjusts email tone based on student performance (`Passing`, `Needs Support`, `At Risk`).
- **Structured Outputs (Pydantic):** Guarantees type-safe responses with synchronized plain-text and rich HTML formatting.
- **Embedded Performance Card:** Generates a clean, highlighted summary card in the center of each report.
- **Standardized Signature:** Enforces an official closing signature (`Best regards, Malini, School Principal`).
- **Rate-Limit Safe:** Includes pacing buffers to prevent API throttling during batch sending.

---

## 🏗️ Architecture & Flow

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────────┐
│  Google Sheet   │ ────> │  gspread Client │ ────> │ Data Normalization  │
└─────────────────┘       └─────────────────┘       └─────────────────────┘
                                                               │
                                                               ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────────┐
│ Parent's Inbox  │ <──── │    Gmail API    │ <──── │ OpenAI LLM Engine   │
│ (Rich HTML Box) │       │   Send Gateway  │       │ (Pydantic Schema)   │
└─────────────────┘       └─────────────────┘       └─────────────────────┘
```

---

## 📁 Project Directory Structure

```text
├── credentials.json       # OAuth 2.0 Desktop credentials from Google Cloud (Untracked)
├── token.json             # Cached user access & refresh token (Generated on 1st run)
├── .env                   # Environment variables containing API keys (Untracked)
├── .gitignore             # Git ignore file protecting credentials & virtualenvs
├── main.py                # Main orchestration script
├── requirements.txt       # Project dependencies
└── README.md              # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.10 or higher
- A Google Cloud Project with **Google Sheets API** and **Gmail API** enabled
- An active OpenAI API key

---

### 2. Google Cloud Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g., `Student-Report-Automation`).
3. Enable the **Google Sheets API** and **Gmail API**.
4. Configure the **OAuth Consent Screen**:
   - Set user type to **External**.
   - Under **Test Users**, add the Gmail account you will use to send emails.
5. Create an **OAuth Client ID**:
   - Navigate to **APIs & Services > Credentials > Create Credentials > OAuth client ID**.
   - Application type: **Desktop app**.
   - Download the JSON file, place it in your root directory, and rename it to `credentials.json`.

---

### 3. Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/student-email-automation.git
   cd student-email-automation
   ```

2. **Create and activate a virtual environment:**
   - **Windows:**
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Or manually install: `pip install google-auth google-auth-oauthlib google-api-python-client gspread openai pydantic python-dotenv`)*

4. **Configure your `.env` file:**
   Create a file named `.env` in the root folder:
   ```env
   OPENAI_API_KEY=sk-proj-yourActualOpenAIApiKeyHere
   ```

---

### 4. Prepare Your Google Sheet

Create a native Google Sheet (ensure it is saved as a Google Sheet, not an uploaded `.xlsx` or `.csv` preview) with the following column headers:

| Student_ID | Student_Name | Course | Midterm_Score | Final_Score | Attendance_Rate | Grade | Status | Parent_Email |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| STU-101 | Maya Chen | Computer Science | 88 | 94 | 96% | A | Passing | parent1@example.com |
| STU-102 | Liam Brooks | Computer Science | 62 | 68 | 81% | D | Needs Support | parent2@example.com |

Open `main.py` and set your `SPREADSHEET_ID`:
```python
SPREADSHEET_ID = "YOUR_SPREADSHEET_ID_HERE"
WORKSHEET_NAME = "Sheet1"
```

---

## 💻 Usage

Run the automation:

```bash
python main.py
```

### First-Time Run
1. A browser tab will open requesting OAuth permission.
2. Select your Google account (the one registered under **Test Users**).
3. If presented with "Google hasn't verified this app", click **Advanced > Go to App (unsafe)**.
4. Check all authorization boxes to grant access to Sheets and Gmail.
5. The session saves locally as `token.json` for all future runs.

---

## 🔒 Security Best Practices

Ensure your sensitive keys and tokens are **never** committed to version control:

Create a `.gitignore` containing:
```gitignore
# Virtual Environment
venv/
.venv/

# Environment Variables
.env

# Google OAuth Credentials & Cached Tokens
credentials.json
token.json

# Python Cache
__pycache__/
*.py[cod]
```

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).