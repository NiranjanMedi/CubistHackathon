# KL Divergence Implementation for Chess Novelty Engine

## Overview

This document describes the KL divergence approach used in our chess engine to detect when to play novel moves that humans won't expect.

## What is KL Divergence?

**Kullback-Leibler (KL) divergence** is a measure from information theory that quantifies how one probability distribution differs from another.

**Formula:**
```
KL(P || Q) = Σ P(x) × log(P(x) / Q(x))
```

**In plain English:** KL divergence measures how "surprised" distribution Q would be by distribution P.

## Our Application

### The Two Distributions

We compare two probability distributions over chess moves:

#### 1. Engine Distribution (P)
**What it represents:** What moves are objectively good according to chess engine evaluation

**How we build it:**
```python
def get_engine_distribution(board, temperature=100.0):
    scores = {}
    for move in legal_moves:
        # Evaluate position after making the move
        new_board = board.copy()
        new_board.make_move(move)
        scores[move] = evaluate(new_board)

    # Convert scores to probabilities using softmax
    exp_scores = {m: exp(score/temperature) for m, score in scores.items()}
    total = sum(exp_scores.values())
    return {m: s/total for m, s in exp_scores.items()}
```

**Example output (starting position):**
```python
{
    'b1c3': 0.052,  # Knight to c3
    'd2d4': 0.051,  # Pawn to d4
    'g1f3': 0.050,  # Knight to f3
    'e2e4': 0.049,  # Pawn to e4
    # ... 16 more moves
}
```

#### 2. Human Distribution (Q)
**What it represents:** What moves humans actually play in practice

**How we build it:**
```python
def get_human_distribution(board):
    # Query Lichess Opening Explorer API
    fen = board_to_fen(board)
    data = query_lichess(fen)

    # Convert game counts to probabilities
    total_games = sum(move['count'] for move in data['moves'])
    return {move['uci']: move['count'] / total_games
            for move in data['moves']}
```

**Example output (starting position from Lichess):**
```python
{
    'e2e4': 0.450,  # 45% of humans play e4
    'd2d4': 0.300,  # 30% play d4
    'g1f3': 0.150,  # 15% play Nf3
    'c2c4': 0.050,  # 5% play c4
    # ... other moves
}
```

### Computing KL Divergence

```python
def compute_kl_divergence(engine_dist, human_dist, epsilon=0.001):
    """
    KL(Engine || Human) - how surprised would humans be by engine preferences?
    """
    kl = 0.0
    for move, p_engine in engine_dist.items():
        p_human = human_dist.get(str(move), epsilon)
        if p_engine > 0:
            kl += p_engine * log(p_engine / p_human)
    return kl
```

### Interpretation

| KL Value | Meaning | Action |
|----------|---------|--------|
| < 0.5 | Engine and humans strongly agree | Play normally |
| 0.5 - 1.0 | Moderate disagreement | Borderline for novelty |
| 1.0 - 2.0 | Strong disagreement | **NOVELTY OPPORTUNITY** |
| > 2.0 | Extreme disagreement | Prime novelty territory |

**Our threshold: 1.0**

When `KL > 1.0`, the engine switches to novelty mode.

## Decision Logic

```python
def get_novel_move(board):
    # Step 1: Build both distributions
    engine_dist = get_engine_distribution(board)
    human_dist = get_human_distribution(board)

    # Step 2: Compute KL divergence
    kl = compute_kl_divergence(engine_dist, human_dist)

    # Step 3: Decision based on KL
    if kl > KL_THRESHOLD:  # 1.0
        # NOVELTY MODE
        # Pick move that engine likes but humans don't expect
        scores = {}
        for move in legal_moves:
            p_engine = engine_dist[move]
            p_human = human_dist.get(str(move), 0.001)
            scores[move] = p_engine / p_human  # High when engine likes, humans don't
        return max(scores, key=scores.get)
    else:
        # BASE MODE
        # Just play the engine's best move
        return max(engine_dist, key=engine_dist.get)
```

## Concrete Example

**Position:** After 1.e4 e5 2.Nf3 Nc6 3.Bb5 (Ruy Lopez)

**Engine distribution:**
```python
{
    'a6': 0.35,   # Attack the bishop
    'Nf6': 0.30,  # Develop knight
    'd6': 0.20,   # Solid defense
    'Bc5': 0.10,  # Develop bishop
    'f5': 0.05    # Aggressive but risky
}
```

**Human distribution (from Lichess):**
```python
{
    'a6': 0.85,   # 85% of humans play a6!
    'Nf6': 0.10,
    'd6': 0.03,
    'Bc5': 0.01,
    'f5': 0.01
}
```

