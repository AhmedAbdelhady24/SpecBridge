const evidenceLabels: Record<string, string> = {
  user_provided: 'Provided information',
  recommendation: 'Proposed wording',
  assumption: 'Assumption',
  unknown: 'Unresolved',
  verified: 'Marked verified',
};
export function evidenceLabel(kind: string): string {
  return Object.hasOwn(evidenceLabels, kind) ? evidenceLabels[kind] : kind.replaceAll('_', ' ');
}
