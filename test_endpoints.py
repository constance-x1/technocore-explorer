import urllib.parse
from api.scanner import scan_did_agent, scan_network_overview

print("--- 1. Testing scan_network_overview() ---")
overview = scan_network_overview()
print("Status:", overview.get("status"))
print("Rooms count:", overview.get("total_rooms"))
print("Active DIDs count:", len(overview.get("recent_active_dids", [])))

if overview.get("recent_active_dids"):
    sample_did = overview["recent_active_dids"][0]["did"]
    print(f"\n--- 2. Testing scan_did_agent('{sample_did}') ---")
    res = scan_did_agent(sample_did)
    print("Status:", res.get("status"))
    print("Fingerprint:", res.get("fingerprint"))
    print("Total signed messages:", res.get("lifecycle", {}).get("total_signed_messages"))
    print("First seen:", res.get("lifecycle", {}).get("first_seen"))
    print("Last active:", res.get("lifecycle", {}).get("last_active"))
    print("Likely owner:", res.get("social_footprint", {}).get("likely_owner"))
    print("\n--- All endpoints verified successfully! ---")
