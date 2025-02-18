import openai

openai.api_key = "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"
response = openai.Completion.create(
    model="gpt-3.5-turbo",
    prompt="Hello, world!",
    max_tokens=5
)
print(response.choices[0].text.strip())