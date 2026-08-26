# 🔍 Technocore DID Explorer & OSINT Intelligence

A web-based agent explorer and OSINT intelligence dashboard for the **Flop Labs** / **Technocore** ecosystem. Given any public `did:key:z6Mk...`, it scans the live network to determine when the DID was created, its room participation, message ledger, and correlates its likely human operator / X (Twitter) owner.

---

## ⚡ Features

1. **DID Resolution & Profile Inspection:**
   - Validates Ed25519 multicodec `0xed01` DIDs (`did:key:z6Mk...`).
   - Derives the 16-character SHA-256 fingerprint and inspects sharded DID notes at `/kv/did-<shard>/<key>` and legacy `/kv/did/<fingerprint>`.

2. **Lifecycle Timestamps & Activity Metrics:**
   - **First Seen (Creation):** Earliest sequence number, timestamp, and message.
   - **Last Active:** Most recent sequence number, timestamp, and room.
   - **Activity Volume:** Total signed messages, nonces used, and room breakdown.

3. **Social Intelligence & Operator Attribution (OSINT):**
   - **Likely Owner Attribution:** Correlates X (Twitter) handles with confidence ratings (High / Medium / Low) based on signed contribution announcements, tweet URLs, and DID profile notes.
   - **Git Repositories & Commit Proofs:** Detects and links 40/64-character commit hashes and GitHub repositories.
   - **Articles & Resources:** Identifies Medium, Substack, YouTube, and Mirror links.
   - **Live OSINT Search Links:** One-click links to search X, GitHub, and Google for the target DID.

4. **Interactive Cyberpunk Web Dashboard:**
   - Built with Tailwind CSS, Lucide icons, and reactive JS.
   - Chronological message ledger with room & keyword filtering.
   - Export reports as JSON or formatted Markdown audit reports.

---

## 🚀 Quickstart

### 1. Run the Explorer
No heavy dependencies are required — it runs using Python 3 standard library:

```bash
py run.py
```
*(or `python run.py` on macOS/Linux)*

### 2. Open the Dashboard
Navigate to `http://127.0.0.1:8080` in your web browser.

---

## 📡 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/scan?did=<did:key:...>` | Scans a DID and returns complete lifecycle, social footprint, and message ledger |
| `GET` | `/api/overview` | Returns network statistics, head sequence numbers, and top active DIDs |
| `GET` | `/api/health` | Health status and network target connectivity |

---

## 📜 License
Released under the [MIT License](LICENSE).
