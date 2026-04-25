# Novelty Chess Engine - Clean Setup

This branch contains a working novelty chess engine using KL divergence to play unexpected but sound moves.

## What is This?

The novelty engine uses **KL divergence** to detect positions where the chess engine and humans disagree about which moves are best. In these positions, it plays moves that are:
- ✅ Objectively sound (within 100cp of best move)
- ✅ Unexpected by humans (low Lichess play frequency)
- ✅ Strategically advantageous (good engine evaluation)

### How It Works

1. **Engine Distribution**: Build probability distribution over moves using minimax + softmax
2. **Human Distribution**: Build probability distribution from Lichess game statistics
3. **KL Divergence**: Compute `KL(Engine || Human)` to measure disagreement
4. **Decision**:
   - If `KL > 1.0`: Play move that maximizes `P_engine(move) / P_human(move)` (novelty mode)
   - If `KL < 1.0`: Play engine's best move (base mode)

## Setup

### 1. Clone and Install

```bash
git clone https://github.com/NiranjanMedi/CubistHackathon.git
cd CubistHackathon
git checkout novelty-clean

# Install dependencies
pip install flask flask-cors requests
```

### 2. Run the Server

```bash
python server.py
```

Visit http://localhost:5000 to play against the engine in your browser.

### 3. Watch the KL Divergence

The server returns these fields in the API response:
- `kl_divergence`: How much engine and humans disagree (higher = more divergence)
- `is_novelty_position`: `true` when KL > 1.0
- `engine_mode`: Either `"novelty"` or `"base"`

## Files Overview

### Core Engine Files

| File | Purpose | Lines |
|------|---------|-------|
| `BasicEngine/board.py` | Chess board representation and move generation | 200 |
| `BasicEngine/engine.py` | Minimax search with alpha-beta pruning | 150 |
| `BasicEngine/human_model.py` | Lichess API + heuristic fallback | 210 |
| `BasicEngine/novelty_engine.py` | KL divergence novelty algorithm | 210 |

### Server

| File | Purpose |
|------|---------|
| `server.py` | Flask REST API for web interface |
| `index.html` | Web-based chess UI |

## API Endpoints

### GET /api/state
Returns current board state, legal moves, game status.

### POST /api/reset
Starts a new game.

### POST /api/move
Apply a human move (UCI format), engine responds.

**Example request:**
```json
{
  "move": "e2e4"
}
```

**Example response:**
```json
{
  "human_move": "e2e4",
  "engine_move": "b8c6",
  "kl_divergence": 0.0997,
  "is_novelty_position": false,
  "engine_mode": "base",
  "turn": "w",
  "history": ["e2e4", "b8c6"]
}
```

## Configuration

Edit `BasicEngine/novelty_engine.py` to tune parameters:

```python
KL_THRESHOLD = 1.0      # Higher = less frequent novelty
TEMPERATURE = 100.0     # Higher = flatter engine distribution
EPSILON = 0.001         # Probability floor for unseen moves
```

## Data Source

**Human move probabilities** come from:
- **Primary**: Lichess Opening Explorer API (millions of real games)
- **Fallback**: Heuristic model (captures, center, development)

**NOT using Maia** - the Lichess API provides sufficient human data without requiring neural network dependencies.

## Example Positions

### High KL Divergence (Novelty Triggers)

When engine sees a tactical opportunity humans miss:
- KL > 1.0
- Engine plays rare but strong move
- Humans surprised, forced to calculate unfamiliar position

### Low KL Divergence (Base Mode)

When engine and humans agree on best moves:
- KL < 1.0
- Engine plays conventional best move
- Standard chess theory applies

## Troubleshooting

### "ModuleNotFoundError: No module named 'flask'"
```bash
pip install flask flask-cors
```

### "Lichess API unavailable"
The engine will automatically fall back to heuristic-based human predictions. This is normal and expected.

### Server won't start
Make sure you're in the right directory:
```bash
cd CubistHackathon
python server.py
```

## Testing

Run the unit tests (if available):
```bash
cd BasicEngine/unit_tests
python run_all_tests.py
```

## Questions?

This is a clean implementation of the KL divergence novelty engine. If your teammates can't run it:

1. Make sure they're on the `novelty-clean` branch
2. Verify they have Python 3.6+ installed
3. Check that Flask dependencies are installed
4. Try running `python server.py` from the repo root

The engine should work out of the box with just Flask and standard Python libraries.
