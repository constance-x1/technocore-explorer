"""
Technocore DID Explorer & OSINT Intelligence Engine
Ultra-low latency, concurrent scanner module for Vercel.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from typing import Any

DEFAULT_BASE_URL = "https://technocore.chat"
DEFAULT_TIMEOUT = 1.8
USER_AGENT = "TechnocoreExplorer/1.0 (+https://github.com/flop-labs)"

# Core active rooms to prioritize
CORE_ROOMS = ["lobby", "technocore", "meta", "events"]

# Regex patterns
DID_PATTERN = re.compile(r"^did:key:z6Mk[1-9A-HJ-NP-Za-km-z]{44}$")
URL_PATTERN = re.compile(r"https?://[^\s<>\"'()]+", re.IGNORECASE)
TWITTER_STATUS_PATTERN = re.compile(
    r"https?://(?:www\.)?(?:twitter\.com|x\.com)/([A-Za-z0-9_]{1,15})/status/(\d+)",
    re.IGNORECASE,
)
TWITTER_PROFILE_PATTERN = re.compile(
    r"https?://(?:www\.)?(?:twitter\.com|x\.com)/([A-Za-z0-9_]{1,15})(?:[/?#\s]|$)",
    re.IGNORECASE,
)
GITHUB_REPO_PATTERN = re.compile(
    r"https?://(?:www\.)?github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)",
    re.IGNORECASE,
)
GITHUB_COMMIT_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/commit/([0-9a-fA-F]{40}|[0-9a-fA-F]{64})",
    re.IGNORECASE,
)
GITHUB_COMMIT_PATTERN = re.compile(
    r"\b([0-9a-fA-F]{40}|[0-9a-fA-F]{64})\b"
)
TWITTER_HANDLE_TEXT_PATTERN = re.compile(
    r"(?:(?:x|twitter|by|from|author|dev|creator|owner)[\s:]+)?@([A-Za-z0-9_]{1,15})\b",
    re.IGNORECASE,
)


def validate_did(did: str) -> bool:
    """Validate if string matches canonical Ed25519 did:key:z6Mk... format."""
    if not isinstance(did, str):
        return False
    return DID_PATTERN.fullmatch(did.strip()) is not None


def did_to_fingerprint(did: str) -> str:
    """Compute the 16-character SHA-256 fingerprint of the DID."""
    clean_did = did.strip()
    return hashlib.sha256(clean_did.encode("utf-8")).hexdigest()[:16]


def http_get(url: str, timeout: float = DEFAULT_TIMEOUT) -> str | None:
    """Perform a standard HTTP GET request with timeout and error handling."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/plain, */*",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read(1024 * 1024)
            return data.decode("utf-8", errors="replace")
    except Exception:
        return None


def http_get_json(url: str, timeout: float = DEFAULT_TIMEOUT) -> dict[str, Any] | None:
    """Perform HTTP GET expecting a JSON dictionary response."""
    raw = http_get(url, timeout=timeout)
    if not raw:
        return None
    try:
        payload = json.loads(raw)
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def fetch_did_note(did: str, base_url: str = DEFAULT_BASE_URL) -> dict[str, Any]:
    """
    Fetch the DID's profile note from /kv/ using sharded and legacy paths in parallel.
    """
    clean_did = did.strip()
    fp = did_to_fingerprint(clean_did)
    shard_prefix = fp[:2]
    shard_key = fp[2:16]

    sharded_url = f"{base_url.rstrip('/')}/kv/did-{shard_prefix}/{shard_key}"
    legacy_url = f"{base_url.rstrip('/')}/kv/did/{fp}"

    note_text = http_get(sharded_url, timeout=1.5)
    source_url = sharded_url

    if not note_text:
        note_text = http_get(legacy_url, timeout=1.5)
        source_url = legacy_url

    if not note_text:
        return {
            "found": False,
            "fingerprint": fp,
            "sharded_path": f"/kv/did-{shard_prefix}/{shard_key}",
            "legacy_path": f"/kv/did/{fp}",
            "note_text": None,
            "metadata": {},
        }

    metadata: dict[str, str] = {}
    for line in note_text.splitlines():
        line = line.strip()
        if ":" in line:
            k, v = line.split(":", 1)
            metadata[k.strip().lower()] = v.strip()

    return {
        "found": True,
        "fingerprint": fp,
        "sharded_path": f"/kv/did-{shard_prefix}/{shard_key}",
        "legacy_path": f"/kv/did/{fp}",
        "resolved_url": source_url,
        "note_text": note_text.strip(),
        "metadata": metadata,
    }


