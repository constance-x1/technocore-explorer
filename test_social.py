import json
import urllib.request
from backend.scanner import scan_did_agent, extract_social_footprint

print("Fetching recent messages from technocore room to find social links...")
req = urllib.request.urlopen("https://technocore.chat/r/technocore?format=json&limit=200", timeout=5)
data = json.loads(req.read().decode('utf-8'))

found_dids = []
for msg in data.get('messages', []):
    txt = msg.get('text', '')
    if ('x.com' in txt or 'twitter.com' in txt or 'github.com' in txt) and msg.get('from', '').startswith('did:key:'):
        found_dids.append((msg.get('from'), txt))

print(f"Found {len(found_dids)} DIDs with social/git links in recent room activity.")
if found_dids:
    target_did, sample_text = found_dids[0]
    print(f"\nTesting attribution on DID: {target_did}")
    print(f"Sample message: {sample_text}")
    res = scan_did_agent(target_did)
    print("\nSocial Footprint Result:")
    print("Likely Owner:", json.dumps(res['social_footprint']['likely_owner'], indent=2))
    print("X Posts:", json.dumps(res['social_footprint']['x_posts'], indent=2))
    print("Git Commits:", json.dumps(res['social_footprint']['git_commits'], indent=2))
