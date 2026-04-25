# BasicEngine Documentation

This directory contains comprehensive documentation for the BasicEngine novelty chess engine.

## Documentation Files

### 1. [chess_engine_research.md](chess_engine_research.md)
**Academic and theoretical foundation**

- Research papers that informed design decisions
- Statistical and mathematical concepts used
- Theoretical grounding for KL divergence approach
- Bounded rationality framework
- Information theory applications

**Key papers covered:**
- Maia chess engine (McIlroy-Young et al., 2020)
- Variation entropy (Barthelemy, 2025)
- Game tree theory (Shannon, 1950)
- Blunder prediction
- Tactical difficulty assessment

### 2. [KL_DIVERGENCE_IMPLEMENTATION.md](KL_DIVERGENCE_IMPLEMENTATION.md)
**Detailed KL divergence explanation**

- What KL divergence is and why we use it
- The two probability distributions (engine vs human)
- Concrete examples with calculations
- Decision logic and thresholds
- Comparison to alternatives (Maia, pure rarity)
- Configuration parameters and tuning

**Read this for:** Understanding the core algorithm

### 3. [ENGINE_ARCHITECTURE.md](ENGINE_ARCHITECTURE.md)
**System design and implementation**

- Architecture diagram
- Component breakdown (board, engine, human model, novelty)
- Data flow through the system
- File structure
- Design decisions and tradeoffs
- Performance characteristics
- Testing approach

**Read this for:** Understanding how everything fits together

## Quick Reference

### What This Engine Does

Uses **KL divergence** to detect positions where the chess engine and humans disagree about move quality, then plays moves that are:
- ✅ Objectively sound (within 100cp of best move)
- ✅ Unexpected by humans (low Lichess play frequency)
- ✅ Strategically advantageous (engine evaluation is good)

### Core Algorithm

```python
1. Evaluate all legal moves (minimax depth 3)
2. Build engine probability distribution (softmax over evals)
3. Build human probability distribution (Lichess API)
4. Compute KL divergence: KL(Engine || Human)
5. If KL > 1.0:
     Play move with highest (P_engine / P_human)
   Else:
     Play engine's best move
```

### Key Files

| File | Purpose | Lines |
|------|---------|-------|
| `novelty_engine.py` | KL divergence implementation | 213 |
| `human_model.py` | Lichess API + heuristics | 213 |
| `engine.py` | Minimax search + eval | 150 |
| `board.py` | Board representation | 350 |
| `server.py` | Flask web interface | 223 |

### Key Concepts

**KL Divergence:** Measures how different two probability distributions are

**Engine Distribution:** What moves are objectively good (via minimax)

**Human Distribution:** What moves humans actually play (via Lichess)

**Novelty Score:** `P_engine(move) / P_human(move)` - high when engine likes but humans don't

**Soundness Filter:** Only consider moves within 100cp of best

**Temperature:** Softmax parameter controlling distribution shape (100.0)

**Threshold:** KL > 1.0 triggers novelty mode

## For Different Audiences

### For Researchers
→ Start with **chess_engine_research.md**
- Academic citations and theoretical grounding
- Statistical justifications for design choices
- Connections to bounded rationality and information theory

### For Developers
→ Start with **ENGINE_ARCHITECTURE.md**
- System design and component interactions
- File structure and code organization
- Performance characteristics and limitations

### For Chess Players
→ Start with **KL_DIVERGENCE_IMPLEMENTATION.md**
- Concrete examples with chess positions
- Why the engine plays certain moves
- How it differs from normal engines

### For Evaluators/Judges
→ Read all three:
1. Research document for theoretical validity
2. Implementation document for algorithmic clarity
3. Architecture document for engineering quality

## Example Usage

### Analyze a Position
```python
from board import Board
from novelty_engine import analyze_position

board = Board()  # Starting position
analysis = analyze_position(board)

print(f"KL Divergence: {analysis['kl_divergence']:.3f}")
print(f"Novelty position: {analysis['is_novelty_position']}")
print(f"Recommended move: {analysis['recommended_move']}")
```

### Play Against the Engine
```bash
# Web interface
python server.py
# Visit http://localhost:5000

# Terminal interface
python BasicEngine/play_novelty.py

# UCI interface (for chess GUIs)
python BasicEngine/uci.py
```

### Run Tests
```bash
cd BasicEngine/unit_tests
python3 run_all_tests.py

# Output:
# Tests run: 29
# Successes: 29
# ✓ ALL TESTS PASSED!
```

## Configuration

Edit `BasicEngine/novelty_engine.py`:

```python
KL_THRESHOLD = 1.0      # Lower = more frequent novelty
TEMPERATURE = 100.0     # Lower = more peaked distribution
EPSILON = 0.001         # Probability floor for unseen moves
```

## Data Sources

### Primary: Lichess Opening Explorer
- Real games from millions of players
- Returns frequency of each move in position
- Free, no authentication required (with fallback)

### Fallback: Heuristic Model
- When API unavailable or position not in database
- Hand-coded chess heuristics:
  - Prefer captures
  - Prefer central squares
  - Prefer piece development

### Future: Maia Neural Network
- More accurate human prediction
- Rating-specific models
- Requires ML dependencies

## Metrics and Evaluation

### Engine Strength
- Material evaluation + piece-square tables
- Minimax search with alpha-beta pruning
- Depth 3 (~27,000 positions evaluated per move)

### Novelty Effectiveness
- Measured by deviation from human database
- Validated by KL divergence thresholds
- Soundness guaranteed by 100cp filter

### Test Coverage
- 29 unit tests covering:
  - Probability distribution validity
  - KL divergence correctness
  - Move legality
  - Game phase detection
  - Full pipeline integration

## Limitations

**Current:**
- Fixed depth 3 (no time-based adjustment)
- No transposition table
- Lichess API rate limits
- No opening book
- No endgame tablebases

**Future Enhancements:**
- Maia integration for better human prediction
- Dynamic depth search
- Neural network evaluation
- Opening book
- Opponent modeling

## References

**Academic Papers:**
1. McIlroy-Young et al. (2020) - Maia
2. Tang et al. (2024) - Maia-2
3. Shannon (1950) - Game tree theory
4. Barthelemy (2025) - Variation entropy
5. Kullback & Leibler (1951) - KL divergence

**See:** `chess_engine_research.md` for full citations and applications

## License and Attribution

- Lichess Opening Explorer API: Public, courtesy of Lichess.org
- Research citations: See individual papers
- Code: Original implementation

## Contact and Support

For questions about:
- **Theory/Research:** See chess_engine_research.md citations
- **Implementation:** See ENGINE_ARCHITECTURE.md component breakdown
- **Algorithm:** See KL_DIVERGENCE_IMPLEMENTATION.md examples

## Getting Started

**Quickest path:**
1. Read this README (you're here!)
2. Run `python server.py`
3. Play at http://localhost:5000
4. Watch KL divergence scores to see when novelty triggers

**Deep dive:**
1. Read KL_DIVERGENCE_IMPLEMENTATION.md for the core idea
2. Read ENGINE_ARCHITECTURE.md for system design
3. Read chess_engine_research.md for theoretical grounding
4. Run unit tests to verify everything works
5. Experiment with different positions and configurations

Enjoy exploring the engine! 🎯