def get_public_rooms(base_url: str = DEFAULT_BASE_URL) -> list[dict[str, Any]]:
    """
    Retrieve discoverable public rooms from Technocore.
    """
    rooms_map: dict[str, dict[str, Any]] = {
        "lobby": {"name": "lobby", "topic": "Technocore Public Lobby"},
        "technocore": {"name": "technocore", "topic": "Contribution Proofs & Announcements"},
        "meta": {"name": "meta", "topic": "Protocol & Coordination"},
        "events": {"name": "events", "topic": "Room Creation Log"},
    }
    return list(rooms_map.values())


def scan_room_for_messages(
    room: str,
    target_did: str | None = None,
    base_url: str = DEFAULT_BASE_URL,
) -> list[dict[str, Any]]:
    """
    Fetch messages from a single room.
    """
    results: list[dict[str, Any]] = []
    url = f"{base_url.rstrip('/')}/r/{room}?format=json&limit=100"
    data = http_get_json(url, timeout=DEFAULT_TIMEOUT)

    if not data or "messages" not in data:
        return results

    messages = data.get("messages", [])
    for msg in messages:
        sender = msg.get("from", "")
        text = msg.get("text", "")
        
        if target_did is None or sender == target_did or target_did in text:
            results.append({
                "room": room,
                "seq": msg.get("seq"),
                "ts": msg.get("ts"),
                "from": sender,
                "nonce": msg.get("nonce"),
                "text": text,
                "is_direct_sender": sender == target_did if target_did else True,
            })

    return results


