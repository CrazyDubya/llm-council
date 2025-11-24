"""Fact-checking and validation utilities for model responses."""

import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse


def extract_citations(text: str) -> List[Dict[str, str]]:
    """
    Extract citations (URLs and references) from text.

    Args:
        text: Text to extract citations from

    Returns:
        List of citation dictionaries with 'type' and 'value'
    """
    citations = []

    # Extract URLs
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, text)

    for url in urls:
        # Clean up trailing punctuation
        url = url.rstrip('.,;:!?)')

        citations.append({
            'type': 'url',
            'value': url,
            'domain': urlparse(url).netloc,
            'source_quality': assess_source_quality(url)
        })

    # Extract markdown-style references [text](url) or [^1] style
    markdown_refs = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', text)
    for ref_text, ref_url in markdown_refs:
        if ref_url not in urls:  # Don't duplicate
            citations.append({
                'type': 'markdown_reference',
                'value': ref_url,
                'text': ref_text,
                'domain': urlparse(ref_url).netloc if ref_url.startswith('http') else None,
                'source_quality': assess_source_quality(ref_url) if ref_url.startswith('http') else 'unknown'
            })

    # Extract footnote-style references [1], [2], etc.
    footnotes = re.findall(r'\[(\d+)\]', text)
    if footnotes:
        citations.append({
            'type': 'footnotes',
            'value': footnotes,
            'count': len(set(footnotes))
        })

    return citations


def assess_source_quality(url: str) -> str:
    """
    Assess the quality/reliability of a source based on domain.

    Args:
        url: The URL to assess

    Returns:
        Quality rating: 'high', 'medium', 'low', 'unknown'
    """
    domain = urlparse(url).netloc.lower()

    # High-quality academic and authoritative sources
    high_quality_domains = [
        'edu', 'gov', 'ieee.org', 'acm.org', 'springer.com',
        'nature.com', 'science.org', 'arxiv.org', 'ncbi.nlm.nih.gov',
        'who.int', 'cdc.gov', 'nih.gov'
    ]

    # Medium-quality news and reference sources
    medium_quality_domains = [
        'reuters.com', 'apnews.com', 'bbc.com', 'wikipedia.org',
        'britannica.com', 'nytimes.com', 'washingtonpost.com',
        'theguardian.com', 'wsj.com'
    ]

    for hq_domain in high_quality_domains:
        if hq_domain in domain:
            return 'high'

    for mq_domain in medium_quality_domains:
        if mq_domain in domain:
            return 'medium'

    # Check for .edu or .gov TLDs
    if domain.endswith('.edu') or domain.endswith('.gov'):
        return 'high'

    # Blog platforms and user-generated content
    low_quality_indicators = ['blogspot', 'wordpress', 'medium.com', 'reddit.com']
    for lq_indicator in low_quality_indicators:
        if lq_indicator in domain:
            return 'low'

    return 'unknown'


def extract_claims(text: str) -> List[Dict[str, Any]]:
    """
    Extract factual claims from text for verification.

    Uses simple heuristics to identify statements that could be fact-checked.

    Args:
        text: Text to extract claims from

    Returns:
        List of claim dictionaries
    """
    claims = []

    # Split into sentences
    sentences = re.split(r'[.!?]+', text)

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence or len(sentence) < 20:
            continue

        # Identify potential factual claims
        claim_type = identify_claim_type(sentence)

        if claim_type:
            claims.append({
                'text': sentence,
                'type': claim_type,
                'verification_status': 'unverified',  # Would be updated by external API
                'confidence': None  # Would be set by verification service
            })

    return claims


def identify_claim_type(sentence: str) -> Optional[str]:
    """
    Identify if a sentence contains a factual claim and what type.

    Args:
        sentence: The sentence to analyze

    Returns:
        Claim type or None if no claim detected
    """
    sentence_lower = sentence.lower()

    # Statistical claims (numbers, percentages)
    if re.search(r'\d+%|\d+\s*(percent|million|billion|thousand)', sentence_lower):
        return 'statistical'

    # Historical claims (dates, years, "in YYYY")
    if re.search(r'\b(19|20)\d{2}\b|in\s+\d{4}|on\s+\w+\s+\d{1,2}', sentence):
        return 'historical'

    # Definitional claims ("is", "are", "was", "were")
    if re.search(r'\b(is|are|was|were)\s+(the|a|an)\s+\w+', sentence_lower):
        # But filter out subjective statements
        subjective_words = ['good', 'bad', 'best', 'worst', 'better', 'worse', 'should', 'might', 'could']
        if not any(word in sentence_lower for word in subjective_words):
            return 'definitional'

    # Causal claims ("causes", "leads to", "results in")
    if re.search(r'\b(causes?|leads?\s+to|results?\s+in|because\s+of)\b', sentence_lower):
        return 'causal'

    # Comparative claims ("more than", "less than", "higher than")
    if re.search(r'\b(more|less|higher|lower|greater|smaller)\s+than\b', sentence_lower):
        return 'comparative'

    return None


