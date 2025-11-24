import { useState } from 'react';
import './ConsensusMap.css';

export default function ConsensusMap({ consensusMap }) {
  const [selectedNode, setSelectedNode] = useState(null);

  if (!consensusMap || !consensusMap.nodes || consensusMap.nodes.length === 0) {
    return null;
  }

  const { nodes, edges, stats, num_clusters } = consensusMap;

  // SVG dimensions
  const width = 600;
  const height = 400;
  const centerX = width / 2;
  const centerY = height / 2;

  // Arrange nodes in a circle
  const radius = Math.min(width, height) / 3;
  const angleStep = (2 * Math.PI) / nodes.length;

  const positionedNodes = nodes.map((node, index) => ({
    ...node,
    x: centerX + radius * Math.cos(index * angleStep - Math.PI / 2),
    y: centerY + radius * Math.sin(index * angleStep - Math.PI / 2)
  }));

  // Handle node click
  const handleNodeClick = (node) => {
    setSelectedNode(selectedNode?.id === node.id ? null : node);
  };

  return (
    <div className="consensus-map">
      <div className="consensus-header">
        <h3>Consensus Map</h3>
        <div className="consensus-stats">
          <span className="stat">
            {num_clusters} {num_clusters === 1 ? 'cluster' : 'clusters'}
          </span>
          <span className="stat">
            Avg similarity: {(stats.avg_similarity * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      <svg width={width} height={height} className="consensus-svg">
        {/* Draw edges first (so they appear behind nodes) */}
        {edges.map((edge, index) => {
          const source = positionedNodes.find(n => n.id === edge.source);
          const target = positionedNodes.find(n => n.id === edge.target);
          if (!source || !target) return null;

          return (
            <line
              key={`edge-${index}`}
              x1={source.x}
              y1={source.y}
              x2={target.x}
              y2={target.y}
              stroke={edge.color || '#ccc'}
              strokeWidth={edge.weight * 2}
              opacity={0.6}
            />
          );
        })}

        {/* Draw nodes */}
        {positionedNodes.map((node) => (
          <g
            key={node.id}
            onClick={() => handleNodeClick(node)}
            style={{ cursor: 'pointer' }}
            className={selectedNode?.id === node.id ? 'node-selected' : ''}
          >
            <circle
              cx={node.x}
              cy={node.y}
              r={node.size || 10}
              fill={node.color}
              stroke={selectedNode?.id === node.id ? '#333' : '#fff'}
              strokeWidth={selectedNode?.id === node.id ? 3 : 2}
            />
            <text
              x={node.x}
              y={node.y - 15}
              textAnchor="middle"
              fontSize="12"
              fontWeight="bold"
              fill="#333"
            >
              {node.label}
            </text>
          </g>
        ))}
      </svg>

      {/* Legend */}
      <div className="consensus-legend">
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#10b981' }}></div>
          <span>Cluster 0</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#3b82f6' }}></div>
          <span>Cluster 1</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#f59e0b' }}></div>
          <span>Cluster 2</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#ef4444' }}></div>
          <span>Outlier</span>
        </div>
      </div>

      {/* Selected node details */}
      {selectedNode && (
        <div className="node-details">
          <h4>{selectedNode.label}</h4>
          <p className="node-model">{selectedNode.model}</p>
          <p className="node-cluster">Cluster: {selectedNode.cluster}</p>
          <div className="node-content">
            {selectedNode.content.substring(0, 200)}
            {selectedNode.content.length > 200 && '...'}
          </div>
        </div>
      )}
    </div>
  );
}
