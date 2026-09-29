"""Generate interconnected enterprise sample data into ../sample_data (stdlib only, deterministic)."""
import csv, json, os, random
random.seed(42)
OUT = os.path.join(os.path.dirname(__file__), "..", "sample_data")
FIRST = "Aarav Priya Rohan Ananya Vikram Sneha Karthik Divya Arjun Meera Rahul Kavya Imran Neha Sanjay Lakshmi Aditya Pooja Nikhil Isha".split()
LAST = "Reddy Sharma Iyer Rao Khan Patel Nair Gupta Menon Das Verma Naidu Singh Joshi Kulkarni".split()
ROLES = ["Sales Executive", "Support Engineer", "DevOps Engineer", "Product Manager", "Account Manager", "SRE"]
COMP = ["Contoso", "Fabrikam", "Northwind", "Tailspin", "Adatum", "Litware", "Woodgrove", "Proseware", "Infosys BPM", "TCS Digital"]
SUFFIX = ["Systems", "Labs", "Cloud", "Logistics", "Bank", "Health", "Retail", "Energy"]
ISSUES = ["login timeout", "certificate expiry", "slow dashboard", "API 429 errors", "SSO failure", "data sync delay", "billing mismatch"]
CAUSES = ["expired TLS certificate", "bad config rollout", "database connection pool exhaustion", "memory leak in worker", "DNS misconfiguration"]

def name(): return f"{random.choice(FIRST)} {random.choice(LAST)}"
emps = [{"id": i, "name": name(), "role": random.choice(ROLES)} for i in range(1, 51)]
custs = [{"id": i, "company": f"{random.choice(COMP)} {random.choice(SUFFIX)} {i}", "tier": random.choice(["Enterprise", "Growth", "Starter"])} for i in range(1, 101)]
tickets = [{"id": i, "customer_id": random.randint(1, 100), "issue": random.choice(ISSUES), "assignee_id": random.randint(1, 50),
            "frustration": random.randint(1, 5), "resolved": random.random() > 0.2} for i in range(1, 501)]
deals = [{"id": i, "customer_id": random.randint(1, 100), "value_usd": random.randint(5, 400) * 1000, "stage": random.choice(["won", "lost", "negotiation"]),
          "competitor": random.choice(["Salesforce", "Zoho", "HubSpot", "None"])} for i in range(1, 101)]
meetings = [{"id": i, "customer_id": random.randint(1, 100), "organizer_id": random.randint(1, 50),
             "summary": f"Discussed {random.choice(ISSUES)} and renewal", "action_items": random.randint(0, 5)} for i in range(1, 301)]
emails = [{"id": i, "customer_id": random.randint(1, 100), "from_id": random.randint(1, 50), "subject": f"Re: {random.choice(ISSUES)}"} for i in range(1, 1001)]
incidents = [{"id": i, "root_cause": random.choice(CAUSES), "severity": random.randint(1, 4), "customer_id": random.randint(1, 100),
              "engineer_id": random.randint(1, 50)} for i in range(1, 301)]
docs = [{"id": i, "title": f"Runbook: {random.choice(CAUSES)}", "owner_id": random.randint(1, 50)} for i in range(1, 201)]
os.makedirs(OUT, exist_ok=True)
for fname, rows in dict(employees=emps, customers=custs, tickets=tickets, deals=deals, meetings=meetings,
                        emails=emails, incidents=incidents, documents=docs).items():
    with open(os.path.join(OUT, f"{fname}.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)

def load_into_memory():
    """Turn a slice of the data into memories so the brain starts warm: python seed.py --load"""
    from app.memory_service import MemoryService
    svc = MemoryService(); cmap = {c["id"]: c["company"] for c in custs}; emap = {e["id"]: e["name"] for e in emps}
    for t in tickets[:60]:
        svc.retain("support", "success" if t["resolved"] else "failure",
                   f"Ticket for {cmap[t['customer_id']]}: {t['issue']}, frustration {t['frustration']}/5, handled by {emap[t['assignee_id']]}",
                   ["ticket"], [cmap[t["customer_id"]], emap[t["assignee_id"]]], 0.6, 0.5)
    for i in incidents[:40]:
        svc.retain("devops", "episodic", f"Incident sev{i['severity']} at {cmap[i['customer_id']]}: root cause {i['root_cause']}",
                   ["incident", "root-cause"], [cmap[i["customer_id"]], emap[i["engineer_id"]]], 0.6, 0.6)
    for d in deals[:30]:
        svc.retain("sales", "outcome", f"Deal with {cmap[d['customer_id']]} {d['stage']} at ${d['value_usd']} vs {d['competitor']}",
                   ["deal"], [cmap[d["customer_id"]]], 0.6, 0.6)
    print("loaded memories:", svc.status()["local"]["total"])

if __name__ == "__main__":
    import sys
    print(f"wrote sample data: {len(emps)} employees, {len(custs)} customers, {len(tickets)} tickets, {len(deals)} deals, "
          f"{len(meetings)} meetings, {len(emails)} emails, {len(incidents)} incidents, {len(docs)} documents")
    if "--load" in sys.argv: load_into_memory()
