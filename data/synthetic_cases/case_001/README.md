# Synthetic Case 001 - Operation Cygnus (ARGUS Benchmark Dataset)

This dataset is a completely synthetic, benign, and non-sensitive child-protection cyber investigation benchmark created for the **ARGUS (Agentic Investigation Backbone)** proof-of-concept.

---

## 🔒 Safety & Ethical Integrity Verification
- **No Real Individuals**: All names, handle tags, phone numbers, IP addresses, device serials, and locations are 100% fictional.
- **No CSAM / No Explicit Content**: Evidence contains zero abusive, sexually explicit, or harmful text or imagery.
- **Harmless Demonstration**: Created exclusively to evaluate technical entity extraction, EXIF parsing, cross-source correlation, and timeline reconstruction.

---

## 📁 Dataset Directory Structure

```
data/synthetic_cases/case_001/
├── case.json                 # Case metadata and investigation goals
├── chats.json                # Synthetic chat logs between handles (@CyberHawk, @NightOwl)
├── social_messages.json      # Public social media posts and direct messages
├── gps.csv                   # Synthetic device location tracking logs (Lat/Lon/Timestamp)
├── calls.csv                 # Cellular call detail records (CDR)
├── devices.json              # Device specs (IMEI, MAC, primary accounts)
├── events.json               # Chronological event log
├── evidence_photo_01.jpg     # Synthetic photo artifact with EXIF metadata
├── evidence_photo_02.jpg     # Synthetic photo artifact with EXIF metadata
├── screenshot_chat_01.png    # Synthetic chat screenshot for OCR evaluation
└── README.md                 # Case overview and correlation map
```

---

## 🧩 Planted Cross-Source Correlations & Relationship Map

The evidence intentionally distributes clues across multiple heterogeneous data sources that ARGUS is built to discover:

1. **Account A ↔ Device D1**:
   - `@CyberHawk` is linked to Phone Number `+1-555-0199` in `chats.json` and registered as primary user of `DEV-SPH-9001` (Samsung Galaxy S22) in `devices.json`.

2. **Device D1 ↔ Location L1**:
   - `DEV-SPH-9001` records GPS coordinate `37.774929, -122.419416` (San Francisco Dock 14) at timestamp `2026-08-10T14:00:00Z` in `gps.csv`.

3. **Image I1 ↔ Device D1**:
   - `evidence_photo_01.jpg` metadata links creation to camera model `Samsung Galaxy S22` (`DEV-SPH-9001`) at `2026-08-10T14:05:30Z`.

4. **Chat C1 ↔ Location L1**:
   - `chats.json` message `CHAT-1001` contains explicit text coordinates `37.774929, -122.419416` matching `LOC-SF-01`.

5. **Call C1 ↔ Account A**:
   - `calls.csv` record `CALL-5002` logs direct call between `+1-555-0199` (`@CyberHawk`) and `+1-555-0144` (`@NightOwl`).

6. **Event E1 ↔ Shared Timestamp**:
   - Timestamp `2026-08-10T14:05:30Z` is shared across `chats.json`, `gps.csv`, `calls.csv`, `events.json`, and image EXIF metadata.

---

## 🎯 Architecture Capabilities Demonstrated

| Capability | Evidence Artifact Used | Expected ARGUS Output |
| :--- | :--- | :--- |
| **1. Content Analysis** | `chats.json`, `social_messages.json` | Co-occurrence of `@CyberHawk` and `@NightOwl` |
| **2. Metadata Extraction** | `evidence_photo_01.jpg` EXIF | GPS `37.774929, -122.419416`, Device `Samsung Galaxy S22` |
| **3. Entity Extraction** | `chats.json`, `calls.csv` | Extract handles (`@CyberHawk`), phone (`+1-555-0199`), IP (`192.168.1.105`) |
| **4. Cross-source Correlation** | All files | Knowledge graph edges: `COMMUNICATED_WITH`, `GEOTAGGED_AT`, `REGISTERED_TO` |
| **5. Timeline Reconstruction** | `events.json`, timestamps | Chronological event sequence spanning 13:45Z to 14:20Z |
| **6. Evidence Gap Detection** | `calls.csv` vs `gps.csv` | Detect gap between cell tower 415-OAK and GPS ping at 14:15Z |
| **7. Lead Generation** | Knowledge graph + findings | Candidate lead connecting `@CyberHawk` to `DEV-SPH-9001` and `LOC-SF-01` |
| **8. Explainability** | Proposed lead payloads | Provenance chain linking findings back to exact source file and line |
