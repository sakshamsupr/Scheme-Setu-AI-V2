# Scheme Setu AI V2 — Full local prototype

Scheme Setu AI is a responsive Bharat-first fintech-style web prototype for discovering government schemes, understanding eligibility, planning finance, preparing documents, finding relevant partners, and navigating an application roadmap through a multilingual AI Copilot.

## V2 capabilities

- Responsive React + Vite experience for laptop, tablet and mobile.
- Bharat/FinTech visual system using a violet + saffron + green accent direction with navy/neutral surfaces.
- Multiple generated visual assets for rural entrepreneurship, women-led enterprises, artisans, retail and mobility.
- Custom Scheme Setu AI logo artwork used in the shell and brand sections.
- Floating AI Copilot with profile-aware conversation, RAG retrieval, deterministic navigation actions, and optional Gemini generation.
- Improved browser voice input with interim transcript, listening state, selected Indian language locale, and text-to-speech controls.
- Global multilingual UI selector for English, Hindi, Hinglish, Bengali, Marathi, Tamil, Telugu, Gujarati, Kannada, Malayalam and Punjabi.
- Scheme cards with a "Why this scheme?" explanation block and evidence/case-study layer.
- Eligibility Gap Detector that compares the saved profile with the rule-based eligibility signals.
- Interactive Application Roadmap in the sidebar with scheme selector and browser-persisted step completion.
- Functional notification bell with scheme/application/deadline updates plus user reminders stored locally in the browser.
- Financial calculator with scheme selection, live scenario recalculation, repayment-mix donut visualization and interactive comparison bars.
- Partner Locator with optional scheme selector, so a user can search by location without selecting a scheme.
- Generated images are page-specific rather than one repeated hero image.
- Existing 52 seed schemes + 277 partner records retained as demo/seed data.

## Local run — Windows PowerShell

### Backend

```powershell
cd "C:\path\to\Scheme-Setu-AI-V2-Full"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
Copy-Item .env.example .env
python -m uvicorn backend.app.main:app --reload --port 8000
```

### Frontend

Open a second terminal:

```powershell
cd "C:\path\to\Scheme-Setu-AI-V2-Full\frontend"
npm install
npm run dev
```

Open the Vite URL printed in the terminal, typically `http://localhost:5173/` or the next available port.

## Optional Gemini

Put your key in `.env`:

```env
GEMINI_API_KEY=your_key_here
```

The app still runs without the key using local retrieval and deterministic Copilot responses. When Gemini is configured, the retrieved context is supplied to the model for grounded answers.

## Important data boundaries

The supplied scheme and partner files are still seed/demo data. In particular, the partner rows include demo-style values and example URLs from the original prototype. Replace them with the junior team's verified dataset before presenting them as live institutional data.

The notification bell is fully functional for the local prototype, but live government change ingestion requires an official source/API/feed. The UI and API contract are ready for that integration.

Live application tracking remains an authorized integration point; the roadmap and reminder UX are implemented without fabricating partner-side status.

## Verification performed

- Backend Python compilation passed.
- Existing smoke test passed: 52 schemes, 277 partners, personalized matching works.
- Copilot tests passed.
- FastAPI `/health`, `/stats`, `/notifications` endpoints returned HTTP 200 in a local server run.
- `/eligibility-gap` and `/copilot` were exercised through the FastAPI test client.

The sandbox could not complete a final browser build because npm registry access is not available there; run `npm install` + `npm run dev` on the target Windows machine to perform the final frontend build/run check.

## Final consolidated V2 notes
- Partner radius supports up to 300 km.
- Gemini model default is `gemini-3.8-flash`; put your own API key in `.env`.
- The notification feed is file-backed in `data/runtime/updates.json`; live government push requires an authorized feed/API.
- AI chat history is sanitized to `{role, content}` before API calls.
- Hero imagery uses a dark contrast overlay to keep text accessible.
