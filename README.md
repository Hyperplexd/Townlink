# TownLink | Πλατφόρμα Διακλαδικής Διαλειτουργικότητας & Έξυπνης Δρομολόγησης
### City of Athens & Crowdpolicy Hackathon Pilot MVP

**TownLink** solves the ultimate civic fragmentation problem in Athens: citizens today need **4 different apps** on their phone (Novoville for the Municipality, EydApp for water/manholes, MyDEDDIE for power poles, and the Region of Attica form for metropolitan avenues). 

TownLink acts as an intelligent **Interoperability Broker & Vision AI Triage Engine** that processes citizen incident reports (photo + GPS) and automatically splits and dispatches standardized JSON payloads to the correct agency while querying live Greek Open Data APIs (OASA Telematics, Mitos Registry, and Athens GIS).

---

## Key Features & Architecture

1. **Multi-Label Vision AI Triage (`google-genai`):** Detects multiple distinct infrastructure problems in a single photo (e.g., broken sidewalk tiles next to a leaking EYDAP manhole) and draws 2D bounding boxes.
2. **GIS & OSM Jurisdiction Routing:** Queries live **City of Athens GIS (`gis.cityofathens.gr`)** and **OpenStreetMap Overpass API** to distinguish municipal streets from major metropolitan avenues belonging to the **Region of Attica**.
3. **OASA Telematics Proximity Layer (`telematics.oasa.gr`):** Checks if a hazard is within 30 meters of a bus stop, automatically escalating the Smart SLA (`HIGH_CRITICAL_TRANSIT_HUB`).
4. **Mitos Administrative Knowledge (`api.mitos.gov.gr`):** Fetches official administrative procedures and required documents for citizens.
5. **Live Interoperability Webhooks:** Dispatches real Open311 GeoReport v2 and utility JSON payloads with automated feedback receipts.
6. **Executive Municipality View:** Interactive Leaflet map of Athens displaying live clustered tickets across the 7 Municipal Communities (`1η–7η Δημοτική Κοινότητα`) and AI Executive Briefings.

---

## Installation

1. Set one model key in `.env`. Vision and reasoning both use whichever key has a value (`GEMINI_API_KEY` or `OPENROUTER_API_KEY`):
   ```bash
   cp .env.example .env
   # GEMINI_API_KEY=...   or   OPENROUTER_API_KEY=sk-or-v1-...
   ```
   
2. Install Backend & Frontend:
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt

   # Frontend (in another terminal)
   cd frontend
   npm install
   ```

## Quick Start & Local Execution

1. Start Backend & Frontend:
   ```bash
   # Open one terminal for Backend
   cd backend; uvicorn main:app --reload --port 8000

   # Frontend (in another terminal)
   cd frontend; npm run dev
   ```

2. Open `http://localhost:5173` in your browser.