**KL divergence calculation:**
```python
KL = 0.35 × log(0.35/0.85) +
     0.30 × log(0.30/0.10) +
     0.20 × log(0.20/0.03) +
     0.10 × log(0.10/0.01) +
     0.05 × log(0.05/0.01)

   = 0.35 × (-0.89) +
     0.30 × (1.10) +
     0.20 × (1.90) +
     0.10 × (2.30) +
     0.05 × (1.61)

   = -0.31 + 0.33 + 0.38 + 0.23 + 0.08
   = 0.71
```

**Result:** KL = 0.71 < 1.0 → **BASE MODE** (play normally)

Even though humans overwhelmingly prefer a6, the engine also thinks it's good, so there's not enough disagreement for novelty.

**Different scenario - Novelty triggered:**

If engine distribution was:
```python
{
    'Nf6': 0.40,  # Engine likes this
    'd6': 0.30,
    'a6': 0.20,   # Engine doesn't love a6
    'Bc5': 0.10
}
```

Then:
```python
KL = 0.40 × log(0.40/0.10) +
     0.30 × log(0.30/0.03) +
     0.20 × log(0.20/0.85) +
     0.10 × log(0.10/0.01)

   = 0.40 × 1.39 +
     0.30 × 2.30 +
     0.20 × (-1.43) +
     0.10 × 2.30

   = 0.56 + 0.69 - 0.29 + 0.23
   = 1.19
```

**Result:** KL = 1.19 > 1.0 → **NOVELTY MODE**

**Novelty scoring:**
```python
Nf6: 0.40 / 0.10 = 4.0  ← HIGHEST (engine likes, humans ignore)
d6:  0.30 / 0.03 = 10.0 ← EVEN BETTER!
a6:  0.20 / 0.85 = 0.24
Bc5: 0.10 / 0.01 = 10.0
```

**Engine plays:** Either **d6** or **Bc5** (both have high novelty scores)

## Why This Works

### 1. Theoretical Grounding
- **Information Theory:** High KL = high "surprise" when switching from Q to P
- **Bounded Rationality:** Humans don't calculate like engines, they pattern-match
- **Cognitive Psychology:** Unfamiliar patterns require more cognitive effort

### 2. Practical Advantages

**Over pure database frequency:**
- ✅ Works in positions not in database (uses heuristics)
- ✅ Contextual (accounts for position evaluation)
- ✅ Adaptive (threshold can be tuned)

**Over pure "rare moves":**
- ✅ Filtered for soundness (only considers good moves)
- ✅ Measures disagreement, not just rarity
- ✅ Position-sensitive

### 3. Soundness Filter

**Critical:** We only compute KL over moves within 100cp of the best move.

```python
def sound_move_scores(board, max_loss=100):
    scores = score_legal_moves(board, depth=3)
    best_score = max(scores.values())
    return {move: score for move, score in scores.items()
            if best_score - score <= max_loss}
```

This prevents blunders - novelty only chooses among sound moves.

## Data Source: Lichess vs Maia

**Current implementation: Lichess Opening Explorer**

**Why Lichess:**
- ✅ Real game data from millions of games
- ✅ Simple API query (no neural network to run)
- ✅ No dependencies (TensorFlow, PyTorch)
- ✅ Works offline with heuristic fallback

**Maia alternative:**
- Would give more accurate human prediction
- Requires running neural network inference
- More complex integration
- Future enhancement possibility

## Configuration Parameters

```python
# From novelty_engine.py
KL_THRESHOLD = 1.0      # Novelty triggers when KL > this
TEMPERATURE = 100.0     # Softmax temperature (higher = flatter)
EPSILON = 0.001         # Small probability for unseen moves
```

**Tuning guide:**
- Lower KL_THRESHOLD → More frequent novelty
- Higher KL_THRESHOLD → More conservative
- Lower TEMPERATURE → More peaked engine distribution
- Higher TEMPERATURE → Flatter engine distribution

## References

1. **Kullback, S., & Leibler, R. A. (1951).** On information and sufficiency. *Annals of Mathematical Statistics*, 22(1), 79-86.
   - Original KL divergence paper

2. **McIlroy-Young, R., et al. (2020).** Aligning Superhuman AI with Human Behavior: Chess as a Model System. *KDD 2020*.
   - Maia chess engine, human move prediction

3. **Shannon, C. (1950).** Programming a Computer for Playing Chess. *Philosophical Magazine*.
   - Foundational game tree theory

4. **Tang, Z., et al. (2024).** Maia-2: A Unified Model for Human-AI Alignment in Chess. *NeurIPS 2024*.
   - Unified human chess model

## Implementation File

**Location:** `BasicEngine/novelty_engine.py`

**Key functions:**
- `get_engine_distribution()` - Build engine probability distribution
- `get_human_distribution()` - Build human probability distribution (via Lichess)
- `compute_kl_divergence()` - Calculate KL(Engine || Human)
- `get_novel_move()` - Main entry point, returns best novel move
- `analyze_position()` - Debug/analysis function

**Line count:** ~213 lines
**Dependencies:** math (exp, log), board.py, engine.py, human_model.py
