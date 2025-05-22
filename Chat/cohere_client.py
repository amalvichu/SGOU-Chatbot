import cohere

co = cohere.Client("gh2mx5fHOKRx3M7sdfDE1c32tckBCfowuT9scRS2")  
def generate_response(prompt):
    response = co.generate(
        model='command-xlarge-nightly',
        prompt=prompt,
        max_tokens=150,
        temperature=0.7,
        stop_sequences=["--"]
    )
    return response.generations[0].text.strip()
