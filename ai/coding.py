from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

model_name = "deepseek-ai/deepseek-coder-6.7b-instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", torch_dtype="auto")

generator = pipeline("text-generation", model=model, tokenizer=tokenizer)

prompt = "### Task: Write a Python function to check if a number is prime.\n```python\n"
response = generator(prompt, max_new_tokens=200, temperature=0.7)
print(response[0]['generated_text'])
