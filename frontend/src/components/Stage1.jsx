import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import CopyButton from './CopyButton';
import './Stage1.css';

export default function Stage1({ responses }) {
  const [activeTab, setActiveTab] = useState(0);

  if (!responses || responses.length === 0) {
    return null;
  }

  const activeResponse = responses[activeTab];

  return (
    <div className="stage stage1">
      <h3 className="stage-title">Stage 1: Individual Responses</h3>

      <div className="tabs">
        {responses.map((resp, index) => (
          <button
            key={index}
            className={`tab ${activeTab === index ? 'active' : ''}`}
            onClick={() => setActiveTab(index)}
          >
            {resp.model.split('/')[1] || resp.model}
          </button>
        ))}
      </div>

      <div className="tab-content">
        <div className="response-header">
          <div className="model-name">{activeResponse.model}</div>
          <CopyButton text={activeResponse.response} />
        </div>
        <div className="response-text markdown-content">
          <ReactMarkdown>{activeResponse.response}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
