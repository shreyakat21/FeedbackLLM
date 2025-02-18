import openai

openai.api_key = "your-openai-api-key"
response = openai.Completion.create(
    model="gpt-3.5-turbo",
    prompt="Hello, world!",
    max_tokens=5
)
print(response.choices[0].text.strip())