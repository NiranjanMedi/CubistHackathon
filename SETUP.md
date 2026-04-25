# Setup Instructions for Friends

## Quick Start (niranjan-engine branch)

### 1. Clone and Setup
```bash
git clone https://github.com/NiranjanMedi/CubistHackathon.git
cd CubistHackathon
git checkout niranjan-engine
```

### 2. Install Dependencies
```bash
pip install flask flask-cors requests
```

### 3. Run the Engine
```bash
python server.py
```

### 4. Play in Browser
Open: http://localhost:5000

---

## What You're Getting

### The KL Divergence Novelty Engine

This engine uses **KL divergence** to detect when to play unusual moves:

- **Files**: `BasicEngine/novelty_engine.py` + `BasicEngine/human_model.py`
- **Algorithm**: Compares engine preferences vs human play frequencies
- **Data Source**: Lichess Opening Explorer API (real games)
- **Novelty Trigger**: When KL divergence > 1.0

### How It Works

1. **Engine Distribution**: What moves are objectively good (via minimax evaluation)
2. **Human Distribution**: What moves humans actually play (from Lichess database)
3. **KL Divergence**: Measures disagreement between engine and humans
4. **Decision**:
   - If KL > 1.0: Play a novel move (engine likes it, humans don't expect it)
   - If KL < 1.0: Play the best engine move (everyone agrees anyway)

---

## Testing the Engine

```bash
cd BasicEngine
python3 << 'EOF'
from board import Board
from novelty_engine import get_novel_move, analyze_position

board = Board()
analysis = analyze_position(board)

print(f"KL Divergence: {analysis['kl_divergence']:.4f}")
print(f"Novelty Mode: {analysis['is_novelty_position']}")
print(f"Recommended: {analysis['recommended_move']}")
EOF
```

Expected output:
```
KL Divergence: 0.0997
Novelty Mode: False
Recommended: b1c3
```

---

## API Endpoints

Once server is running (http://localhost:5000):

- `GET /api/state` - Current board state
- `POST /api/reset` - New game
- `POST /api/move` - Make a move (you + engine responds)
- `POST /api/engine_move` - Engine plays one move

Example:
```bash
# Make a move
curl -X POST http://localhost:5000/api/move \
  -H "Content-Type: application/json" \
  -d '{"move": "e2e4"}'
```

---

## Configuration

Edit `BasicEngine/novelty_engine.py`:

```python
KL_THRESHOLD = 1.0      # Novelty triggers when KL > this (default: 1.0)
TEMPERATURE = 100.0     # Softmax temperature (higher = flatter distribution)
EPSILON = 0.001         # Small probability for unseen moves
```

---

## Troubleshooting

### "No module named 'flask'"
```bash
pip install flask flask-cors
```

### "Connection refused" when accessing localhost
Make sure server is running:
```bash
python server.py
```

### "Human distribution uses heuristics" warning
This is fine! The engine falls back to heuristics when:
- Lichess API is unavailable (no auth token)
- Position not in Lichess database (deep middlegame/endgame)

To use real Lichess data (optional):
```bash
# Get token from: https://lichess.org/account/oauth/token
export LICHESS_API_TOKEN="lip_xxxxxxxxxxxxx"
python server.py
```

---

## What's Included

### Core Engine Files
- `BasicEngine/board.py` - Chess board representation
- `BasicEngine/engine.py` - Minimax evaluation engine
- `BasicEngine/novelty_engine.py` - KL divergence novelty engine ⭐
- `BasicEngine/human_model.py` - Human move prediction (Lichess API)
- `BasicEngine/critical_point.py` - Game phase detection

### UI & Server
- `server.py` - Flask API server
- `index.html` - Web-based chess UI

### Testing
- `BasicEngine/demo_critical_point.py` - Demo of critical point detection
- `BasicEngine/test_pipeline.py` - Integration tests
- `BasicEngine/uci.py` - UCI protocol (for chess GUIs)

---

## Next Steps

1. **Play some games** - See when novelty mode triggers (KL > 1.0)
2. **Tune thresholds** - Adjust `KL_THRESHOLD` to change novelty frequency
3. **Analyze positions** - Use `analyze_position()` to debug
4. **Compare engines** - Try different novelty strategies

---

## Notes

- Engine uses **Lichess game statistics**, NOT Maia
- No neural networks or machine learning
- Pure Python, no heavy dependencies
- Works offline (uses heuristic fallback)

Enjoy! 🎯
