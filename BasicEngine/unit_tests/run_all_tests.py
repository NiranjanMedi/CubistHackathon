#!/usr/bin/env python3
"""
Run all unit tests for the Novelty Chess Engine.

Usage:
    python run_all_tests.py              # Run all tests
    python run_all_tests.py -v           # Verbose output
    python run_all_tests.py --module novelty_engine  # Run specific module tests
"""

import sys
import os
import unittest
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_all_tests(verbosity=2):
    """Run all tests in the unit_tests directory."""
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=os.path.dirname(__file__),
        pattern='test_*.py'
    )

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    return result


def run_specific_module(module_name, verbosity=2):
    """Run tests for a specific module."""
    module_map = {
        'novelty_engine': 'test_novelty_engine',
        'critical_point': 'test_critical_point',
        'basic': 'test_basic_functionality'
    }

    if module_name not in module_map:
        print(f"Unknown module: {module_name}")
        print(f"Available modules: {', '.join(module_map.keys())}")
        return None

    test_module = module_map[module_name]

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(test_module)

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    return result


def print_summary(result):
    """Print a summary of test results."""
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    if result.wasSuccessful():
        print("\n✓ ALL TESTS PASSED!")
    else:
        print("\n✗ SOME TESTS FAILED")

    print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run unit tests for the Novelty Chess Engine'
    )
    parser.add_argument(
        '--module', '-m',
        help='Run tests for specific module (novelty_engine, critical_point, basic)',
        default=None
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Minimal output'
    )

    args = parser.parse_args()

    # Determine verbosity
    if args.quiet:
        verbosity = 0
    elif args.verbose:
        verbosity = 2
    else:
        verbosity = 1

    print("=" * 70)
    print("NOVELTY CHESS ENGINE - UNIT TESTS")
    print("=" * 70)

    if args.module:
        print(f"\nRunning tests for module: {args.module}\n")
        result = run_specific_module(args.module, verbosity=verbosity)
    else:
        print("\nRunning all tests...\n")
        result = run_all_tests(verbosity=verbosity)

    if result:
        print_summary(result)

        # Exit with appropriate code
        sys.exit(0 if result.wasSuccessful() else 1)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
