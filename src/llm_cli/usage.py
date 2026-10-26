from __future__ import annotations

PRICES_PER_MILLION : dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "deepseek-chat": (0.27, 1.10),
    "qwen-plus": (0.40, 1.20),
}

def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int)-> float| None :
    price = PRICES_PER_MILLION.get(model)
    if price is None:
        return None
    input_price, output_price = price
    return prompt_tokens/1000000 * input_price + completion_tokens / 1000000 * output_price
