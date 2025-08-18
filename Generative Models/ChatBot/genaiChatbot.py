# imports
import base64
import os
from google import genai
from google.genai import types

# GenAI integration

# To run this code you need to install the following dependencies:
# pip install google-genai


def generate():
    client = genai.Client(api_key="AIzaSyBR-BJNTA4HSiK3b0iKmz-NZnVvSbeXCMw")
    model = "gemini-2.5-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""Write me a short poem about coffee."""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config = types.ThinkingConfig(
            thinking_budget=-1,
        ),
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        print(chunk.text, end="")

if __name__ == "__main__":
    generate()