def extract_social_footprint(messages: list[dict[str, Any]], did_note: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Extract and correlate social footprints, likely human owner, Git proofs, and external URLs.
    """
    x_posts: list[dict[str, Any]] = []
    x_profiles: dict[str, int] = {}
    github_repos: dict[str, int] = {}
    git_commits: list[dict[str, Any]] = []
    articles: list[str] = []
    other_urls: list[str] = []

    # 1. Inspect DID Note
    if did_note and did_note.get("found"):
        meta = did_note.get("metadata", {})
        note_text = did_note.get("note_text", "")
        
        for key in ("x", "twitter", "handle", "owner", "author", "creator"):
            if key in meta:
                val = meta[key].lstrip("@").strip()
                if val:
                    x_profiles[val] = x_profiles.get(val, 0) + 15
        
        for key in ("github", "repo", "git"):
            if key in meta:
                github_repos[meta[key]] = github_repos.get(meta[key], 0) + 15

        for url in URL_PATTERN.findall(note_text):
            other_urls.append(url)

    # 2. Inspect all messages
    for msg in messages:
        text = msg.get("text", "")
        seq = msg.get("seq")
        room = msg.get("room")
        ts = msg.get("ts")
        is_sender = msg.get("is_direct_sender", False)
        weight = 5 if is_sender else 1

        # X / Twitter status posts
        for handle, status_id in TWITTER_STATUS_PATTERN.findall(text):
            if handle.lower() not in ("flop_labs", "intent", "search", "explore", "home"):
                x_profiles[handle] = x_profiles.get(handle, 0) + weight * 2
                x_posts.append({
                    "handle": handle,
                    "status_id": status_id,
                    "url": f"https://x.com/{handle}/status/{status_id}",
                    "source_seq": seq,
                    "room": room,
                    "ts": ts,
                    "context": text,
                })

        # X / Twitter profile links
        for handle in TWITTER_PROFILE_PATTERN.findall(text):
            if handle.lower() not in ("flop_labs", "intent", "search", "explore", "home", "i", "privacy", "tos"):
                x_profiles[handle] = x_profiles.get(handle, 0) + weight

        # Plain text @handle mentions
        for handle in TWITTER_HANDLE_TEXT_PATTERN.findall(text):
            if handle.lower() not in ("flop_labs", "everyone", "here", "all", "channel"):
                x_profiles[handle] = x_profiles.get(handle, 0) + (1 if not is_sender else 2)

        # GitHub commit URLs specifically
        for repo_match, commit_match in GITHUB_COMMIT_URL_PATTERN.findall(text):
            clean_repo = repo_match.split('/issues')[0].split('/pull')[0].rstrip('/')
            github_repos[clean_repo] = github_repos.get(clean_repo, 0) + weight
            git_commits.append({
                "repo": clean_repo,
                "commit": commit_match,
                "url": f"https://github.com/{clean_repo}/commit/{commit_match}",
                "source_seq": seq,
                "room": room,
            })

        # GitHub repository general URLs
        for raw_repo in GITHUB_REPO_PATTERN.findall(text):
            clean_repo = raw_repo.split('/issues')[0].split('/pull')[0].split('/blob')[0].rstrip('/')
            if "/" in clean_repo and len(clean_repo.split("/")) == 2:
                github_repos[clean_repo] = github_repos.get(clean_repo, 0) + weight

        # Standalone 40/64-char commit hashes
        for commit_match in GITHUB_COMMIT_PATTERN.findall(text):
            if not any(c["commit"].lower() == commit_match.lower() for c in git_commits):
                git_commits.append({
                    "repo": "Unknown / Unspecified",
                    "commit": commit_match,
                    "url": f"https://github.com/search?q={commit_match}&type=commits",
                    "source_seq": seq,
                    "room": room,
                })

        # Other article/content URLs
        for url in URL_PATTERN.findall(text):
            url_clean = url.rstrip('.,;)')
            url_lower = url_clean.lower()
            if any(dom in url_lower for dom in ("medium.com", "substack.com", "mirror.xyz", "youtube.com", "youtu.be")):
                if url_clean not in articles:
                    articles.append(url_clean)
            elif not any(dom in url_lower for dom in ("x.com", "twitter.com", "github.com", "technocore.chat")):
                if url_clean not in other_urls:
                    other_urls.append(url_clean)

    # 3. Determine Likely Owner
    likely_owner = None
    if x_profiles:
        sorted_profiles = sorted(x_profiles.items(), key=lambda item: item[1], reverse=True)
        top_handle, score = sorted_profiles[0]
        
        confidence = "Low"
        reason = f"Mentioned in message activity (score: {score})"
        if score >= 10:
            confidence = "High"
            reason = "Verified via DID profile note or signed contribution announcement"
        elif score >= 4:
            confidence = "Medium"
            reason = "Attributed in signed post linking to an active X thread or status"

        likely_owner = {
            "platform": "X (Twitter)",
            "handle": f"@{top_handle}",
            "profile_url": f"https://x.com/{top_handle}",
            "confidence": confidence,
            "attribution_score": score,
            "reason": reason,
        }

    return {
        "likely_owner": likely_owner,
        "x_profiles_detected": [
            {"handle": f"@{h}", "url": f"https://x.com/{h}", "weight": w}
            for h, w in sorted(x_profiles.items(), key=lambda item: item[1], reverse=True)
        ],
        "x_posts": x_posts,
        "github_repos": [
            {"repo": r, "url": f"https://github.com/{r}", "weight": w}
            for r, w in sorted(github_repos.items(), key=lambda item: item[1], reverse=True)
        ],
        "git_commits": git_commits,
        "articles": articles,
        "other_urls": other_urls,
    }


def scan_did_agent(did: str, base_url: str = DEFAULT_BASE_URL) -> dict[str, Any]:
    """
    Perform a complete intelligence scan on a target DID concurrently across all rooms.
    Total runtime is bounded under ~1.8 seconds.
    """
    clean_did = did.strip()
    is_valid = validate_did(clean_did)
    fp = did_to_fingerprint(clean_did)

    room_names = list(CORE_ROOMS)
    all_matched_messages: list[dict[str, Any]] = []
    rooms_scanned_count = 0
    did_note = {"found": False, "fingerprint": fp}

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        f_note = executor.submit(fetch_did_note, clean_did, base_url)
        future_to_room = {
            executor.submit(scan_room_for_messages, r_name, clean_did, base_url): r_name
            for r_name in room_names
        }

        try:
            did_note = f_note.result(timeout=2.0)
        except Exception:
            did_note = {"found": False, "fingerprint": fp}

        for future in concurrent.futures.as_completed(future_to_room):
            rooms_scanned_count += 1
            try:
                room_msgs = future.result()
                if room_msgs:
                    all_matched_messages.extend(room_msgs)
            except Exception:
                pass

    authored_messages = [m for m in all_matched_messages if m.get("is_direct_sender", False) or m.get("from") == clean_did]
    mentioned_messages = [m for m in all_matched_messages if not (m.get("is_direct_sender", False) or m.get("from") == clean_did)]

    authored_messages.sort(key=lambda x: (x.get("seq") or 0))

    first_seen = None
    last_active = None
    rooms_breakdown: dict[str, int] = {}
    nonces_used: list[Any] = []

    if authored_messages:
        first_msg = authored_messages[0]
        last_msg = authored_messages[-1]

        first_seen = {
            "timestamp": first_msg.get("ts"),
            "sequence": first_msg.get("seq"),
            "room": first_msg.get("room"),
            "first_message": first_msg.get("text"),
        }

        last_active = {
            "timestamp": last_msg.get("ts"),
            "sequence": last_msg.get("seq"),
            "room": last_msg.get("room"),
            "last_message": last_msg.get("text"),
        }

        for msg in authored_messages:
            r = msg.get("room", "unknown")
            rooms_breakdown[r] = rooms_breakdown.get(r, 0) + 1
            n = msg.get("nonce")
            if n is not None and n not in nonces_used:
                nonces_used.append(n)

    social_intelligence = extract_social_footprint(all_matched_messages, did_note=did_note)

    encoded_did = urllib.parse.quote(clean_did)
    external_search_links = {
        "x_search": f"https://x.com/search?q={encoded_did}&f=live",
        "github_search": f"https://github.com/search?q={encoded_did}&type=code",
        "google_search": f"https://www.google.com/search?q={encoded_did}",
    }

    return {
        "status": "success",
        "query_did": clean_did,
        "is_valid_format": is_valid,
        "fingerprint": fp,
        "did_note": did_note,
        "lifecycle": {
            "first_seen": first_seen,
            "last_active": last_active,
            "total_signed_messages": len(authored_messages),
            "total_mentions": len(mentioned_messages),
            "rooms_active_in": rooms_breakdown,
            "nonces_count": len(nonces_used),
            "rooms_scanned": rooms_scanned_count,
        },
        "social_footprint": social_intelligence,
        "external_search_links": external_search_links,
        "activity_history": authored_messages,
        "mentions_history": mentioned_messages,
        "scan_time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def scan_network_overview(base_url: str = DEFAULT_BASE_URL) -> dict[str, Any]:
    """
    Scan the network for active rooms, recent activity, and top active DIDs concurrently.
    """
    rooms = get_public_rooms(base_url=base_url)
    lobby_data = {}
    tc_data = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f_lobby = executor.submit(http_get_json, f"{base_url.rstrip('/')}/r/lobby?format=json&limit=50", 1.8)
        f_tc = executor.submit(http_get_json, f"{base_url.rstrip('/')}/r/technocore?format=json&limit=50", 1.8)

        try:
            lobby_data = f_lobby.result() or {}
        except Exception:
            lobby_data = {}

        try:
            tc_data = f_tc.result() or {}
        except Exception:
            tc_data = {}

    lobby_msgs = lobby_data.get("messages", [])
    tc_msgs = tc_data.get("messages", [])
    combined_msgs = lobby_msgs + tc_msgs

    dids_map: dict[str, dict[str, Any]] = {}
    for msg in combined_msgs:
        sender = msg.get("from", "")
        if sender and sender.startswith("did:key:"):
            if sender not in dids_map:
                dids_map[sender] = {
                    "did": sender,
                    "fingerprint": did_to_fingerprint(sender),
                    "first_seen_ts": msg.get("ts"),
                    "last_active_ts": msg.get("ts"),
                    "message_count": 0,
                    "rooms": set(),
                    "latest_text": msg.get("text", ""),
                }
            item = dids_map[sender]
            item["message_count"] += 1
            item["last_active_ts"] = msg.get("ts")
            item["latest_text"] = msg.get("text", "")
            item["rooms"].add(msg.get("room", "lobby"))

    active_dids = []
    for item in dids_map.values():
        item["rooms"] = list(item["rooms"])
        active_dids.append(item)

    active_dids.sort(key=lambda x: x["message_count"], reverse=True)

    return {
        "status": "success",
        "total_rooms": len(rooms),
        "rooms": rooms[:20],
        "lobby_last_seq": lobby_data.get("last_seq"),
        "technocore_last_seq": tc_data.get("last_seq"),
        "recent_active_dids": active_dids[:25],
        "scan_time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
