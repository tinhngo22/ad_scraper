# Wikipedia category scraper

This project scrapes pages from a specific Wikipedia category
(`https://en.wikipedia.org/wiki/Category:Tourist_attractions_in_Abu_Dhabi`),
extracts infobox text for each attraction, writes the results to JSON, and
optionally post‑processes the raw text with a Gemini model to get a clean,
typed JSON object.

## Project structure

- `scraper.py` – scrapes the category and individual pages and builds
  `data/raw.json` with extracted infobox text.
- `api.py` – uses Google Gemini (via `google-genai`) to turn a raw entry from
  `data/raw.json` into a structured `Attraction` object.
- `data/` – local data directory (ignored by Git) that will contain:
  - `data/targets.csv` – list of relative Wikipedia page URLs from the category.
  - `data/pages/` – raw HTML for each page (one file per attraction).
  - `data/raw.json` – list of JSON objects with fields like
    `raw_html`, `name`, and `infobox_text`.

## Requirements

- Python 3.10+ (recommended)
- A Google AI Studio / Gemini API key

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Setting up the Gemini API key (local environment)

The `api.py` script uses the `google-genai` client. By default it picks up your
Gemini API key from the `GOOGLE_API_KEY` environment variable.


## How to run the scraper (Wikipedia → JSON)

The main scraping pipeline is implemented in `scraper.py` and is designed
around the category:

`https://en.wikipedia.org/wiki/Category:Tourist_attractions_in_Abu_Dhabi`

The flow is:

1. Run scraper.py: scrape data from category page and stored in data folder. Raw html files are stored for rescraping.
2. Run api.py: extract data into json format

