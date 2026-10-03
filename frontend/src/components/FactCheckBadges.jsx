import { useState, useEffect } from 'react';
import { api } from '../api';
import './FactCheckBadges.css';

export default function FactCheckBadges({ text, responses = null }) {
  const [citations, setCitations] = useState([]);
  const [claims, setClaims] = useState([]);
  const [validation, setValidation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showCitations, setShowCitations] = useState(false);
  const [showClaims, setShowClaims] = useState(false);
  const [showValidation, setShowValidation] = useState(false);

  useEffect(() => {
    if (text) {
      analyzeFacts();
    }
  }, [text]);

  const analyzeFacts = async () => {
    setLoading(true);
    try {
      // Extract citations
      const citationsData = await api.extractCitations(text);
      setCitations(citationsData);

      // Extract claims
      const claimsData = await api.extractClaims(text);
      setClaims(claimsData);

      // Cross-reference validation if multiple responses provided
      if (responses && responses.length > 1) {
        const validationData = await api.crossReferenceValidate(responses);
        setValidation(validationData);
      }
    } catch (error) {
      console.error('Failed to analyze facts:', error);
    } finally {
      setLoading(false);
    }
  };

  const getQualityBadgeClass = (quality) => {
    switch (quality) {
      case 'high': return 'quality-high';
      case 'medium': return 'quality-medium';
      case 'low': return 'quality-low';
      default: return 'quality-unknown';
    }
  };

  const getQualityLabel = (quality) => {
    switch (quality) {
      case 'high': return '🟢 High Quality';
      case 'medium': return '🟡 Medium Quality';
      case 'low': return '🔴 Low Quality';
      default: return '⚪ Unknown';
    }
  };

  const getClaimTypeLabel = (type) => {
    switch (type) {
      case 'statistical': return '📊 Statistical';
      case 'historical': return '📅 Historical';
      case 'definitional': return '📖 Definitional';
      case 'causal': return '🔗 Causal';
      case 'comparative': return '⚖️ Comparative';
      default: return '📝 Claim';
    }
  };

  const getConsensusLabel = (level) => {
    switch (level) {
      case 'high_consensus': return '✅ High Consensus';
      case 'moderate_consensus': return '⚠️ Moderate Consensus';
      case 'low_consensus': return '❌ Low Consensus';
      default: return '❓ Unknown';
    }
  };

  const hasFactCheckData = citations.length > 0 || claims.length > 0 || validation;

  if (loading) {
    return (
      <div className="fact-check-badges">
        <div className="fact-check-loading">🔍 Analyzing facts...</div>
      </div>
    );
  }

  if (!hasFactCheckData) {
    return null;
  }

  return (
    <div className="fact-check-badges">
      <div className="fact-check-header">
        <span className="fact-check-title">📋 Fact Check Analysis</span>
        <div className="fact-check-counts">
          {citations.length > 0 && (
            <button
              className={`count-badge ${showCitations ? 'active' : ''}`}
              onClick={() => setShowCitations(!showCitations)}
            >
              🔗 {citations.length} Citation{citations.length !== 1 ? 's' : ''}
            </button>
          )}
          {claims.length > 0 && (
            <button
              className={`count-badge ${showClaims ? 'active' : ''}`}
              onClick={() => setShowClaims(!showClaims)}
            >
              📝 {claims.length} Claim{claims.length !== 1 ? 's' : ''}
            </button>
          )}
          {validation && (
            <button
              className={`count-badge ${showValidation ? 'active' : ''}`}
              onClick={() => setShowValidation(!showValidation)}
            >
              🤝 Cross-Reference
            </button>
          )}
        </div>
      </div>

      {/* Citations Panel */}
      {showCitations && citations.length > 0 && (
        <div className="fact-check-panel">
          <h4>Citations</h4>
          <div className="citations-list">
            {citations.map((citation, idx) => (
              <div key={idx} className="citation-item">
                {citation.type === 'url' || citation.type === 'markdown_reference' ? (
                  <>
                    <span className={`quality-badge ${getQualityBadgeClass(citation.source_quality)}`}>
                      {getQualityLabel(citation.source_quality)}
                    </span>
                    <a
                      href={citation.value}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="citation-link"
                    >
                      {citation.domain || citation.value}
                    </a>
                    {citation.text && (
                      <span className="citation-text">"{citation.text}"</span>
                    )}
                  </>
                ) : citation.type === 'footnotes' ? (
                  <div className="footnote-info">
                    <span className="footnote-label">📌 Footnotes:</span>
                    <span className="footnote-count">{citation.count} reference(s)</span>
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Claims Panel */}
      {showClaims && claims.length > 0 && (
        <div className="fact-check-panel">
          <h4>Factual Claims</h4>
          <div className="claims-list">
            {claims.map((claim, idx) => (
              <div key={idx} className="claim-item">
                <div className="claim-header">
                  <span className="claim-type">{getClaimTypeLabel(claim.type)}</span>
                  <span className="verification-status">
                    {claim.verification_status === 'unverified' ? '⏳ Unverified' : '✓ Verified'}
                  </span>
                </div>
                <p className="claim-text">{claim.text}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cross-Reference Validation Panel */}
      {showValidation && validation && !validation.error && (
        <div className="fact-check-panel">
          <h4>Cross-Reference Validation</h4>

          <div className="validation-summary">
            <div className="consensus-indicator">
              <span className="consensus-label">Overall Consensus:</span>
              <span className={`consensus-badge ${validation.overall_assessment}`}>
                {getConsensusLabel(validation.overall_assessment)}
              </span>
            </div>
            <div className="consensus-score">
              <span className="score-label">Consensus Score:</span>
              <div className="score-bar">
                <div
                  className="score-fill"
                  style={{
                    width: `${validation.consensus_level * 100}%`,
                    backgroundColor: validation.consensus_level > 0.7 ? '#4caf50' :
                                     validation.consensus_level > 0.4 ? '#ffc107' : '#f44336'
                  }}
                />
                <span className="score-value">
                  {(validation.consensus_level * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>

          {validation.agreements && validation.agreements.length > 0 && (
            <div className="agreements-section">
              <h5>✅ Model Agreements ({validation.agreements.length})</h5>
              {validation.agreements.slice(0, 3).map((agreement, idx) => (
                <div key={idx} className="agreement-item">
                  <span className="model-pair">
                    {agreement.models.map(m => m.split('/')[1] || m).join(' & ')}
                  </span>
                  <span className="similarity-score">
                    {(agreement.similarity * 100).toFixed(0)}% similar
                  </span>
                </div>
              ))}
            </div>
          )}

          {validation.contradictions && validation.contradictions.length > 0 && (
            <div className="contradictions-section">
              <h5>⚠️ Potential Contradictions ({validation.contradictions.length})</h5>
              {validation.contradictions.slice(0, 3).map((contradiction, idx) => (
                <div key={idx} className="contradiction-item">
                  <span className="model-pair">
                    {contradiction.models.map(m => m.split('/')[1] || m).join(' vs ')}
                  </span>
                  <span className="similarity-score">
                    {(contradiction.similarity * 100).toFixed(0)}% similar
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {showValidation && validation?.error && (
        <div className="fact-check-panel">
          <div className="validation-error">
            ⚠️ {validation.error}
          </div>
        </div>
      )}
    </div>
  );
}
