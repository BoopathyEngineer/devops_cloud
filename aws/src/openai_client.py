from openai import OpenAI
import httpx

openai_key = ""
organization_key = ""
# Configure an http_client
http_client = httpx.Client(base_url="http://localhost:3000")
client = OpenAI(
    organization='',
    api_key = openai_key,
    http_client=http_client
)