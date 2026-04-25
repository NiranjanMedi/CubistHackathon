# Chess Engine — Research Grounding Document

This document describes every academic paper and statistical concept used to justify design decisions in this engine. For each paper, it describes what the paper actually says, and exactly how it was applied.

---

## Paper 1 — The Foundational Paper

### McIlroy-Young, R., Sen, S., Kleinberg, J., & Anderson, A. (2020). Aligning Superhuman AI with Human Behavior: Chess as a Model System. *Proceedings of the 26th ACM SIGKDD Conference on Knowledge Discovery and Data Mining (KDD 2020).*

**What the paper actually says**

This paper introduces Maia — a version of the AlphaZero architecture retrained on human chess games from Lichess rather than on self-play. The core finding is that Maia predicts human moves at significantly higher accuracy than Stockfish does, because Stockfish is trained to find the best move while Maia is trained to find the human move. The paper demonstrates that human chess play at different rating levels is statistically distinct and predictable — there is a genuine 1200-rated playing style, a genuine 1600-rated playing style, and so on. It is not just that stronger players make fewer random errors — they make systematically different types of moves. The paper also shows Maia can predict whether a human will make a large mistake on their next move with meaningful accuracy.

**How we use it**

Maia is the core tool in Component 2. Its output is a probability distribution over all legal moves from any position — P(move | position, rating). We use the inverse of this — 1 - P_maia(move) — as our novelty signal. A move with low Maia probability is a move humans do not naturally find or consider at that rating level. This is a more principled novelty signal than raw database frequency because it is a learned model of human cognition, not just a historical count. It generalises to positions not in any database and is sensitive to the opponent's specific rating level.

The blunder prediction finding justifies Component 1's approach: if Maia can predict where humans will make large mistakes, those are exactly the positions where injecting a novel move compounds the difficulty.

---

## Paper 2 — The Unified Maia Model

### Tang, Z., Jiao, D., McIlroy-Young, R., Kleinberg, J., Sen, S., & Anderson, A. (2024). Maia-2: A Unified Model for Human-AI Alignment in Chess. *Advances in Neural Information Processing Systems (NeurIPS 2024).*

**What the paper actually says**

The original Maia trained separate models for each rating band (1100, 1300, 1500, 1700, 1900). Maia-2 replaces this with a single unified model that uses a skill-aware attention mechanism — the model takes the player's rating as an explicit input and modulates its predictions accordingly. The key finding is that categorical skill embeddings outperform raw Elo as a predictor — the relationship between rating and playing style is non-linear and complex, not a smooth gradient. The unified model achieves better move prediction accuracy than the band-specific models across all rating levels.

**How we use it**

Maia-2 justifies using a single Maia query parameterised by the opponent's rating rather than selecting between separate models. This simplifies the Component 2 implementation significantly. More importantly, the finding that skill is non-linearly related to rating supports the rating-parameterised depth calibration in Component 1 — different Elo bands do not just make fewer errors, they have genuinely different analytical profiles. A depth-5 search is not just a noisier version of a depth-9 search for a weaker player — it is a qualitatively different model of cognition.

---

## Paper 3 — Variation Entropy

### Barthelemy, M. (2025). Chess Variation Entropy and Engine Relevance for Humans. *arXiv:2505.03251.*

**What the paper actually says**

This paper introduces variation entropy as a formal measure of chess position complexity from a human perspective. The core methodology computes entropy based on the gaps between the evaluations of the best move and second-best move at each step of the principal variation. A position with one clearly dominant move has low entropy — easy for humans to find the right move. A position where many moves look equally good has high entropy — humans struggle to identify the correct choice. The paper models the probability of a human finding the best move using a logit function where the skill level parameter represents their ability to discern between moves. The key empirical finding is that high-entropy positions cause the most errors specifically in the 1200-1800 rating range. Forced variations have low entropy. Positions with multiple viable-looking alternatives have high entropy.

**How we use it**

