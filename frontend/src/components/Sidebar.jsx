import { useState, useEffect } from 'react';
import './Sidebar.css';

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onShowAnalytics,
  onShowModelBrowser,
  onShowTimeTravel,
  onSearch,
  onArchiveConversation,
  onUnarchiveConversation,
  onAddTag,
  onRemoveTag,
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [showArchived, setShowArchived] = useState(false);
  const [selectedTags, setSelectedTags] = useState([]);
  const [editingTags, setEditingTags] = useState(null);
  const [newTag, setNewTag] = useState('');

  // Get all unique tags from conversations
  const allTags = [...new Set(conversations.flatMap(c => c.tags || []))];

  // Handle search
  const handleSearch = (query) => {
    setSearchQuery(query);
    if (onSearch) {
      onSearch(query, selectedTags, showArchived);
    }
  };

  // Handle tag filter toggle
  const toggleTagFilter = (tag) => {
    const newSelectedTags = selectedTags.includes(tag)
      ? selectedTags.filter(t => t !== tag)
      : [...selectedTags, tag];
    setSelectedTags(newSelectedTags);
    if (onSearch) {
      onSearch(searchQuery, newSelectedTags, showArchived);
    }
  };

  // Handle show archived toggle
  const toggleShowArchived = () => {
    const newShowArchived = !showArchived;
    setShowArchived(newShowArchived);
    if (onSearch) {
      onSearch(searchQuery, selectedTags, newShowArchived);
    }
  };

  // Handle archive/unarchive
  const handleArchiveToggle = (e, conv) => {
    e.stopPropagation();
    if (conv.archived) {
      onUnarchiveConversation?.(conv.id);
    } else {
      onArchiveConversation?.(conv.id);
    }
  };

  // Handle add tag
  const handleAddTag = (convId) => {
    if (newTag.trim()) {
      onAddTag?.(convId, newTag.trim());
      setNewTag('');
    }
  };

  // Handle remove tag
  const handleRemoveTag = (convId, tag) => {
    onRemoveTag?.(convId, tag);
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h1>LLM Council</h1>
        <div className="sidebar-buttons">
          <button className="analytics-btn" onClick={onShowAnalytics} title="View Analytics">
            📊
          </button>
          <button className="analytics-btn" onClick={onShowModelBrowser} title="Model Browser">
            🤖
          </button>
          <button className="analytics-btn" onClick={onShowTimeTravel} title="Time-Travel Benchmarks">
            ⏱️
          </button>
          <button className="new-conversation-btn" onClick={onNewConversation}>
            + New
          </button>
        </div>
      </div>

      {/* Search bar */}
      <div className="search-container">
        <input
          type="text"
          className="search-input"
          placeholder="Search conversations..."
          value={searchQuery}
          onChange={(e) => handleSearch(e.target.value)}
        />
        {searchQuery && (
          <button
            className="search-clear"
            onClick={() => handleSearch('')}
            title="Clear search"
          >
            ✕
          </button>
        )}
      </div>

      {/* Filter controls */}
      <div className="filter-controls">
        <label className="archive-toggle">
          <input
            type="checkbox"
            checked={showArchived}
            onChange={toggleShowArchived}
          />
          <span>Show archived</span>
        </label>
      </div>

      {/* Tag filters */}
      {allTags.length > 0 && (
        <div className="tag-filters">
          <div className="tag-filters-label">Filter by tags:</div>
          <div className="tag-filter-list">
            {allTags.map(tag => (
              <button
                key={tag}
                className={`tag-filter-btn ${selectedTags.includes(tag) ? 'active' : ''}`}
                onClick={() => toggleTagFilter(tag)}
              >
                {tag}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Conversation list */}
      <div className="conversation-list">
        {conversations.length === 0 ? (
          <div className="no-conversations">
            {searchQuery || selectedTags.length > 0
              ? 'No matching conversations'
              : 'No conversations yet'}
          </div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`conversation-item ${
                conv.id === currentConversationId ? 'active' : ''
              } ${conv.archived ? 'archived' : ''}`}
              onClick={() => onSelectConversation(conv.id)}
            >
              <div className="conversation-header-row">
                <div className="conversation-title">
                  {conv.title || 'New Conversation'}
                  {conv.archived && <span className="archived-badge">📦</span>}
                </div>
                <button
                  className="archive-btn"
                  onClick={(e) => handleArchiveToggle(e, conv)}
                  title={conv.archived ? 'Unarchive' : 'Archive'}
                >
                  {conv.archived ? '📤' : '📥'}
                </button>
              </div>

              <div className="conversation-meta">
                {conv.message_count} messages
              </div>

              {/* Tags display */}
              {conv.tags && conv.tags.length > 0 && (
                <div className="conversation-tags">
                  {conv.tags.map(tag => (
                    <span key={tag} className="conversation-tag">
                      {tag}
                      {editingTags === conv.id && (
                        <button
                          className="tag-remove-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRemoveTag(conv.id, tag);
                          }}
                        >
                          ✕
                        </button>
                      )}
                    </span>
                  ))}
                </div>
              )}

              {/* Tag editing */}
              {editingTags === conv.id ? (
                <div className="tag-edit-container" onClick={(e) => e.stopPropagation()}>
                  <input
                    type="text"
                    className="tag-input"
                    placeholder="Add tag..."
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        handleAddTag(conv.id);
                      } else if (e.key === 'Escape') {
                        setEditingTags(null);
                        setNewTag('');
                      }
                    }}
                    autoFocus
                  />
                  <button
                    className="tag-add-btn"
                    onClick={() => handleAddTag(conv.id)}
                  >
                    Add
                  </button>
                  <button
                    className="tag-cancel-btn"
                    onClick={() => {
                      setEditingTags(null);
                      setNewTag('');
                    }}
                  >
                    Done
                  </button>
                </div>
              ) : (
                <button
                  className="tag-edit-trigger"
                  onClick={(e) => {
                    e.stopPropagation();
                    setEditingTags(conv.id);
                  }}
                >
                  🏷️ Tags
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
