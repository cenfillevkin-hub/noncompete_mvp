from pydantic import BaseModel

# Define this at the top of your main.py
class UserInput(BaseModel):
    facts: str

from fastapi import FastAPI
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pydantic import BaseModel
from typing import List, Dict

# Initialize FastAPI
app = FastAPI()

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Open your sheet by name
sheet = client.open("noncompete_cases_dataset").sheet1  # <-- Replace with your Google Sheet name
headers = sheet.row_values(1)

# -------------------------------
# Helper: Map user facts → criteria
# -------------------------------
def map_user_facts_to_criteria(facts: str) -> Dict[str, str]:
    criteria = {}
    f = facts.lower()

    # Trade Secrets
    if "no formula" in f or "no secret" in f or "didn't see" in f:
        criteria["Trade Secrets / Confidential Information"] = "No"
    elif "formula" in f or "secret" in f or "confidential" in f:
        criteria["Trade Secrets / Confidential Information"] = "Yes"

    # Undue Hardship
    if "hardship" in f or "fired" in f or "necessity" in f or "burden" in f:
        criteria["Undue Hardship on Franchisee/Employee"] = "Yes"
        # Courts often link hardship to public policy
        criteria["Public Policy Concerns"] = "Yes"

    return criteria

# -------------------------------
# Request model
# -------------------------------
class AssessmentRequest(BaseModel):
    facts: str

# -------------------------------
# Routes
# -------------------------------
@app.get("/")
def read_root():
    return {"message": "Non-Compete Self-Assessment API is running!"}

@app.get("/raw")
def get_raw_data():
    return sheet.get_all_values()

@app.get("/cases")
def get_cases():
    records = sheet.get_all_records()
    return records

@app.post("/assess")
def assess_case(user_input: UserInput):
    facts = user_input.facts.lower()
    user_criteria = {}

    # Helper for negation
    def is_negated(term):
        return any(neg in facts for neg in ["no " + term, "not " + term, "didn't " + term, "did not " + term])

    # Trade secrets
    if "secret" in facts or "formula" in facts or "process" in facts:
        if is_negated("secret") or "didn’t see" in facts or "did not see" in facts:
            user_criteria["Trade Secrets / Confidential Information"] = "No"
        else:
            user_criteria["Trade Secrets / Confidential Information"] = "Yes"

    # Hardship
    if "hardship" in facts or "fired" in facts or "lose job" in facts:
        if "no hardship" in facts or "not hardship" in facts:
            user_criteria["Undue Hardship on Franchisee/Employee"] = "No"
        else:
            user_criteria["Undue Hardship on Franchisee/Employee"] = "Yes"
            # hardship implies public policy concerns
            user_criteria["Public Policy Concerns"] = "Yes"

    # Customer goodwill
    if "customer" in facts or "loyalty" in facts:
        user_criteria["Customer Goodwill"] = "Yes"

    # Training
    if "training" in facts or "trained" in facts or "know-how" in facts:
        user_criteria["Specialized Training / Skill Investment"] = "Yes"

    # Territory / geography
    if "worldwide" in facts or "anywhere" in facts or "too broad" in facts:
        user_criteria["Reasonable Geographic Scope"] = "No"

    # Now match against cases
    all_cases = sheet.get_all_records()
    matched = []
    for case in all_cases:
        score = 0
        for criterion, value in user_criteria.items():
            if criterion in case and str(case[criterion]).strip().lower() == value.lower():
                score += 1
        matched.append({"case": case, "match_score": score})

    matched = sorted(matched, key=lambda x: x["match_score"], reverse=True)
    return {"user_criteria": user_criteria, "matched_cases": matched[:5]}