def cross_reference_validate(
    responses: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Validate consistency across multiple model responses.

    Identifies statements that are consistent across models vs. contradictory.

    Args:
        responses: List of response dictionaries with 'model' and 'response' keys

    Returns:
        Validation results with consistency metrics
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np

    if len(responses) < 2:
        return {'error': 'Need at least 2 responses for cross-reference validation'}

    # Extract all text
    texts = [r.get('response', '') for r in responses]
    models = [r.get('model', f'Model {i}') for i, r in enumerate(responses)]

    # Calculate pairwise similarities
    vectorizer = TfidfVectorizer()
    try:
        vectors = vectorizer.fit_transform(texts)
        similarity_matrix = cosine_similarity(vectors)

        # Find agreeing pairs (high similarity)
        agreements = []
        contradictions = []

        for i in range(len(responses)):
            for j in range(i + 1, len(responses)):
                sim = similarity_matrix[i][j]

                if sim > 0.7:  # High agreement
                    agreements.append({
                        'models': [models[i], models[j]],
                        'similarity': float(sim),
                        'type': 'agreement'
                    })
                elif sim < 0.3:  # Low similarity, potential contradiction
                    contradictions.append({
                        'models': [models[i], models[j]],
                        'similarity': float(sim),
                        'type': 'contradiction'
                    })

        # Calculate overall consensus
        avg_similarity = float(np.mean(similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)]))

        return {
            'consensus_level': avg_similarity,
            'agreements': agreements,
            'contradictions': contradictions,
            'overall_assessment': (
                'high_consensus' if avg_similarity > 0.7 else
                'moderate_consensus' if avg_similarity > 0.4 else
                'low_consensus'
            )
        }

    except Exception as e:
        return {'error': f'Cross-reference validation failed: {str(e)}'}


def extract_numerical_claims(text: str) -> List[Dict[str, Any]]:
    """
    Extract numerical claims from text for fact-checking.

    Args:
        text: Text to extract from

    Returns:
        List of numerical claims with values and context
    """
    claims = []

    # Pattern for percentages
    percentage_pattern = r'(\d+(?:\.\d+)?)\s*(%|percent)'
    percentage_matches = re.finditer(percentage_pattern, text, re.IGNORECASE)

    for match in percentage_matches:
        # Get context (surrounding words)
        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        context = text[start:end].strip()

        claims.append({
            'type': 'percentage',
            'value': float(match.group(1)),
            'context': context,
            'position': match.start()
        })

    # Pattern for large numbers with units
    number_pattern = r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(million|billion|thousand|trillion)'
    number_matches = re.finditer(number_pattern, text, re.IGNORECASE)

    for match in number_matches:
        value = float(match.group(1).replace(',', ''))
        unit = match.group(2).lower()

        # Convert to actual number
        multipliers = {'thousand': 1e3, 'million': 1e6, 'billion': 1e9, 'trillion': 1e12}
        actual_value = value * multipliers.get(unit, 1)

        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        context = text[start:end].strip()

        claims.append({
            'type': 'large_number',
            'value': actual_value,
            'formatted_value': f"{value} {unit}",
            'context': context,
            'position': match.start()
        })

    return claims


async def verify_claim_external(claim: str) -> Dict[str, Any]:
    """
    Verify a claim using external fact-checking APIs.

    This is a stub that can be integrated with services like:
    - Google Fact Check Tools API
    - ClaimReview structured data
    - FactCheckAPI.org

    Args:
        claim: The claim to verify

    Returns:
        Verification result
    """
    # TODO: Integrate with actual fact-checking API
    # For now, return a stub response

    return {
        'claim': claim,
        'status': 'not_verified',
        'message': 'External fact-checking API not configured',
        'suggested_action': 'Manual verification recommended'
    }
