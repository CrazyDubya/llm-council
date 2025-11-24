import { useState, useEffect } from 'react';
import { api } from '../api';
import './ModelBrowser.css';

export default function ModelBrowser({ onClose, onSelectModels }) {
  const [models, setModels] = useState([]);
  const [filteredModels, setFilteredModels] = useState([]);
  const [selectedModels, setSelectedModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [costEstimate, setCostEstimate] = useState(null);

  useEffect(() => {
    loadModels();
  }, []);

  useEffect(() => {
    filterModels();
  }, [models, searchTerm, categoryFilter]);

  useEffect(() => {
    if (selectedModels.length > 0) {
      estimateCost();
    } else {
      setCostEstimate(null);
    }
  }, [selectedModels]);

  const loadModels = async () => {
    try {
      const data = await api.listModels();
      setModels(data);
      setFilteredModels(data);
    } catch (error) {
      console.error('Failed to load models:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterModels = () => {
    let filtered = models;

    if (categoryFilter) {
      filtered = filtered.filter(m => m.category === categoryFilter);
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(
        m =>
          m.name?.toLowerCase().includes(term) ||
          m.id?.toLowerCase().includes(term) ||
          m.description?.toLowerCase().includes(term)
      );
    }

    setFilteredModels(filtered);
  };

  const estimateCost = async () => {
    try {
      const estimate = await api.estimateCost(selectedModels);
      setCostEstimate(estimate);
    } catch (error) {
      console.error('Failed to estimate cost:', error);
    }
  };

  const toggleModel = (modelId) => {
    setSelectedModels(prev =>
      prev.includes(modelId)
        ? prev.filter(id => id !== modelId)
        : [...prev, modelId]
    );
  };

  const handleApply = () => {
    if (selectedModels.length > 0) {
      onSelectModels(selectedModels);
      onClose();
    }
  };

  const getRecommendations = async () => {
    try {
      const recommended = await api.recommendCouncil(null, true, false);
      setSelectedModels(recommended);
    } catch (error) {
      console.error('Failed to get recommendations:', error);
    }
  };

  if (loading) {
    return (
      <div className="model-browser-overlay">
        <div className="model-browser">
          <div className="loading">Loading models...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="model-browser-overlay" onClick={onClose}>
      <div className="model-browser" onClick={(e) => e.stopPropagation()}>
        <div className="model-browser-header">
          <h2>Model Catalog</h2>
          <button className="close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="model-browser-controls">
          <input
            type="text"
            className="search-input"
            placeholder="Search models..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />

          <select
            className="category-filter"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option value="">All Categories</option>
            <option value="flagship">Flagship</option>
            <option value="budget">Budget</option>
            <option value="open_source">Open Source</option>
          </select>

          <button className="recommend-btn" onClick={getRecommendations}>
            🎯 Get Recommendations
          </button>
        </div>

        {selectedModels.length > 0 && (
          <div className="selected-models-bar">
            <div className="selected-count">
              {selectedModels.length} model{selectedModels.length !== 1 ? 's' : ''} selected
            </div>
            {costEstimate && (
              <div className="cost-estimate">
                Est. cost: ${costEstimate.total_cost.toFixed(6)} per query
              </div>
            )}
            <button className="clear-btn" onClick={() => setSelectedModels([])}>
              Clear
            </button>
          </div>
        )}

        <div className="model-list">
          {filteredModels.length === 0 ? (
            <div className="no-models">No models found</div>
          ) : (
            filteredModels.map((model) => (
              <div
                key={model.id}
                className={`model-card ${
                  selectedModels.includes(model.id) ? 'selected' : ''
                }`}
                onClick={() => toggleModel(model.id)}
              >
                <div className="model-card-header">
                  <div className="model-checkbox">
                    <input
                      type="checkbox"
                      checked={selectedModels.includes(model.id)}
                      onChange={() => {}}
                    />
                  </div>
                  <div className="model-info">
                    <div className="model-name">{model.name}</div>
                    <div className="model-id">{model.id}</div>
                  </div>
                  {model.category && (
                    <span className={`category-badge ${model.category}`}>
                      {model.category}
                    </span>
                  )}
                </div>

                {model.description && (
                  <div className="model-description">{model.description}</div>
                )}

                <div className="model-metadata">
                  {model.context_length && (
                    <span className="meta-item">
                      📏 {(model.context_length / 1000).toFixed(0)}K context
                    </span>
                  )}
                  {model.pricing?.prompt && (
                    <span className="meta-item">
                      💰 ${(parseFloat(model.pricing.prompt) * 1000000).toFixed(2)}/1M tokens
                    </span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        <div className="model-browser-footer">
          <button className="cancel-btn" onClick={onClose}>
            Cancel
          </button>
          <button
            className="apply-btn"
            onClick={handleApply}
            disabled={selectedModels.length === 0}
          >
            Apply Selection ({selectedModels.length})
          </button>
        </div>
      </div>
    </div>
  );
}
