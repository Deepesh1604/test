from fastapi import FastAPI, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Union
import json
import uvicorn

YOUR_EMAIL = "22f2001290@ds.study.iitm.ac.in"

# Load dataset
with open("q-fastapi-llm-query.json") as f:
    data = json.load(f)

# Create app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/query")
def query(q: str = Query(...), response: Response = None):
    response.headers["X-Email"] = YOUR_EMAIL
    answer: Union[str, int] = "Not Found"

    try:
        q_clean = q.strip().rstrip("?")
        q_lower = q_clean.lower()

        if "total sales of" in q_lower and "in" in q_lower:
            start = q_lower.find("total sales of") + len("total sales of")
            mid = q_lower.find("in")
            product = q_clean[start:mid].strip()
            city = q_clean[q_lower.find("in") + 2:].strip()

            total = sum(
                entry["sales"]
                for entry in data
                if entry["product"].strip().lower() == product.lower()
                and entry["city"].strip().lower() == city.lower()
            )
            answer = total

        elif "how many sales reps" in q_lower and "in" in q_lower:
            region = q_clean[q_lower.find("in") + 2:].strip()
            reps = set(
                entry["rep"]
                for entry in data
                if entry["region"].strip().lower() == region.lower()
            )
            answer = len(reps)

        elif "average sales for" in q_lower and "in" in q_lower:
            start = q_lower.find("average sales for") + len("average sales for")
            mid = q_lower.find("in")
            product = q_clean[start:mid].strip()
            region = q_clean[q_lower.find("in") + 2:].strip()

            filtered_sales = [
                entry["sales"]
                for entry in data
                if entry["product"].strip().lower() == product.lower()
                and entry["region"].strip().lower() == region.lower()
            ]
            answer = round(sum(filtered_sales) / len(filtered_sales)) if filtered_sales else 0

        elif "did" in q_lower and "make the highest sale in" in q_lower:
            rep_start = q_lower.find("did") + len("did")
            rep_end = q_lower.find("make the highest sale in")
            rep = q_clean[rep_start:rep_end].strip()
            city = q_clean[q_lower.find("in") + 2:].strip()

            filtered_entries = [
                entry
                for entry in data
                if entry["rep"].strip().lower() == rep.lower()
                and entry["city"].strip().lower() == city.lower()
            ]
            if filtered_entries:
                max_entry = max(filtered_entries, key=lambda x: x["sales"])
                answer = max_entry["date"]
            else:
                answer = "N/A"

    except Exception as e:
        print("Error:", e)
        answer = "Not Found"

    return {
        "answer": answer,
        "email": YOUR_EMAIL
    }

# Run the app
if __name__ == "__main__":
    uvicorn.run("3_json_fastapi:app", host="0.0.0.0", port=8003, reload=True)