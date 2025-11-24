"""Time-travel benchmarking utilities for comparing model performance over time."""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from . import storage
from .strategies import get_strategy
from .config import DATA_DIR


# Directory for time-travel benchmark data
BENCHMARK_DIR = Path(DATA_DIR).parent / "benchmarks"


def ensure_benchmark_dir():
    """Ensure the benchmark directory exists."""
    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)


def create_benchmark_snapshot(
    conversation_id: str,
    message_index: int,
    original_response: Dict[str, Any]
) -> str:
    """
    Create a snapshot of a conversation response for future comparison.

    Args:
        conversation_id: The conversation ID
        message_index: Index of the message in the conversation
        original_response: The original response data (stage1, stage2, stage3, metadata)

    Returns:
        Snapshot ID
    """
    ensure_benchmark_dir()

    snapshot_id = f"{conversation_id}_{message_index}_{int(datetime.utcnow().timestamp())}"

    # Load conversation to get the query
    conv = storage.get_conversation(conversation_id)
    if not conv or message_index >= len(conv['messages']):
        raise ValueError(f"Invalid conversation or message index")

    # Get the user message that prompted this response
    user_message = None
    for i in range(message_index, -1, -1):
        if conv['messages'][i]['role'] == 'user':
            user_message = conv['messages'][i]['content']
            break

    if not user_message:
        raise ValueError("No user message found before this response")

    snapshot = {
        'snapshot_id': snapshot_id,
        'conversation_id': conversation_id,
        'message_index': message_index,
        'created_at': datetime.utcnow().isoformat(),
        'query': user_message,
        'original_response': original_response,
        'reruns': []
    }

    snapshot_path = BENCHMARK_DIR / f"{snapshot_id}.json"
    with open(snapshot_path, 'w') as f:
        json.dump(snapshot, f, indent=2)

    return snapshot_id


async def rerun_benchmark(
    snapshot_id: str,
    models: List[str],
    chairman: str,
    strategy: str = 'simple'
) -> Dict[str, Any]:
    """
    Re-run a benchmarked query with current models and compare results.

    Args:
        snapshot_id: The snapshot ID to re-run
        models: List of model identifiers to use
        chairman: Chairman model identifier
        strategy: Strategy to use (default: 'simple')

    Returns:
        Comparison results with drift metrics
    """
    ensure_benchmark_dir()

    snapshot_path = BENCHMARK_DIR / f"{snapshot_id}.json"
    if not snapshot_path.exists():
        raise ValueError(f"Snapshot {snapshot_id} not found")

    with open(snapshot_path, 'r') as f:
        snapshot = json.load(f)

    # Execute the strategy with current models
    strategy_instance = get_strategy(strategy)
    new_result = await strategy_instance.execute(
        query=snapshot['query'],
        models=models,
        chairman=chairman
    )

    # Calculate drift metrics
    drift_metrics = calculate_drift_metrics(
        snapshot['original_response'],
        new_result
    )

    # Record the rerun
    rerun_record = {
        'rerun_at': datetime.utcnow().isoformat(),
        'models': models,
        'chairman': chairman,
        'strategy': strategy,
        'result': new_result,
        'drift_metrics': drift_metrics
    }

    snapshot['reruns'].append(rerun_record)

    # Save updated snapshot
    with open(snapshot_path, 'w') as f:
        json.dump(snapshot, f, indent=2)

    return {
        'snapshot': snapshot,
        'rerun': rerun_record,
        'comparison': {
            'original': snapshot['original_response'],
            'new': new_result,
            'drift': drift_metrics
        }
    }


def calculate_drift_metrics(
    original: Dict[str, Any],
    new: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate performance drift between original and new responses.

    Args:
        original: Original response data
        new: New response data

    Returns:
        Dictionary of drift metrics
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np

    metrics = {}

    # Response count drift
    orig_count = len(original.get('stage1', []))
    new_count = len(new.get('stage1', []))
    metrics['response_count_change'] = new_count - orig_count

    # Content similarity (if same models in same order)
    orig_stage1 = original.get('stage1', [])
    new_stage1 = new.get('stage1', [])

    if orig_stage1 and new_stage1:
        # Compare final answers (Stage 3)
        orig_final = original.get('stage3', {}).get('response', '')
        new_final = new.get('stage3', {}).get('response', '')

        if orig_final and new_final:
            vectorizer = TfidfVectorizer()
            try:
                vectors = vectorizer.fit_transform([orig_final, new_final])
                similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
                metrics['final_answer_similarity'] = float(similarity)
            except:
                metrics['final_answer_similarity'] = None

        # Compare individual model responses
        model_similarities = []
        for orig_resp, new_resp in zip(orig_stage1, new_stage1):
            if orig_resp.get('model') == new_resp.get('model'):
                orig_text = orig_resp.get('response', '')
                new_text = new_resp.get('response', '')

                if orig_text and new_text:
                    vectorizer = TfidfVectorizer()
                    try:
                        vectors = vectorizer.fit_transform([orig_text, new_text])
                        sim = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
                        model_similarities.append({
                            'model': orig_resp['model'],
                            'similarity': float(sim)
                        })
                    except:
                        pass

        metrics['model_similarities'] = model_similarities
        if model_similarities:
            metrics['average_model_similarity'] = float(
                np.mean([m['similarity'] for m in model_similarities])
            )

    # Ranking stability
    orig_rankings = original.get('metadata', {}).get('aggregate_rankings', [])
    new_rankings = new.get('metadata', {}).get('aggregate_rankings', [])

    if orig_rankings and new_rankings:
        # Create model -> rank mappings
        orig_rank_map = {r['model']: i for i, r in enumerate(orig_rankings)}
        new_rank_map = {r['model']: i for i, r in enumerate(new_rankings)}

        # Calculate rank changes for common models
        rank_changes = []
        for model in set(orig_rank_map.keys()) & set(new_rank_map.keys()):
            change = abs(orig_rank_map[model] - new_rank_map[model])
            rank_changes.append({
                'model': model,
                'rank_change': change,
                'original_rank': orig_rank_map[model] + 1,
                'new_rank': new_rank_map[model] + 1
            })

        metrics['ranking_changes'] = rank_changes
        if rank_changes:
            metrics['average_rank_change'] = float(
                np.mean([r['rank_change'] for r in rank_changes])
            )

    return metrics


def list_benchmarks() -> List[Dict[str, Any]]:
    """
    List all available benchmark snapshots.

    Returns:
        List of benchmark metadata
    """
    ensure_benchmark_dir()

    benchmarks = []
    for snapshot_file in BENCHMARK_DIR.glob("*.json"):
        with open(snapshot_file, 'r') as f:
            snapshot = json.load(f)
            benchmarks.append({
                'snapshot_id': snapshot['snapshot_id'],
                'conversation_id': snapshot['conversation_id'],
                'created_at': snapshot['created_at'],
                'query': snapshot['query'][:100] + '...' if len(snapshot['query']) > 100 else snapshot['query'],
                'rerun_count': len(snapshot['reruns'])
            })

    # Sort by creation date, newest first
    benchmarks.sort(key=lambda x: x['created_at'], reverse=True)

    return benchmarks


def get_benchmark(snapshot_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific benchmark snapshot.

    Args:
        snapshot_id: The snapshot ID

    Returns:
        Benchmark data or None if not found
    """
    ensure_benchmark_dir()

    snapshot_path = BENCHMARK_DIR / f"{snapshot_id}.json"
    if not snapshot_path.exists():
        return None

    with open(snapshot_path, 'r') as f:
        return json.load(f)
