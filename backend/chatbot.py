import os
import requests

HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"
HF_MODEL = "google/gemma-2-2b-it:fastest"

SYSTEM_PROMPT = """
You are MediMind AI, a health-education assistant.

Your role is limited to general, understandable health education.
Important safety rules:
- Never diagnose a person or claim that symptoms prove a disease.
- Never prescribe medicines, recommend dosages, or tell users to start,
  stop, or change medication.
- Explain that many symptoms have several possible causes.
- Encourage a qualified healthcare professional for personal assessment.
- For severe or rapidly worsening symptoms, trouble breathing, chest pain,
  fainting, seizures, severe allergic reactions, or other emergencies,
  advise the user to seek urgent medical help immediately and contact
  local emergency services.
- Do not ask for full name, address, phone number, passwords, or other
  identifying information.
- If asked something unrelated to health, politely say this chatbot is
  designed for general health education.
- Be calm, concise, non-judgmental, and use simple language.
- Do not present yourself as a doctor or a clinically validated system.
- If uncertain, say so rather than inventing facts.
This is educational information, not a diagnosis or substitute for care.
"""


def get_available_model():
    return HF_MODEL


def chat_with_ollama(message, history=None):
    if not HF_TOKEN:
        raise RuntimeError(
            "Hugging Face token is missing. Check the HF_TOKEN environment variable."
        )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if isinstance(history, list):
        for item in history[-8:]:
            if not isinstance(item, dict):
                continue

            role = item.get("role")
            content = item.get("content")

            if role in ("user", "assistant") and isinstance(content, str):
                messages.append({
                    "role": role,
                    "content": content[:1200]
                })

    messages.append({"role": "user", "content": message})

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": HF_MODEL,
        "messages": messages,
        "max_tokens": 500,
        "stream": False
    }

    try:
        response = requests.post(
            HF_API_URL,
            headers=headers,
            json=payload,
            timeout=120
        )

        if response.status_code == 401:
            raise RuntimeError("Hugging Face authentication failed. Check your token.")

        if response.status_code == 402:
            raise RuntimeError("Hugging Face inference credits or payment limit reached.")

        if response.status_code == 503:
            raise RuntimeError("The AI model is temporarily unavailable. Try again later.")

        response.raise_for_status()

        result = response.json()
        answer = result["choices"][0]["message"]["content"].strip()

        if not answer:
            raise RuntimeError("The AI returned an empty response.")

        return answer, HF_MODEL

    except requests.Timeout as error:
        raise RuntimeError(
            "The AI is taking too long to respond. Please try again."
        ) from error

    except requests.RequestException as error:
        raise RuntimeError(
            "Could not connect to Hugging Face. Please try again later."
        ) from error