This paper is the primary statistical grounding for Component 1. The shallow/deep divergence we compute is a tractable proxy for variation entropy. When the shallow eval and deep eval disagree significantly, it means the position has high surface ambiguity — what looks correct on the surface is not what deep calculation reveals. This is exactly the structure that variation entropy captures formally. We do not compute full variation entropy (which requires evaluating all moves at all depths of the principal variation) but approximate it with the two-point divergence between surface eval and deep eval. The paper validates that this type of signal — disagreement between shallow and deep evaluation — is precisely what predicts human failure.

---

## Paper 4 — Spatial Statistics and Tipping Points

### Barthelemy, M. (2023). Statistical Analysis of Chess Games: Space Control and Tipping Points. *arXiv:2304.11425.*

**What the paper actually says**

This paper applies statistical physics methods to chess games. Two main findings are relevant. First, engines and humans use pieces in measurably different spatial patterns across a game — you can construct a distance metric between players based on how they distribute pieces across the board. Second, the paper identifies tipping points in chess games — positions where the game's trajectory changes sharply and irreversibly. These tipping points are statistically identifiable from board features. The paper also finds that the number of possible moves during a game is positively correlated with game outcome.

**How we use it**

The spatial distribution finding validates that engine-optimal moves and human-natural moves are measurably different along a spatial dimension — not just in eval but in how pieces are physically arranged. This is a statistical confirmation that the gap our engine exploits is real and measurable. The tipping point concept informed the Component 1 framing: critical points are not arbitrary — they are statistically identifiable positions where the game's direction is determined. Injecting novelty at a tipping point has maximum leverage because the position's trajectory is being set at that moment.

---

## Paper 5 — Blunder Prediction

### Rokach, L. & Shapira, B. (2026). Blunder Prediction in Chess. *Applied Intelligence, Springer.*

**What the paper actually says**

This paper builds a model to predict whether a human player will make a large mistake on their next move. It uses a hybrid CNN plus user embedding architecture and achieves 0.801 AUC on the blunder prediction task. The critical finding is that a latent blunder profile — a learned representation of a player's tendencies — is significantly more predictive of error than their explicit Elo rating. The model learns that certain position types systematically produce errors for certain player profiles, and this is not fully captured by rating alone.

**How we use it**

This paper does two things for us. First, it confirms that human error in chess is structured and predictable by position type — not random noise. This validates the entire premise of Component 1: there exist identifiable positions where humans are systematically more likely to fail, and we can detect them. Second, the finding that blunder profiles outperform raw Elo as a predictor suggests that our rating-parameterised depth calibration, while principled, is a simplification. A richer opponent model than Elo alone would improve Component 1's precision. This is flagged as a limitation and a direction for future work.

---

## Paper 6 — Tactical Difficulty

### Assessing the Difficulty of Chess Tactical Problems. (2019). *ResearchGate.*

**What the paper actually says**

This paper studies what makes chess tactical puzzles hard for humans. It proposes a three-category framework for complexity: difficulty (how hard the best move is to find), optionality (how many plausible-looking alternatives exist), and rarity (how unusual the pattern is in human experience). It finds that complexity scores integrating centipawn change and eval variability across candidate moves correlate with human error rates in tactical positions. Positions with multiple plausible-looking moves that are actually strongly differentiated in quality are the hardest.

**How we use it**

The optionality dimension directly informed the Component 1 sign disagreement weighting. A position where the shallow eval and deep eval disagree on sign is a position with maximum optionality in the worst sense — the human thinks one player is winning and the engine knows the other is. The three-category framework also informed our decision to use a composite discomfort signal rather than a single measure: difficulty corresponds to the magnitude of shallow/deep divergence, optionality corresponds to variation entropy, and rarity corresponds to Maia inverse probability.

---

## Paper 7 — Foundational Game Tree Theory

### Shannon, C. (1950). Programming a Computer for Playing Chess. *Philosophical Magazine, 41(314), 256-275.*

**What the paper actually says**

Shannon's foundational paper establishes the game-tree model of chess — the idea that chess can be solved in principle by searching a tree of all possible move sequences. It derives the branching factor of approximately 30 legal moves per position and estimates the total game-tree complexity. Shannon distinguishes between Type A strategies (full-width search to a fixed depth) and Type B strategies (selective search guided by heuristics). He establishes that the evaluation function at leaf nodes is the fundamental bottleneck — the quality of the search is bounded by the quality of the eval.

