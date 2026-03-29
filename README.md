# Wikipedia Category Scraper

Turn Wikipedia category page into structured JSON data.
The pipeline fetches every article in a category, pulls the infobox and body text from each page,
and uses Google Gemini to extract whatever fields you define into a clean, typed JSON output.

**Example use case:** scraping Abu Dhabi tourist attractions from
[`Category:Tourist_attractions_in_Abu_Dhabi`](https://en.wikipedia.org/wiki/Category:Tourist_attractions_in_Abu_Dhabi)
to produce a structured dataset of attraction names, types, locations, and opening years.

---

## Project structure

```
ad_scraper/
├── scraper.py        # Core scraping functions (category → pages → raw JSON)
├── api.py            # Gemini AI extraction (raw JSON → typed structured data)
├── server.py         # FastAPI backend — exposes the pipeline as REST endpoints
├── requirements.txt
└── data/
    ├── targets.csv   # Relative Wikipedia URLs collected from the category page
    ├── pages/        # Raw HTML saved per page (used for offline re-scraping)
    ├── raw.json      # Infobox + body text extracted from each page
    └── extracted.json  # Final structured output after AI extraction
```

---

## Requirements

- Python 3.10+
- Node.js 18+ (for the React frontend)
- A [Google AI Studio](https://aistudio.google.com/) API key

### Install Python dependencies

```bash
pip install -r requirements.txt
```

### Set up the Gemini API key

The `api.py` module reads your key from the `GOOGLE_API_KEY` environment variable:

```bash
# Windows (PowerShell)
$env:GOOGLE_API_KEY = "your-key-here"

# macOS / Linux
export GOOGLE_API_KEY="your-key-here"
```

---

## Running the app

The project ships with a FastAPI backend and a Vite + React frontend that walks you through
the full pipeline in three steps.

### 1. Start the FastAPI backend

```bash
uvicorn server:app --reload
```

The API will be available at `http://localhost:8000`.  
Interactive docs are at `http://localhost:8000/docs`.

### 2. Start the React frontend

```bash
cd frontend
npm install   # first time only
npm run dev
```

Open `http://localhost:5173` in your browser.

### 3. Using the UI

| Step | What it does |
|------|-------------|
| **Scrape Category** | Paste a Wikipedia category URL and click *Scrape* to collect target page links into `data/targets.csv` |
| **Scrape Pages** | Fetches each target page, saves raw HTML to `data/pages/`, and writes infobox + body text to `data/raw.json` |
| **Extract with AI** | Define custom fields (name + description), click *Extract Data* — Gemini fills each field for every entry and saves the result to `data/extracted.json` |

**Abu Dhabi example URL to paste in Step 1:**
```
https://en.wikipedia.org/wiki/Category:Tourist_attractions_in_Abu_Dhabi
```

Example fields to define in Step 3:

| Field name | Description |
|---|---|
| `name` | The official name of the attraction |
| `place_type` | Category of place, e.g. Museum, Theme Park, Mosque |
| `location` | The island or district where it is located |
| `open_year` | The year the attraction opened |

---

## Scraper function reference (`scraper.py`)

### `scrapeURL(url: str) -> list[str] | None`

Fetches a Wikipedia **category** page and returns a list of relative page paths
(e.g. `["/wiki/Ferrari_World", "/wiki/Sheikh_Zayed_Grand_Mosque", ...]`).

- Targets the `#mw-pages` container and filters links to `/wiki/` paths only.
- Returns `None` and prints an error if the page cannot be fetched or parsed.

```python
hrefs = scrapeURL("https://en.wikipedia.org/wiki/Category:Tourist_attractions_in_Abu_Dhabi")
```

---

### `scrapePage(url: str, session=None) -> dict | None`

Fetches a single Wikipedia **article** page and returns a dictionary with:

| Key | Value |
|-----|-------|
| `raw_html` | The relative URL used to fetch the page |
| `name` | Page title from `<span class="mw-page-title-main">` |
| `infobox_text` | Plain text extracted from the infobox table (or `None` if absent) |
| `body_text` | Concatenated paragraph text from the article body |

- Saves the full prettified HTML to `data/pages/<page_name>.csv` for offline reuse.
- Accepts an optional `session` to reuse a persistent connection across many pages.
- Returns `None` and prints a warning if the page cannot be fetched.

```python
entry = scrapePage("/wiki/Ferrari_World")
# {"raw_html": "/wiki/Ferrari_World", "name": "Ferrari World", "infobox_text": "...", "body_text": "..."}
```

---

### `scrapeFile(url: str) -> dict | None`

Parses a **locally saved** HTML file (from `data/pages/`) without making any network
request. Useful for re-extracting data after changing the parsing logic.

Returns the same dictionary shape as `scrapePage`.

```python
entry = scrapeFile("data/pages/Ferrari_World.csv")
```

---


## API reference (`server.py`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/scrape-category` | Body: `{"url": "..."}` — scrapes the category and writes `targets.csv` |
| `GET` | `/api/targets` | Returns the list of collected target URLs |
| `POST` | `/api/scrape-pages` | Scrapes all targets, writes `raw.json` |
| `GET` | `/api/results` | Returns contents of `raw.json` |
| `POST` | `/api/extract` | Body: `{"fields": [{"name": "...", "description": "..."}]}` — runs AI extraction |
| `GET` | `/api/extracted` | Returns contents of `extracted.json` |
