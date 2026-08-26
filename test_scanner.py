import sys
import time

sys.path.insert(0, '.')
from backend.scanner import scan_network_overview, scan_did_agent

print("--- 1. Testing Network Overview ---")
t0 = time.time()
overview = scan_network_overview()
t1 = time.time()
print(f"Overview fetched in {t1-t0:.2f}s")
print(f"Total rooms: {overview['total_rooms']}, Top DIDs: {len(overview['recent_active_dids'])}")

if overview['recent_active_dids']:
    test_did = overview['recent_active_dids'][0]['did']
    print(f"\n--- 2. Testing Scan on DID: {test_did} ---")
    t2 = time.time()
    res = scan_did_agent(test_did)
    t3 = time.time()
    print(f"DID scan completed in {t3-t2:.2f}s")
    print(f"Status: {res['status']}")
    print(f"Fingerprint: {res['fingerprint']}")
    print(f"First seen: {res['lifecycle']['first_seen']}")
    print(f"Last active: {res['lifecycle']['last_active']}")
    print(f"Total messages: {res['lifecycle']['total_signed_messages']}")
    print(f"Likely owner: {res['social_footprint']['likely_owner']}")
    print("\n--- All tests passed! ---")
