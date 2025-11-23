#!/usr/bin/env python3
"""Test script for OpenRouter API functionality."""

import asyncio
import sys
from backend.openrouter import query_model, query_models_parallel
from backend.config import COUNCIL_MODELS, CHAIRMAN_MODEL, OPENROUTER_API_KEY


async def test_single_model():
    """Test querying a single model."""
    print("\n" + "="*60)
    print("TEST 1: Single Model Query")
    print("="*60)

    model = "openai/gpt-4o-mini"  # Using a cheaper model for testing
    messages = [
        {
            "role": "user",
            "content": "What is 2+2? Answer briefly."
        }
    ]

    print(f"\nQuerying model: {model}")
    response = await query_model(model, messages)

    if response:
        print(f"✓ Success!")
        print(f"  Content: {response.get('content', 'N/A')[:100]}...")
        if response.get('reasoning_details'):
            print(f"  Reasoning details present: Yes")
        return True
    else:
        print("✗ Failed to get response")
        return False


async def test_parallel_models():
    """Test querying multiple models in parallel."""
    print("\n" + "="*60)
    print("TEST 2: Parallel Model Query")
    print("="*60)

    test_models = [
        "openai/gpt-4o-mini",
        "anthropic/claude-3.5-haiku",
        "openai/gpt-4-turbo"
    ]

    messages = [
        {
            "role": "user",
            "content": "What is the capital of France? Answer briefly."
        }
    ]

    print(f"\nQuerying {len(test_models)} models in parallel...")
    for model in test_models:
        print(f"  - {model}")

    responses = await query_models_parallel(test_models, messages)

    successful = 0
    failed = 0

    for model, response in responses.items():
        if response:
            print(f"✓ {model}: Success")
            successful += 1
        else:
            print(f"✗ {model}: Failed")
            failed += 1

    print(f"\nResults: {successful} successful, {failed} failed")
    return failed == 0


async def test_council_models():
    """Test all configured council models."""
    print("\n" + "="*60)
    print("TEST 3: Council Model Configuration")
    print("="*60)

    print(f"\nConfigured council models ({len(COUNCIL_MODELS)}):")
    for model in COUNCIL_MODELS:
        print(f"  - {model}")

    print(f"\nChairman model: {CHAIRMAN_MODEL}")

    # Try a simple query with each council model
    messages = [
        {
            "role": "user",
            "content": "What is 1+1?"
        }
    ]

    print(f"\nTesting council models...")
    results = await query_models_parallel(COUNCIL_MODELS, messages)

    successful = 0
    failed = 0

    for model, response in results.items():
        if response:
            print(f"✓ {model}: Available")
            successful += 1
        else:
            print(f"✗ {model}: Failed/Unavailable")
            failed += 1

    print(f"\nResults: {successful}/{len(COUNCIL_MODELS)} available")
    return failed == 0


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("OpenRouter API Test Suite")
    print("="*60)

    # Check API key
    if not OPENROUTER_API_KEY:
        print("\n✗ ERROR: OPENROUTER_API_KEY not set!")
        print("  Please set the OPENROUTER_API_KEY environment variable.")
        sys.exit(1)

    print(f"\n✓ API Key configured (length: {len(OPENROUTER_API_KEY)})")

    # Run tests
    test_results = []

    try:
        test_results.append(("Single Model", await test_single_model()))
        test_results.append(("Parallel Models", await test_parallel_models()))
        test_results.append(("Council Models", await test_council_models()))
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, passed in test_results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")

    all_passed = all(result[1] for result in test_results)

    print("\n" + "="*60)
    if all_passed:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
