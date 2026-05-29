export interface Company {
  id: string;
  name_legal: string;
  name_commercial: string | null;
  description: string | null;
  created_at: string;
}

export interface Program {
  id: string;
  company_id: string;
  name: string;
  program_type: string;
  platform: string;
  program_url: string | null;
  status: string;
  scope_last_reviewed_at: string | null;
  created_at: string;
}

export interface Audit {
  id: string;
  program_id: string;
  title: string;
  objective: string | null;
  status: string;
  created_at: string;
}

export interface Asset {
  id: string;
  value: string;
  asset_type: string;
  discovered_via: string | null;
  scope_decision: string;
  score: number;
  confidence: string;
  review_status: string;
  first_seen: string;
  last_seen: string;
}

export interface ScanJob {
  id: string;
  mode: string;
  status: string;
  dry_run: boolean;
  summary: Record<string, unknown> | null;
  created_at: string;
}

export interface ScopeSummary {
  allowed: string[];
  forbidden: string[];
  ambiguous: string[];
  requires_review: string[];
  rules: string[];
  counts: Record<string, number>;
}

export interface DryRunResult {
  mode: string;
  eligible_targets: string[];
  blocked_targets: { target: string; decision: string }[];
  sources: string[];
  note: string;
}
