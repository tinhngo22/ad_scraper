from google import genai
import time
from google.genai import errors,types
from pydantic import BaseModel, Field
from typing import List, Optional
import pathlib
import json

def extractData(file, FieldData: BaseModel):
    client = genai.Client()
    results = []

    for item in file:
        prompt = f"Here is the raw data content:\n{item}.Extract the JSON object for the field data. If fields are missing, use 'NA'."
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents = prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": FieldData.model_json_schema(),
                },
            )

            data = FieldData.model_validate_json(response.text)
            results.append(data.model_dump())
            print(data)
            
        except errors.ServerError as e:
            raise e
    return results