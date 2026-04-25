# Engine Architecture Documentation

## System Overview

The BasicEngine novelty chess engine uses **KL divergence** to identify positions where engine and human move preferences diverge, then plays moves that are objectively sound but unexpected by humans.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Chess Position                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│ Engine Analysis  │    │  Human Prediction │
│  (Minimax + Eval)│    │  (Lichess API)    │
└────────┬─────────┘    └────────┬──────────┘
         │                       │
         │  Softmax             │  Frequency
         │  Temperature=100     │  to Probability
         ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│  P_engine(move)  │    │  P_human(move)   │
│  Distribution    │    │  Distribution    │
└────────┬─────────┘    └────────┬──────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
         ┌───────────────────────┐
         │  Compute KL Divergence│
         │  KL(Engine || Human)  │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │    KL < 1.0?          │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    YES  │                       │  NO
         ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│   BASE MODE      │    │  NOVELTY MODE    │
│ Play engine best │    │ Maximize:        │
│ move             │    │ P_engine(m) /    │
│                  │    │ P_human(m)       │
└──────────────────┘    └──────────────────┘
```

## Component Breakdown

### 1. Board Representation
**File:** `board.py`

**Purpose:** Internal chess board state and move generation

**Key classes:**
- `Board` - 8x8 array, turn tracking, castling rights
- `Move` - From/to coordinates, promotion
- `legal_moves()` - Generate all legal moves

**Format:** White pieces uppercase (e.g., `wN`), black lowercase (e.g., `bN`)

### 2. Base Engine
**File:** `engine.py`

**Purpose:** Chess evaluation and search

**Key functions:**
- `evaluate(board)` - Material + piece-square tables
- `_negamax(board, depth, alpha, beta)` - Minimax with alpha-beta pruning
- `best_move(board, depth)` - Returns highest-scoring move

**Evaluation:**
```python
PIECE_VALUES = {
    'P': 100,   # Pawn
    'N': 320,   # Knight
    'B': 330,   # Bishop
    'R': 500,   # Rook
    'Q': 900,   # Queen
    'K': 20000  # King
}
```

Plus position bonuses from piece-square tables.

### 3. Human Model
**File:** `human_model.py`

**Purpose:** Predict what moves humans would play

**Primary method:** Lichess Opening Explorer API
```python
def query_lichess(fen):
    url = f"https://explorer.lichess.ovh/lichess?fen={fen}"
    # Returns: {moves: [{uci: 'e2e4', white: 1000, draws: 500, black: 300}]}
```

**Fallback method:** Heuristic estimation
- Prefer captures (+2.0 score)
- Prefer central squares (+1.5)
- Prefer piece development (+1.0)
- Avoid edge pawns (×0.5)

**Output:** Probability distribution `{move_uci: probability}`

### 4. Novelty Engine
**File:** `novelty_engine.py` ⭐ **CORE**

**Purpose:** KL divergence-based move selection

**Algorithm:**
```python
1. Filter moves for soundness (within 100cp of best)
2. Build engine distribution via softmax
3. Build human distribution via Lichess
4. Compute KL divergence
5. If KL > 1.0:
     Select move maximizing P_engine / P_human
   Else:
     Select engine's best move
```

**Key parameters:**
```python
KL_THRESHOLD = 1.0      # Novelty trigger
TEMPERATURE = 100.0     # Softmax temperature
EPSILON = 0.001         # Probability floor for unseen moves
```

**Main entry point:**
```python
def get_novel_move(board: Board) -> Optional[Move]
```

### 5. Critical Point Detector
**File:** `critical_point.py`

**Purpose:** Game phase and position complexity analysis

**Not used in primary engine** - Available for future integration

**Functionality:**
- Detect game phase (opening/middlegame/endgame)
- Measure "discomfort" (shallow vs deep eval divergence)
- Rating-calibrated depth search
- Suppress novelty in opening/endgame

### 6. Web Server
**File:** `server.py`

**Purpose:** Flask API for web-based play

**Endpoints:**
- `GET /` - Serve HTML chess UI
- `GET /api/state` - Current board state
- `POST /api/reset` - New game
- `POST /api/move` - Make move, get engine response
- `POST /api/engine_move` - Engine plays one move

**Response includes:**
```json
{
  "engine_move": "b8c6",
  "engine_mode": "base",
  "critical_score": 0.0997,
  "kl_divergence": 0.0997,
  "is_novelty_position": false
}
```

## Data Flow

### Typical Move Selection

1. **User makes move** (e.g., `e2e4`)
2. **Server calls** `get_novel_move(board)`
3. **Novelty engine:**
   - Evaluates all legal moves (depth 3)
   - Filters to moves within 100cp of best
   - Builds engine distribution via softmax(evals)
   - Queries Lichess for human distribution
   - Computes KL divergence = 0.0997
   - KL < 1.0 → BASE MODE
   - Returns best engine move
4. **Server responds** with move + analysis
5. **UI updates** board and displays KL score

### When Novelty Triggers

1. **Middlegame position** with high divergence
2. **KL divergence > 1.0** detected
3. **NOVELTY MODE activated**
4. **Scoring formula:** `P_engine(move) / P_human(move)`
   - High when engine likes move but humans don't
5. **Best novel move selected**
6. **Server responds** with `"engine_mode": "novelty"`

## File Structure

```
BasicEngine/
├── board.py                    # Board representation
├── engine.py                   # Minimax search & evaluation
├── human_model.py              # Lichess API & heuristics
├── novelty_engine.py           # KL divergence novelty ⭐
├── critical_point.py           # Game phase analysis
├── demo_novelty.py             # Demo script
├── play_novelty.py             # Interactive play
├── test_pipeline.py            # Integration test
├── uci.py                      # UCI protocol (for GUIs)
└── unit_tests/                 # Test suite
    ├── test_novelty_engine.py
    ├── test_basic_functionality.py
    └── run_all_tests.py