**How we use it**

Shannon's distinction between Type A and Type B search is the theoretical grounding for why our engine is not just a weaker Stockfish. Stockfish is a highly optimised Type A strategy. Our engine introduces a Type B element — selectivity guided not by chess heuristics but by a human cognition model. The evaluation function bottleneck finding also validates our approach: by changing what the evaluation function optimises for (human win probability rather than objective eval), we change the engine's behaviour fundamentally without changing the search architecture. Shannon's branching factor estimate is also used to justify why raw branching count is too coarse as a complexity signal — with ~30 moves per position on average, position-to-position variation in legal move count is small relative to the variation in move quality distribution.

---

## Statistical and Mathematical Concepts Used

### Multiplicative vs Additive Score Combination
**Where used:** Component 2 scoring formula — `eval^α × (1 - P_maia)^β`
**Justification:** Addition allows compensation between signals — a move with very low Maia probability but poor eval could outscore a move with good eval and moderate novelty. Multiplication requires both signals to be simultaneously high. This is a standard technique in multi-criteria decision analysis when both criteria are necessary conditions rather than substitutes. In our case soundness and novelty are both necessary — neither compensates for the absence of the other.

### Statistical Decision Theory — Type I/Type II Error Asymmetry
**Where used:** The sign multiplier of 2.0 in Component 1's discomfort formula
**Justification:** In statistical decision theory, different types of errors have different costs. A human who believes they are winning but is actually losing (sign disagreement) makes a categorically different class of decision than one who simply underestimates the magnitude of their advantage. The former plays aggressively when they should defend, attacks when they should consolidate, ignores threats because they think they have a buffer. This is not a magnitude error — it is a direction error. Direction errors in decision-making are consistently more costly than magnitude errors in the literature on bounded rationality and heuristic decision-making. The 2x multiplier operationalises this asymmetry. The exact value is a hyperparameter but the asymmetry is theoretically justified.

### Information Theory — Self-Information and Surprise
**Where used:** Conceptual framing of Maia inverse probability as a novelty signal
**Justification:** In Shannon's information theory, the self-information of an event with probability p is -log(p). High self-information means the event is surprising. Using 1 - P_maia(move) as a novelty signal is a linear approximation of self-information for low-probability events. The moves with the lowest Maia probability are the highest surprise moves — the ones that fall furthest outside the distribution of human chess cognition. This grounds the novelty signal in formal information theory rather than intuition.

### Softmax Conversion of Evals to Probabilities
**Where used:** Converting Stockfish centipawn evals into a probability distribution for comparison with Maia
**Justification:** Stockfish produces centipawn scores, not probabilities. To compare with Maia's probability distribution, evals can be converted via softmax: P(move) ∝ exp(eval(move) / temperature). The temperature parameter controls how peaked the distribution is — low temperature makes Stockfish's distribution very concentrated on the best move, high temperature spreads it more evenly. This is standard practice in combining neural and classical evaluations in chess and game-playing systems.

### Bounded Rationality
**Where used:** Conceptual foundation for the entire engine design
**Justification:** The engine's premise is grounded in Herbert Simon's bounded rationality framework — humans do not optimise fully but satisfice within cognitive constraints. The analytical horizon (how many moves ahead a player calculates) is the binding constraint in chess. The depth calibration in Component 1 operationalises this: we model the opponent as a bounded rational agent whose constraint is determined by their rating. Every design decision follows from taking bounded rationality seriously as the opponent model rather than assuming a perfect opponent.

---

## What Is Not Yet Grounded

The following design decisions are currently justified by intuition or first principles but do not yet have direct paper citations:

- The specific centipawn threshold of 100 for the soundness cutoff in Component 2
- The specific discomfort threshold of 80 centipawns in Component 1
- The opening suppression cutoff of move 10
- The winning suppression threshold of 200 centipawns
- The starting hyperparameters α=2.0, β=1.0

These are all flagged as empirical hyperparameters to be tuned experimentally. If the hackathon requires justification for these specific values, the honest answer is that they are reasonable starting points derived from domain knowledge of centipawn scales in chess, and will be validated or adjusted by the evaluation framework.
