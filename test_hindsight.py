import os
from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()

API_KEY = os.getenv("HINDSIGHT_API_KEY")
BASE_URL = os.getenv(
    "HINDSIGHT_BASE_URL",
    "https://api.hindsight.vectorize.io"
)

BANK_ID = "Incident Experience"

if not API_KEY:
    raise RuntimeError("HINDSIGHT_API_KEY is missing from .env")

print("=" * 60)
print("INCIDENT RESPONSE AGENT - HINDSIGHT MEMORY TEST")
print("=" * 60)

print(f"\nBase URL : {BASE_URL}")
print(f"Bank ID  : {BANK_ID}")
print("\nConnecting to Hindsight...")

client = Hindsight(
    base_url=BASE_URL,
    api_key=API_KEY
)

try:
    # ---------------------------------------------------------
    # STEP 1: STORE AN INCIDENT
    # ---------------------------------------------------------

    print("\n1. Storing incident memory...")

    incident = """
    Incident ID: INC-001

    Service: Production Orders API

    Symptom:
    API latency increased significantly and customers experienced
    slow order requests.

    Investigation:
    The team checked application logs, database metrics,
    CPU usage, memory usage, and network performance.

    Root Cause:
    The orders database table was missing an index required
    for a frequently used query.

    Resolution:
    The team added the missing database index.

    Outcome:
    API latency returned to normal.

    Resolution Time:
    18 minutes.

    Successful Action:
    Adding the database index resolved the incident.

    Lesson Learned:
    When Orders API latency increases, check database query
    performance and indexes early in the investigation.
    """

    client.retain(
        bank_id=BANK_ID,
        content=incident
    )

    print("✅ Incident memory stored successfully!")

    # ---------------------------------------------------------
    # STEP 2: RECALL THE INCIDENT
    # ---------------------------------------------------------

    print("\n2. Searching Hindsight memory...")

    result = client.recall(
        bank_id=BANK_ID,
        query=(
            "What happened in the previous production Orders API "
            "latency incident? What was the root cause and what "
            "action successfully resolved it?"
        )
    )

    print("\n🔎 HINDSIGHT RECALL RESULT")
    print("=" * 60)

    if not result.results:
        print("No memories were returned.")

    else:
        for index, memory in enumerate(result.results, start=1):
            print(f"\nMemory {index}")
            print("-" * 60)
            print(f"Type : {memory.type}")
            print(f"Text : {memory.text}")

    print("\n" + "=" * 60)
    print("🎉 HINDSIGHT MEMORY TEST COMPLETED!")
    print("=" * 60)

finally:
    client.close()