from __future__ import annotations

Message = dict[str, str]

def build_messages(prompt: str, system: str | None = None) ->list[Message]:
    if not prompt.strip():
        raise ValueError("prompt must not be empty")

    messages: list[Message] = []

    if system and system.strip():
        messages.append({"role": "system", "content": system.strip()})
    messages.append({"role": "user", "content": prompt.strip()})

    return messages    
