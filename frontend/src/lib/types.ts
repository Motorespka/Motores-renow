export type AccessProfile = {
  user_id: string;
  email: string;
  username: string;
  nome: string;
  display_name: string;
  role: string;
  plan: string;
  ativo: boolean;
  is_admin: boolean;
  cadastro_allowed: boolean;
  tier: string;
  source: string;
};

export type MeResponse = {
  authenticated: boolean;
  profile: AccessProfile;
};

export type MotorRecord = {
  id?: string | number;
  /** Ordem global na lista (ex.: #1, #2); não é o PK do Supabase. */
  cadastro_seq?: number;
  marca?: string;
  modelo?: string;
  potencia?: string;
  rpm?: string;
  [key: string]: unknown;
};

export type MotorListResponse = {
  mode: "teaser" | "full" | string;
  total: number;
  items: MotorRecord[];
};

export type MotorDetailResponse = {
  item: MotorRecord;
  raw: Record<string, unknown>;
};

export type AdminUser = {
  id: string;
  email?: string | null;
  username?: string | null;
  nome?: string | null;
  role?: string | null;
  plan?: string | null;
  ativo?: boolean | null;
};

export type CadastroAnalyzeResponse = {
  ok: boolean;
  message: string;
  file_count: number;
  file_names: string[];
  image_urls: string[];
  normalized_data: Record<string, unknown>;
  warnings: string[];
};

export type CadastroSaveResponse = {
  ok: boolean;
  message: string;
  strategy: string;
  inserted_id?: string | number | null;
  warnings: string[];
};

export type DiagnosticRecord = {
  id: string;
  motor_id: string;
  created_by: string;
  status: "pending" | "running" | "done" | "error" | string;
  score: number;
  summary: string;
  recommendations: Record<string, unknown>[];
  evidence: Record<string, unknown>;
  error: string;
  created_at?: string | null;
  updated_at?: string | null;
};

export type DiagnosticListResponse = {
  total: number;
  items: DiagnosticRecord[];
};

export type DiagnosticRunResponse = {
  ok: boolean;
  message: string;
  created: number;
  items: DiagnosticRecord[];
};

export type ConferenceRecord = {
  id: string;
  motor_id: string;
  created_by: string;
  status: "pending" | "approved" | "rejected" | string;
  confidence: number;
  diff: Record<string, unknown>;
  decision: Record<string, unknown>;
  decided_by?: string | null;
  decided_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type ConferenceListResponse = {
  total: number;
  items: ConferenceRecord[];
};

export type SettingsMeResponse = {
  ui_prefs: Record<string, unknown>;
  feature_flags: Record<string, unknown>;
};
