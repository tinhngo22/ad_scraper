from google import genai
import time
from google.genai import errors,types
from pydantic import BaseModel, Field
from typing import List, Optional
import pathlib
import json


filepath = pathlib.Path('./data/raw.json')
with open(filepath, 'r') as f:
    file = json.load(f)



class Attraction(BaseModel):
    name: str = Field(description="The official name of the attraction")
    place_type: str = Field(description="The category of place (e.g., Museum, Theme Park, Mosque)")
    containedInPlace: str = Field(description="The larger area or island where it is located (e.g., Saadiyat Island, Yas Island)")
    open_year: str = Field(description="The year when the attraction opened")

client = genai.Client()


for item in file:
    prompt = f"Here is the raw data content:\n{item}.Extract the JSON object for the attraction. If fields are missing, use 'NA'."
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents = prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": Attraction.model_json_schema(),
            },
        )

        attraction = Attraction.model_validate_json(response.text)

        print(attraction)
        
    except errors.ServerError as e:
        raise e
