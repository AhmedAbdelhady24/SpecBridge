import type { ReactNode } from 'react';
export function ReviewPanel({ children }: {
  children: ReactNode;
}) {
  return <div className="review-task"><p>Read the draft alongside your review. Saving a new revision requires a fresh review and exact-package approval.</p>
    {children}</div>;
}
