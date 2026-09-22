from pathlib import Path
from ollama import chat

MODEL = "qwen3:8b"

question = """
I changed my university password this morning.
Now my Windows laptop won't connect to campus Wi-Fi,
but my phone still works.
"""

selected_files = [
    ##Use only the files that are relevant to the question.
    "knowledge/wifi_setup.txt",
    "knowledge/password_changes.txt",
    "knowledge/service_status.txt",
]


context = ""

## Write a for loop to go through all the files in selected_files and read their contents into the context variable.
for filename in selected_files:
    context += Path(filename).read_text(encoding="utf-8")
    context += "\n\n"

## Call Qwen with the student's question and the context you created above.
response = chat(
    model=MODEL,
    think=False,
    messages=[
        {
            "role": "system",
            "content": "You are a university IT support assistant. Answer using only the provided context."
        },
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nStudent question:\n{question}"
        }
    ]
)


print(
    "Context characters:",
    len(context)
)
print(response.message.content)