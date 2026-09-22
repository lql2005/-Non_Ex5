from pathlib import Path
from ollama import chat
import json
import re

MODEL = "qwen3:8b"
KNOWLEDGE_DIR = Path("knowledge")
STATE_FILE = Path("state.json")

question = """
I changed my university password this morning.
Now my Windows laptop won't connect to campus Wi-Fi,
but my phone still works.
"""

## WRITE ##
service_status = {
    "wifi": "operational"
}

state = {
    "problem": question,
    "wi_fi status": "operational",
    "wi-fi_check": True
}

with open("state.json", "w") as file:
    json.dump(
        state,
        file,
        indent=2
    )

with open("state.json", "r") as file:
    state = json.load(file)

print(state)


## SELECT CONTEXT FILES BASED ON QUESTION
## Create the function that takes the student's question, takes some keywords and chooses the relevant files from the knowledge base. Return a list of the selected files.
## For example, if the question has the kyeword "print" or "printer", then the function should return the file "knowledge/printer_setup.txt" in a list.
def select_context(question):
     q = question.lower()

     keyword_map = {
          "wi-fi": ["wifi_setup.txt", "service_status.txt", "password_changes.txt"],
        "wifi": ["wifi_setup.txt", "service_status.txt", "password_changes.txt"],
        "eduroam": ["wifi_setup.txt", "service_status.txt"],
        "network": ["wifi_setup.txt", "service_status.txt"],
        "password": ["password_changes.txt", "wifi_setup.txt", "email_setup.txt", "vpn.txt"],
        "email": ["email_setup.txt"],
        "vpn": ["vpn.txt"],
        "print": ["printing.txt"],
        "printer": ["printing.txt"],
        "projector": ["classroom_projectors.txt"],
        "display": ["classroom_projectors.txt"],
     }

     selected = set()
     for keyword, files in keyword_map.items():
        if keyword in q:
            selected.update(files)

     if any(k in q for k in ["wi-fi", "wifi", "eduroam", "network"]):
        selected.add("service_status.txt")

     if "password" in q or "change" in q:
        selected.add("password_changes.txt")

     if not selected:
        selected = {p.name for p in KNOWLEDGE_DIR.glob("*.txt")}

     return [str(KNOWLEDGE_DIR / name) for name in sorted(selected)]

selected_files = select_context(question)

## READ SELECTED FILES and add their contents to the context variable.
context = ""

for filename in selected_files:
    context += Path(filename).read_text(encoding="utf-8")
    context += "\n\n"
    
## 
## COMPRESS CONTEXT
## Add logic to compress the context from above by calling Qwen with "context" and the "question" as the parameter
## The response from Qwen should be the compressed context. Store it in a variable called "compressed_context" 

def compress_context(context, question):
     response = chat(
        model=MODEL,
        think=False,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a context compression assistant. "
                    "Extract only the facts from the provided context that are relevant to the user's question. "
                    "Return concise bullet points. Do not add outside information."
                ),
            },
            {
                "role": "user",
                "content": f"Question:\n{question}\n\nContext:\n{context}",
            },
        ],
    )
     return response.message.content


compressed_context = compress_context(context, question)



## Print the length of the compressed context
print(len(compressed_context))

## Now, call Qwen again with the compressed context and the student's question. Store the response in a variable called "response" and print the response from Qwen.
## Ensure the model produces a structured output 


ai_response = chat(
    model=MODEL,
    think=False,
    format="json",
    messages=[
        {
            "role": "system",
            "content": (
                "You are a university IT support assistant. "
                "Use ONLY the compressed context and the student question. "
                "Return valid JSON with exactly these keys: "
                '"diagnosis" (string), "likely_cause" (string), '
                '"steps" (array of strings), "references" (array of strings), '
                '"status" (string: "resolved" or "needs_follow_up"). '
            ),
        },
        {
            "role": "user",
            "content": f"Question:\n{question}\n\nCompressed context:\n{compressed_context}",
        },
    ],
)


print(ai_response.message.content)

## WRITE the above output in an artifact called "state"
state = {
    "problem": question,
    "diagnostic_context": {
        "device": "Windows laptop",
        "wifi_status": "operational",
        "selected_files": selected_files,
        "compressed_context": compressed_context,
    },
    "report_context": {
        "total_wifi_cases": 37,
        "resolved_cases": 29,
        "unresolved_cases": 8,
    },
    "answer": ai_response.message.content,
}

with open("state.json", "w") as file:
    json.dump(state, file, indent=2)
## Update the rest of the code so that it uses the "state" artifact as part of the context. 
## It is important to ensure that the model uses only the relevant parts from the "state" artifact and not the entire artifact.
## For this, you may have to think of a good structure for the "state" artifact and how to use it in the context.

with open("state.json", "r") as file:
    saved_state = json.load(file)

# ISOLATE: only use the part of the state relevant to the diagnostic task
diagnostic_context = {
    "problem": saved_state["problem"],
    "diagnostic_context": saved_state["diagnostic_context"],
}

print("\nRelevant diagnostic state used as context:")
print(json.dumps(diagnostic_context, indent=2))
