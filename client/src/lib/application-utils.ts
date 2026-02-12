/**
 * Shared utils for job application state (applied job IDs persisted in localStorage).
 */

const APPLIED_JOBS_KEY = 'aiviue_applied_job_ids';

export function getAppliedJobIds(): Set<string> {
  if (typeof window === 'undefined') return new Set();
  try {
    const raw = localStorage.getItem(APPLIED_JOBS_KEY);
    const arr = raw ? JSON.parse(raw) : [];
    return new Set(Array.isArray(arr) ? arr : []);
  } catch {
    return new Set();
  }
}

export function addAppliedJobId(jobId: string): void {
  const set = getAppliedJobIds();
  set.add(jobId);
  localStorage.setItem(APPLIED_JOBS_KEY, JSON.stringify([...set]));
}
