"""Claude-powered move commentary with usage tracking."""

import os
import time
from dataclasses import dataclass
from typing import Optional

# claude-haiku-4-5-20251001 pricing
_INPUT_COST_PER_TOKEN = 0.80 / 1_000_000
_OUTPUT_COST_PER_TOKEN = 4.00 / 1_000_000


@dataclass
class CommentaryResult:
    text: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float


def get_commentary(
    engine_uci: str,
    mode: str,
    reason: str,
    eval_cp: int,
    kl_divergence: float,
    is_critical: bool,
    discomfort: float = 0.0,
) -> Optional[CommentaryResult]:
    """Call Claude to narrate the engine's move. Returns None if API key is absent or call fails."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic
    except ImportError:
        return None

    client = anthropic.Anthropic(api_key=api_key)

    prompt = (
        f"You are a chess commentator for a novelty-seeking engine. "
        f"In 1-2 sentences, explain why the engine played {engine_uci}.\n\n"
        f"Mode: {mode} ({'novelty-seeking' if mode == 'novelty' else 'standard engine play'})\n"
        f"Engine evaluation: {eval_cp:+d} centipawns (engine's perspective)\n"
        f"KL divergence (engine vs human preferences): {kl_divergence:.2f}\n"
        f"Critical position: {is_critical}, discomfort: {discomfort:.0f}cp\n"
        f"Engine reason: {reason}\n\n"
        f"Be concise and use chess terminology naturally. Do not repeat the move notation."
    )

    t0 = time.monotonic()
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=120,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception:
        return None
    latency_ms = (time.monotonic() - t0) * 1000

    text = response.content[0].text.strip()
    in_tok = response.usage.input_tokens
    out_tok = response.usage.output_tokens
    cost = in_tok * _INPUT_COST_PER_TOKEN + out_tok * _OUTPUT_COST_PER_TOKEN

    return CommentaryResult(
        text=text,
        input_tokens=in_tok,
        output_tokens=out_tok,
        cost_usd=cost,
        latency_ms=latency_ms,
    )
