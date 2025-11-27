import dspy

lm = dspy.LM(model='ollama/phi3.5:3.8b-mini-instruct-q4_K_M', api_base='http://localhost:11434')
dspy.settings.configure(lm=lm)

print("Sending request...")
response = lm("Say hello!")
print("Response:", response)
