from fastapi import FastAPI
import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Initialize FastAPI
app = FastAPI()

# Allow CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Google Sheets setup from environment variable
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds_json = os.environ.get("GOOGLE_CREDS_JSON")  # JSON string
import json
creds_dict = json.loads(creds_json)

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Open your sheet by name
sheet = client.open("noncompete_cases_dataset").sheet1

@app.get("/")
def read_root():
    return {"message": "Non-Compete Assessment API running!"}

@app.get("/top_cases")
def top_cases(n: int = 3):
    records = sheet.get_all_records()
    return {"top_cases": records[:n]}

class UserInput(BaseModel):
    facts: str

@app.post("/assess")
def assess_case(user_input: UserInput):
    records = sheet.get_all_records()
    # Simple example: mark criteria if keywords in user input
    user_text = user_input.facts.lower()
    user_criteria = {
        "Trade Secrets / Confidential Information": "no" if "no trade secret" in user_text else "yes",
        "Undue Hardship on Franchisee/Employee": "yes" if "hardship" in user_text else "no",
        "Public Policy Concerns": "yes" if "worldwide" in user_text else "no"
    }

    matched_cases = []
    for case in records:
        score = 0
        if case.get("Trade Secrets / Confidential Information", "").lower() == user_criteria["Trade Secrets / Confidential Information"]:
            score += 1
        if case.get("Undue Hardship on Franchisee/Employee", "").lower() == user_criteria["Undue Hardship on Franchisee/Employee"]:
            score += 1
        if case.get("Public Policy Concerns", "").lower() == user_criteria["Public Policy Concerns"]:
            score += 1
        matched_cases.append({"case": case, "match_score": score})

    # sort descending by match score
    matched_cases.sort(key=lambda x: x["match_score"], reverse=True)
    return {"user_criteria": user_criteria, "matched_cases": matched_cases[:5]}
