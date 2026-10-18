import { type ReactNode } from 'react';
export type WorkspaceTask = 'questions' | 'changes' | 'review';
export function WorkspaceShell({ task, onTask, tasks, document, pane, onPane }: {
  task: WorkspaceTask;
  onTask: (task: WorkspaceTask) => void;
  tasks: ReactNode;
  document: ReactNode;
  pane: 'task' | 'draft';
  onPane: (pane: 'task' | 'draft') => void;
}) {
  return <div className={`focused-workspace mobile-${pane}`}>
    <nav className="mobile-pane-switch actions" aria-label="Workspace panes"><button type="button" aria-pressed={pane === 'task'} onClick={() => onPane('task')}>Task pane</button>
      <button type="button" aria-pressed={pane === 'draft'} onClick={() => onPane('draft')}>Draft pane</button></nav>
    <aside className="task-pane" aria-label="Feature tasks" tabIndex={0}>
      <nav className="task-nav" aria-label="Feature tasks">{([['questions', 'Questions'], ['changes', 'Changes'], ['review', 'Review & export']] as const).map(([key, label]) => <button type="button" key={key} className={task === key ? '' : 'secondary'} aria-pressed={task === key} onClick={() => onTask(key)}>{label}</button>)}</nav>
      {tasks}
    </aside>
    <section className="document-pane" aria-label="Complete specification" tabIndex={0}>{document}</section>
  </div>;
}
