"""Consensus mapping utilities for visualizing model agreement/disagreement."""

import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN
import asyncio
import httpx
from .config import OPENROUTER_API_KEY


async def get_embeddings(texts: List[str]) -> np.ndarray:
    """
    Get embeddings for a list of texts using a simple method.

    For v0.3, we use TF-IDF vectors as a lightweight alternative to API embeddings.
    This avoids additional API costs and latency while providing good similarity scores.

    Args:
        texts: List of text strings to embed

    Returns:
        NumPy array of embeddings (n_texts, embedding_dim)
    """
    # Use TF-IDF as lightweight embedding alternative
    vectorizer = TfidfVectorizer(
        max_features=300,  # Limit dimensionality
        ngram_range=(1, 2),  # Use unigrams and bigrams
        min_df=1,
        stop_words='english'
    )

    try:
        embeddings = vectorizer.fit_transform(texts).toarray()
        return embeddings
    except Exception as e:
        # Fallback: return zero vectors if TF-IDF fails
        return np.zeros((len(texts), 300))


def compute_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """
    Compute pairwise cosine similarity between embeddings.

    Args:
        embeddings: NumPy array of embeddings

    Returns:
        Similarity matrix (n x n)
    """
    return cosine_similarity(embeddings)


def detect_clusters(
    similarity_matrix: np.ndarray,
    eps: float = 0.3,
    min_samples: int = 2
) -> np.ndarray:
    """
    Detect clusters using DBSCAN on similarity matrix.

    Args:
        similarity_matrix: Pairwise similarity matrix
        eps: Maximum distance between samples in cluster
        min_samples: Minimum samples for a cluster

    Returns:
        Cluster labels (-1 for outliers, 0+ for clusters)
    """
    # Convert similarity to distance
    distance_matrix = 1 - similarity_matrix

    # Run DBSCAN
    clustering = DBSCAN(
        eps=eps,
        min_samples=min_samples,
        metric='precomputed'
    )
    labels = clustering.fit_predict(distance_matrix)

    return labels


def create_consensus_graph(
    responses: List[Dict[str, Any]],
    similarity_matrix: np.ndarray,
    cluster_labels: np.ndarray,
    threshold: float = 0.5
) -> Dict[str, Any]:
    """
    Create graph data structure for consensus visualization.

    Args:
        responses: List of model responses with 'model' and 'content' keys
        similarity_matrix: Pairwise similarity matrix
        cluster_labels: Cluster assignments from DBSCAN
        threshold: Minimum similarity to create an edge

    Returns:
        Dictionary with 'nodes' and 'edges' for visualization
    """
    nodes = []
    edges = []

    # Create nodes
    for i, response in enumerate(responses):
        # Determine node color based on cluster
        cluster = int(cluster_labels[i])
        if cluster == -1:
            color = '#ef4444'  # Red for outliers
            cluster_name = 'outlier'
        else:
            # Use different colors for different clusters
            colors = ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899']
            color = colors[cluster % len(colors)]
            cluster_name = f'cluster_{cluster}'

        nodes.append({
            'id': str(i),
            'label': response.get('model', f'Model {i}'),
            'model': response.get('model', ''),
            'content': response.get('content', ''),
            'cluster': cluster_name,
            'color': color,
            'size': 10  # Can be adjusted based on ranking or other metrics
        })

    # Create edges (only for similarities above threshold)
    for i in range(len(responses)):
        for j in range(i + 1, len(responses)):
            sim = similarity_matrix[i][j]
            if sim >= threshold:
                edges.append({
                    'source': str(i),
                    'target': str(j),
                    'weight': float(sim),
                    'color': f'rgba(100, 100, 100, {sim})'  # Opacity based on similarity
                })

    return {
        'nodes': nodes,
        'edges': edges,
        'num_clusters': len(set(cluster_labels[cluster_labels >= 0]))
    }


async def build_consensus_map(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build complete consensus map with similarity scoring and clustering.

    Args:
        responses: List of model responses, each with 'model' and 'content'

    Returns:
        Dictionary with consensus map data including nodes, edges, and metadata
    """
    # Extract text content
    texts = [r.get('content', '') for r in responses]

    # Get embeddings
    embeddings = await get_embeddings(texts)

    # Compute similarity
    similarity_matrix = compute_similarity_matrix(embeddings)

    # Detect clusters
    cluster_labels = detect_clusters(similarity_matrix)

    # Create graph
    graph = create_consensus_graph(responses, similarity_matrix, cluster_labels)

    # Compute aggregate statistics
    avg_similarity = float(np.mean(similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)]))
    max_similarity = float(np.max(similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)]))
    min_similarity = float(np.min(similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)]))

    return {
        **graph,
        'stats': {
            'avg_similarity': avg_similarity,
            'max_similarity': max_similarity,
            'min_similarity': min_similarity,
            'num_responses': len(responses)
        }
    }
