import './Skeleton.css';

/**
 * Skeleton loading placeholder component.
 * Shows animated placeholders while content is loading.
 */

export function Skeleton({ width, height, borderRadius = '4px', className = '' }) {
  return (
    <div
      className={`skeleton ${className}`}
      style={{
        width: width || '100%',
        height: height || '1em',
        borderRadius,
      }}
    />
  );
}

export function SkeletonText({ lines = 3, className = '' }) {
  return (
    <div className={`skeleton-text ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          width={i === lines - 1 ? '60%' : '100%'}
          height="1em"
          className="skeleton-line"
        />
      ))}
    </div>
  );
}

export function MessageSkeleton() {
  return (
    <div className="message-skeleton">
      <div className="skeleton-header">
        <Skeleton width="80px" height="14px" />
      </div>
      <div className="skeleton-body">
        <SkeletonText lines={4} />
      </div>
    </div>
  );
}

export function ConversationSkeleton() {
  return (
    <div className="conversation-skeleton">
      <Skeleton width="70%" height="16px" className="skeleton-title" />
      <Skeleton width="40%" height="12px" className="skeleton-meta" />
    </div>
  );
}

export function ResponseSkeleton() {
  return (
    <div className="response-skeleton">
      <div className="skeleton-tabs">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} width="80px" height="32px" borderRadius="4px" />
        ))}
      </div>
      <div className="skeleton-content">
        <SkeletonText lines={6} />
      </div>
    </div>
  );
}

export default Skeleton;
