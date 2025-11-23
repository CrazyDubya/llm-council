#!/usr/bin/env python3
"""Comprehensive test suite for LLM Council - tests strategies, API, and edge cases."""

import asyncio
import json
from typing import Dict, List, Any
from backend.strategies import get_strategy, list_strategies
from backend.council import stage1_collect_responses, stage2_collect_rankings, stage3_synthesize_final
from backend.analytics import AnalyticsEngine
from backend.query_classifier import QueryClassifier
from backend.config import COUNCIL_MODELS, CHAIRMAN_MODEL


async def test_strategy_list():
    """Test listing available strategies."""
    print("\n" + "="*80)
    print("TEST 1: List Available Strategies")
    print("="*80)

    try:
        strategies = list_strategies()
        print(f"\n✓ Found {len(strategies)} strategies:")
        for name, info in strategies.items():
            print(f"  • {name}: {info['name']}")
            print(f"    {info['description']}")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


async def test_simple_ranking_strategy():
    """Test the simple ranking strategy (default)."""
    print("\n" + "="*80)
    print("TEST 2: Simple Ranking Strategy")
    print("="*80)

    query = "What is the best programming language for beginners?"

    try:
        strategy = get_strategy('simple')
        print(f"\n✓ Strategy instantiated: {strategy.get_name()}")
        print(f"  Description: {strategy.get_description()}")

        # Run the strategy with required parameters
        result = await strategy.execute(query, COUNCIL_MODELS, CHAIRMAN_MODEL)

        if result:
            print(f"\n✓ Strategy executed successfully")
            stage3 = result.get('stage3', {})
            answer = stage3.get('response', '') if isinstance(stage3, dict) else stage3
            print(f"  Final answer length: {len(answer)} chars")
            print(f"  Answer preview: {answer[:200]}...")
            return True
        else:
            print(f"✗ Strategy returned no result")
            return False

    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multi_round_strategy():
    """Test the multi-round strategy."""
    print("\n" + "="*80)
    print("TEST 3: Multi-Round Strategy")
    print("="*80)

    query = "Explain quantum computing in simple terms"

    try:
        strategy = get_strategy('multi_round')
        print(f"\n✓ Strategy instantiated: {strategy.get_name()}")
        print(f"  Description: {strategy.get_description()}")

        # Run the strategy with required parameters
        result = await strategy.execute(query, COUNCIL_MODELS, CHAIRMAN_MODEL)

        if result:
            print(f"\n✓ Strategy executed successfully")
            stage3 = result.get('stage3', {})
            answer = stage3.get('response', '') if isinstance(stage3, dict) else stage3
            print(f"  Final answer length: {len(answer)} chars")
            metadata = result.get('metadata', {})
            if 'rounds' in metadata:
                print(f"  Number of rounds: {metadata.get('rounds', 'N/A')}")
            return True
        else:
            print(f"✗ Strategy returned no result")
            return False

    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_weighted_voting_strategy():
    """Test the weighted voting strategy."""
    print("\n" + "="*80)
    print("TEST 4: Weighted Voting Strategy")
    print("="*80)

    query = "What makes a good software design?"

    try:
        strategy = get_strategy('weighted_voting')
        print(f"\n✓ Strategy instantiated: {strategy.get_name()}")
        print(f"  Description: {strategy.get_description()}")

        # Run the strategy with required parameters
        result = await strategy.execute(query, COUNCIL_MODELS, CHAIRMAN_MODEL)

        if result:
            print(f"\n✓ Strategy executed successfully")
            stage3 = result.get('stage3', {})
            answer = stage3.get('response', '') if isinstance(stage3, dict) else stage3
            print(f"  Final answer length: {len(answer)} chars")
            metadata = result.get('metadata', {})
            if 'voting_details' in metadata:
                print(f"  Voting info available: Yes")
            return True
        else:
            print(f"✗ Strategy returned no result")
            return False

    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_reasoning_aware_strategy():
    """Test the reasoning-aware strategy."""
    print("\n" + "="*80)
    print("TEST 5: Reasoning-Aware Strategy")
    print("="*80)

    query = "How should we approach solving complex problems?"

    try:
        strategy = get_strategy('reasoning_aware')
        print(f"\n✓ Strategy instantiated: {strategy.get_name()}")
        print(f"  Description: {strategy.get_description()}")

        # Run the strategy with required parameters
        result = await strategy.execute(query, COUNCIL_MODELS, CHAIRMAN_MODEL)

        if result:
            print(f"\n✓ Strategy executed successfully")
            stage3 = result.get('stage3', {})
            answer = stage3.get('response', '') if isinstance(stage3, dict) else stage3
            print(f"  Final answer length: {len(answer)} chars")
            metadata = result.get('metadata', {})
            if 'reasoning_traces' in metadata:
                print(f"  Reasoning traces available: Yes")
            return True
        else:
            print(f"✗ Strategy returned no result")
            return False

    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_query_classifier():
    """Test the query classifier."""
    print("\n" + "="*80)
    print("TEST 6: Query Classifier")
    print("="*80)

    test_queries = [
        "What is Python?",
        "How do I build a machine learning model?",
        "Write a quick sort algorithm",
        "What are the pros and cons of Docker?",
        "Explain how photosynthesis works"
    ]

    try:
        classifier = QueryClassifier()
        print(f"\n✓ Classifier initialized")

        classifications = {}
        for query in test_queries:
            # The classify method may not be async, call it directly
            classification = classifier.classify(query)
            classifications[query] = classification
            print(f"\n  Query: \"{query}\"")
            print(f"  Type: {classification.type if hasattr(classification, 'type') else 'unknown'}")
            print(f"  Complexity: {classification.complexity if hasattr(classification, 'complexity') else 'unknown'}")

        return True

    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_analytics_engine():
    """Test the analytics engine."""
    print("\n" + "="*80)
    print("TEST 7: Analytics Engine")
    print("="*80)

    try:
        analytics = AnalyticsEngine()
        print(f"\n✓ Analytics engine initialized")

        # Check available methods
        methods = [m for m in dir(analytics) if not m.startswith('_')]
        print(f"  Available methods: {', '.join(methods[:5])}")

        # Try to get statistics if available
        if hasattr(analytics, 'get_statistics'):
            stats = analytics.get_statistics() if not asyncio.iscoroutinefunction(analytics.get_statistics) else await analytics.get_statistics()
            print(f"  Statistics retrieved: {type(stats)}")

        return True

    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_handling():
    """Test error handling with invalid/edge case inputs."""
    print("\n" + "="*80)
    print("TEST 8: Error Handling & Edge Cases")
    print("="*80)

    test_cases = [
        ("Invalid strategy name", "nonexistent", True),
        ("Valid strategy", "simple", False),
    ]

    passed = 0
    failed = 0

    for test_name, strategy_name, should_fail in test_cases:
        try:
            strategy = get_strategy(strategy_name)

            if should_fail:
                print(f"\n✗ {test_name}: Should have failed but didn't")
                failed += 1
            else:
                print(f"\n✓ {test_name}: Retrieved successfully")
                passed += 1

        except ValueError as e:
            if should_fail:
                print(f"\n✓ {test_name}: Failed as expected ({type(e).__name__})")
                passed += 1
            else:
                print(f"\n✗ {test_name}: Unexpected error: {e}")
                failed += 1
        except Exception as e:
            print(f"\n✗ {test_name}: Unexpected error: {type(e).__name__}: {e}")
            failed += 1

    return failed == 0