server.py                       # Flask web server
index.html                      # Web UI
```

## Key Design Decisions

### 1. Why Lichess API instead of Maia?

**Lichess:**
- ✅ Real game statistics from millions of games
- ✅ Simple HTTP API, no neural network
- ✅ No ML dependencies (TensorFlow/PyTorch)
- ✅ Heuristic fallback for offline use

**Maia:**
- ✅ More accurate human prediction
- ❌ Requires neural network inference
- ❌ Complex setup and dependencies
- ❌ Harder to deploy

**Decision:** Start with Lichess, Maia is future enhancement.

### 2. Why KL Divergence threshold = 1.0?

**Empirically derived:**
- KL < 0.5: Engine and humans strongly agree
- KL = 1.0: Noticeable but not extreme disagreement
- KL > 2.0: Very rare, extreme cases

**1.0 balances:**
- Too low → Novelty triggers too often
- Too high → Novelty almost never triggers

**Tunable:** Can adjust based on testing results.

### 3. Why Softmax Temperature = 100.0?

**Effect of temperature:**
- Low (1.0): Very peaked, best move gets ~90% probability
- Medium (100.0): Moderate spread, top moves get 5-10% each
- High (1000.0): Nearly uniform distribution

**100.0 chosen:**
- Spreads probability across multiple good moves
- More realistic distribution than over-peaked
- Better matches typical human consideration set

### 4. Why 100cp Soundness Filter?

**Chess evaluation scale:**
- 50cp = Half a pawn advantage
- 100cp = One pawn advantage
- 300cp = Minor piece advantage

**100cp limit:**
- Allows positional sacrifices
- Prevents blunders
- Conservative but not overly restrictive

## Performance Characteristics

### Time Complexity

**Per move selection:**
- Legal move generation: O(1) amortized
- Minimax search (depth 3): ~O(30³) ≈ 27,000 positions
- Softmax conversion: O(n) where n = legal moves
- Lichess API query: O(1) with caching
- KL divergence: O(n)

**Total:** ~0.1-0.5 seconds per move on modern hardware

### Space Complexity

- Board state: O(1) - 8×8 array
- Move generation: O(n) - typically n ≈ 30
- Transposition table: Not implemented (future enhancement)
- API cache: O(m) where m = unique positions queried

## Limitations and Future Work

### Current Limitations

1. **No transposition table** - Searches same positions multiple times
2. **Fixed depth = 3** - Doesn't adapt to time control
3. **No opening book** - Evaluates every opening position
4. **Lichess API rate limits** - Falls back to heuristics frequently
5. **No endgame tablebases** - Weaker in endgames

### Potential Enhancements

1. **Maia integration** - Better human prediction
2. **Dynamic depth** - Adjust based on time/complexity
3. **Iterative deepening** - Progressive depth increase
4. **Opening book** - Store common opening lines
5. **Neural network eval** - Replace material+PST with NN
6. **Monte Carlo Tree Search** - Alternative to minimax
7. **Opponent modeling** - Learn from opponent's play style

## Testing

**Unit test coverage:** 29 tests, all passing

**Test categories:**
- Engine distribution validity
- KL divergence mathematical properties
- Move legality
- Deterministic behavior
- Game phase detection
- Full pipeline integration

**Run tests:**
```bash
cd BasicEngine/unit_tests
python3 run_all_tests.py
```

## References

See `chess_engine_research.md` for academic paper references and theoretical grounding.

**Key papers:**
1. McIlroy-Young et al. (2020) - Maia chess engine
2. Shannon (1950) - Game tree search
3. Barthelemy (2025) - Variation entropy
4. Kullback & Leibler (1951) - KL divergence

## Quick Start

**Run web server:**
```bash
python server.py
# Visit http://localhost:5000
```

**Run in terminal:**
```bash
python BasicEngine/play_novelty.py
```

**Run tests:**
```bash
python BasicEngine/unit_tests/run_all_tests.py
```

**UCI interface (for GUIs):**
```bash
python BasicEngine/uci.py
```
