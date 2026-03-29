import asyncio
import json
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, create_model

from api import extractData
from scraper import scrapeURL, scrapePage, _create_session

app = FastAPI(title="Wikipedia Scraper API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class URLRequest(BaseModel):
    url: str


class FieldSchema(BaseModel):
    name: str
    description: str


class ExtractRequest(BaseModel):
    fields: List[FieldSchema]


#scrape category for target urls
@app.post("/api/scrape-category")
async def scrape_category(request: URLRequest):
    try:
        results = await asyncio.to_thread(scrapeURL, request.url)
        targets_path = Path("data/targets.csv")
        count =0
        with open(targets_path, "w", encoding="utf-8") as targets:
            for href in results:
                targets.write(f"{href}\n")
                count += 1
        return {"message": "Category scraped successfully", "targets_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#get target urls
@app.get("/api/targets")
async def get_targets():
    targets_path = Path("data/targets.csv")
    if not targets_path.exists():
        return {"targets": [], "count": 0}
    with open(targets_path, "r", encoding="utf-8") as f:
        targets = [line.strip() for line in f if line.strip()]
    return {"targets": targets, "count": len(targets)}


#scrape pages for raw data
@app.post("/api/scrape-pages")
async def scrape_pages():
    targets_path = Path("data/targets.csv")
    if not targets_path.exists():
        raise HTTPException(status_code=404, detail="No targets found. Scrape a category first.")

    with open(targets_path, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    if not urls:
        raise HTTPException(status_code=400, detail="Targets file is empty.")

    session = _create_session()
    data = []
    for url in urls:
        result = await asyncio.to_thread(scrapePage, url, session)
        if result:
            data.append(result)

    raw_path = Path("data/raw.json")
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    return {"message": f"Scraped {len(data)} pages", "count": len(data)}


#get scraped pages
@app.get("/api/results")
async def get_results():
    raw_path = Path("data/raw.json")
    if not raw_path.exists():
        return {"results": [], "count": 0}
    with open(raw_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {"results": data, "count": len(data)}


#extract data from scraped pages
@app.post("/api/extract")
async def extract_data(request: ExtractRequest):
    try:
        if not request.fields:
            raise HTTPException(status_code=400, detail="At least one field is required.")

        raw_path = Path("data/raw.json")
        if not raw_path.exists():
            raise HTTPException(status_code=404, detail="No raw data. Scrape pages first.")

        with open(raw_path, "r", encoding="utf-8") as f:
            items = json.load(f)

        field_defs = {
            f.name: (str, Field(description=f.description))
            for f in request.fields
        }
        DynamicModel = create_model("FieldData", **field_defs)

        results = await asyncio.to_thread(extractData, items, DynamicModel)
        extracted_path = Path("data/extracted.json")
        with open(extracted_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4)

        return {"message": f"Extracted {len(results)} entries", "count": len(results), "results": results}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/extracted")
async def get_extracted():
    extracted_path = Path("data/extracted.json")
    if not extracted_path.exists():
        return {"results": [], "count": 0}
    with open(extracted_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {"results": data, "count": len(data)}