async def test_strategy_comparison():
    """Test comparing multiple strategies on the same query."""
    print("\n" + "="*80)
    print("TEST 9: Strategy Comparison")
    print("="*80)

    query = "What is the difference between AI and machine learning?"
    strategies_to_compare = ["simple", "multi_round", "weighted_voting"]

    print(f"\nQuery: \"{query}\"")
    print(f"Strategies: {', '.join(strategies_to_compare)}")

    results = {}

    for strategy_name in strategies_to_compare:
        try:
            print(f"\n  Testing '{strategy_name}'...", end=" ", flush=True)
            strategy = get_strategy(strategy_name)
            result = await asyncio.wait_for(strategy.execute(query, COUNCIL_MODELS, CHAIRMAN_MODEL), timeout=120)

            if result:
                stage3 = result.get('stage3', {})
                answer = stage3.get('response', '') if isinstance(stage3, dict) else stage3
                results[strategy_name] = {
                    'success': True,
                    'answer_length': len(answer),
                    'answer_preview': answer[:150]
                }
                print("✓")
            else:
                results[strategy_name] = {'success': False}
                print("✗")

        except asyncio.TimeoutError:
            results[strategy_name] = {'success': False, 'error': 'Timeout'}
            print("✗ (Timeout)")
        except Exception as e:
            results[strategy_name] = {'success': False, 'error': str(e)}
            print(f"✗ ({type(e).__name__})")

    print(f"\n📊 Comparison Results:")
    for strategy_name, result in results.items():
        if result.get('success'):
            print(f"  • {strategy_name}: ✓ ({result['answer_length']} chars)")
        else:
            print(f"  • {strategy_name}: ✗ ({result.get('error', 'Failed')})")

    return all(r.get('success', False) for r in results.values())


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("🧪 LLM COUNCIL - COMPREHENSIVE TEST SUITE")
    print("="*80)

    tests = [
        ("List Strategies", test_strategy_list),
        ("Simple Ranking Strategy", test_simple_ranking_strategy),
        ("Multi-Round Strategy", test_multi_round_strategy),
        ("Weighted Voting Strategy", test_weighted_voting_strategy),
        ("Reasoning-Aware Strategy", test_reasoning_aware_strategy),
        ("Query Classifier", test_query_classifier),
        ("Analytics Engine", test_analytics_engine),
        ("Error Handling", test_error_handling),
        ("Strategy Comparison", test_strategy_comparison),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            passed = await test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n\n" + "="*80)
    print("📋 TEST SUMMARY")
    print("="*80)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")

    print("\n" + "="*80)
    print(f"Results: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("✓ All tests passed!")
        return 0
    else:
        print(f"✗ {total_count - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
