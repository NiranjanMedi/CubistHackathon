# Novelty Chess Engine - Unit Tests

Comprehensive test suite for the Novelty Chess Engine components.

## Test Files

### `test_novelty_engine.py`
Tests the core novelty selection logic:
- **TestEngineDistribution**: Probability distribution generation from engine evaluations
- **TestKLDivergence**: KL divergence computation between engine and human distributions
- **TestScoreMoveNovelty**: Novelty scoring for individual moves
- **TestGetNovelMove**: Main novel move selection function
- **TestIntegration**: Full pipeline from position to novel move

**Key tests:**
- Distribution sums to 1.0 and all probabilities in [0, 1]
- Temperature parameter affects distribution sharpness
- KL divergence returns 0 for identical distributions
- Novel moves are always legal
- Deterministic behavior (same position → same move)

### `test_critical_point.py`
Tests the critical point detection system:
- **TestGamePhase**: Opening/middlegame/endgame detection
- **TestDiscomfort**: Discomfort computation (shallow vs deep eval divergence)
- **TestDepthCalibration**: Depth mapping by opponent rating
- **TestShallowAndDeepEval**: Evaluation functions
- **TestIsCriticalPoint**: Main critical point detector
- **TestAnalyzeCriticalPoint**: Detailed analysis output

**Key tests:**
- Opening detected for moves 0-10
- Middlegame for moves 11-40
- Endgame for moves 41+ or low piece count
- Depth increases with opponent rating (<1200→2, 1200→3, 1500→4, 1800→5, 2100+→6)
- Critical points only trigger in middlegame
- Discomfort formula correctness

### `test_human_novelty_engine.py`
Tests the HumanNoveltyEngine class (main integration):
- **TestEngineDecision**: EngineDecision dataclass structure
- **TestHumanNoveltyEngine**: Engine initialization and basic behavior
- **TestModeSelection**: Mode switching logic (base/novelty/fallback)
- **TestDifferentRatings**: Behavior across rating ranges
- **TestDeterminism**: Reproducibility

**Key tests:**
- Chosen moves are always legal
- Base mode in opening and endgame
- Novelty mode only in middlegame when critical
- Mode matches chosen move (base_move vs novelty_move)
- Different ratings handled correctly (1200, 1500, 1800, 2100+)

### `test_integration.py`
End-to-end integration tests:
- **TestSoundness**: No blunders or illegal moves
- **TestNoveltyBehavior**: Novelty differs from base
- **TestModeSwitching**: Phase transitions
- **TestCompleteGame**: Full game simulation
- **TestDirectNoveltyEngine**: Direct `get_novel_move()` testing
- **TestCriticalPointDetection**: Detection in context
- **TestDifferentRatings**: Cross-rating validation
- **TestEdgeCases**: Edge cases and error handling

**Key tests:**
- Novelty moves don't cause >500cp loss (blunder check)
- All moves are legal throughout game simulation
- Opening uses base mode exclusively
- Middlegame allows novelty mode
- Endgame reverts to base mode
- Handles edge cases (move_count=0, very high ratings)

## Running Tests

### Run All Tests
```bash
cd unit_tests
python run_all_tests.py
```

### Run Specific Module
```bash
python run_all_tests.py --module novelty_engine
python run_all_tests.py --module critical_point
python run_all_tests.py --module human_novelty_engine
python run_all_tests.py --module integration
```

### Verbose Output
```bash
python run_all_tests.py -v
```

### Quiet Output
```bash
python run_all_tests.py -q
```

### Run Individual Test File
```bash
python test_novelty_engine.py
python test_critical_point.py
python test_human_novelty_engine.py
python test_integration.py
```

### Run Specific Test Class
```bash
python -m unittest test_novelty_engine.TestEngineDistribution
python -m unittest test_critical_point.TestGamePhase
```

### Run Specific Test Method
```bash
python -m unittest test_novelty_engine.TestEngineDistribution.test_returns_valid_probability_distribution
```

## Test Coverage

| Module | Test File | Coverage Target | Priority |
|--------|-----------|----------------|----------|
| `novelty_engine.py` | `test_novelty_engine.py` | 90%+ | HIGH |
| `critical_point.py` | `test_critical_point.py` | 85%+ | HIGH |
| `human_novelty_engine.py` | `test_human_novelty_engine.py` | 90%+ | HIGH |
| Full Pipeline | `test_integration.py` | Key scenarios | MEDIUM |

## Test Strategy

### Unit Tests (Fast, Isolated)
- Test individual functions with known inputs/outputs
- Mock external dependencies (e.g., Lichess API)
- Use simple, fixed board positions
- **Run frequently during development**

### Integration Tests (Slower, End-to-End)
- Test full pipeline on real positions
- Verify move legality and soundness
- Check that novelty mode actually differs from base
- **Run before commits**

## Expected Test Results

All tests should pass on a clean installation. If tests fail:

1. **Import errors**: Ensure you're running from the `unit_tests/` directory or parent directory is in `sys.path`
2. **Evaluation differences**: Some tests use heuristic evaluations which may vary slightly
3. **Timeout issues**: Integration tests may be slow on slower machines

## Adding New Tests

When adding new functionality:

1. **Write tests first** (TDD approach)
2. **Follow naming convention**: `test_<module>.py` for file, `Test<Feature>` for class
3. **Use descriptive test names**: `test_should_do_something_when_condition`
4. **Add docstrings**: Explain what the test validates
5. **Update this README**: Document new test files/classes

## Continuous Integration

To integrate with CI/CD:

```bash
# In your CI script
cd engines/novelty/unit_tests
python run_all_tests.py --quiet
```

Exit code:
- `0`: All tests passed
- `1`: Some tests failed

## Debugging Failed Tests

### Verbose Mode
```bash
python run_all_tests.py -v
```

### Run Single Failing Test
```bash
python -m unittest test_novelty_engine.TestEngineDistribution.test_returns_valid_probability_distribution -v
```

### Add Print Statements
Temporarily add `print()` statements in test code to debug:

```python
def test_something(self):
    result = function_under_test()
    print(f"DEBUG: result = {result}")  # Temporary debug
    self.assertEqual(result, expected)
```

## Test Fixtures

Common test positions used across tests:

1. **Starting position**: Clean board, move 0
2. **After 1.e4**: Simple opening move
3. **Middlegame**: Moves 15-30, pieces developed
4. **Endgame**: Moves 40+, few pieces remaining

## Mocking

Tests mock the following external dependencies:

- **Lichess API**: Human move distribution queries
  - Mock in `test_novelty_engine.py` to avoid API calls
  - Use heuristic fallback in other tests

## Performance

Typical test run times:
- `test_novelty_engine.py`: ~5-10 seconds
- `test_critical_point.py`: ~5-10 seconds
- `test_human_novelty_engine.py`: ~10-15 seconds
- `test_integration.py`: ~15-20 seconds
- **Total**: ~35-55 seconds for all tests

## Contributing

When contributing tests:

1. Ensure all existing tests still pass
2. Add tests for new features
3. Maintain >85% code coverage
4. Follow existing test structure and naming conventions
5. Update this README with new test documentation
