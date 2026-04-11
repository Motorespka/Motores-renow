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
