# imports
from google import genai


# GenAI integration

# This is my personal API key (ShernFai)
client = genai.Client(api_key="AIzaSyBR-BJNTA4HSiK3b0iKmz-NZnVvSbeXCMw")
response = client.models.generate_content(
    model='gemini-2.5-flash', contents= "Write me a short poem about coffee.")
print(response.text)
