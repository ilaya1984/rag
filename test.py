import requests
# API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"
# headers = {"Authorization": "Bearer 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"}

# payload = {
#     "inputs": "Explain quantum computing in simple terms.",
#     "parameters": {"max_new_tokens": 100, "temperature": 0.7}
# }

# response = requests.post(API_URL, headers=headers, json=payload)
# print(response.text)
# print(response.json()[0]["generated_text"])

# from huggingface_hub import HfApi

# api = HfApi()
# for m in api.list_models(filter="text-generation", inference_provider="together", limit=10):
#     print(m.modelId)

from huggingface_hub import InferenceClient

model_choices = [
    "meta-llama/Llama-3.3-70B-Instruct",
    "meta-llama/Llama-3.2-3B-Instruct",
    "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "deepseek-ai/DeepSeek-R1",
    "deepseek-ai/DeepSeek-V3",
    "Qwen/Qwen2.5-7B-Instruct",
    "Qwen/Qwen2.5-Coder-32B-Instruct",
    "nvidia/Llama-3.1-Nemotron-70B-Instruct-HF"
]


client = InferenceClient(
    provider="together",
    model="mistralai/Mistral-7B-Instruct-v0.3",  # pick any from your printed list
    api_key="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"
)

response = client.chat_completion(
    messages=[{"role": "user", "content": "write simple python hello word code."}],
    max_tokens=100
)
print(response.choices[0].message.content)
