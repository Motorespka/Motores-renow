-- Moto-Renow / Uniao Motor API
-- Cycle 0026: tables for diagnostics, conferences, settings
-- Apply this SQL in Supabase (SQL editor) in the same project as `motores`.

begin;

-- Enable uuid generator (safe if already enabled)
create extension if not exists "pgcrypto";

-- -----------------------------
-- user_settings: per-user prefs
-- -----------------------------
create table if not exists public.user_settings (
  user_id uuid primary key,
  ui_prefs jsonb not null default '{}'::jsonb,
  feature_flags jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create index if not exists user_settings_updated_at_idx on public.user_settings (updated_at desc);

create or replace function public.user_settings_set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_user_settings_updated_at on public.user_settings;
create trigger trg_user_settings_updated_at
before update on public.user_settings
for each row execute function public.user_settings_set_updated_at();

-- ---------------------------------------
-- diagnostics: per-motor diagnostic record
-- ---------------------------------------
create table if not exists public.diagnostics (
  id uuid primary key default gen_random_uuid(),
  motor_id text not null,
  created_by uuid not null,
  status text not null default 'pending', -- pending|running|done|error
  score int not null default 0,           -- 0..100
  summary text not null default '',
  recommendations jsonb not null default '[]'::jsonb,
  evidence jsonb not null default '{}'::jsonb,
  error text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists diagnostics_motor_id_idx on public.diagnostics (motor_id);
create index if not exists diagnostics_created_by_idx on public.diagnostics (created_by);
create index if not exists diagnostics_status_idx on public.diagnostics (status);
create index if not exists diagnostics_created_at_idx on public.diagnostics (created_at desc);

create or replace function public.diagnostics_set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_diagnostics_updated_at on public.diagnostics;
create trigger trg_diagnostics_updated_at
before update on public.diagnostics
for each row execute function public.diagnostics_set_updated_at();

-- -----------------------------------
-- conferences: per-motor QA validation
-- -----------------------------------
create table if not exists public.conferences (
  id uuid primary key default gen_random_uuid(),
  motor_id text not null,
  created_by uuid not null,
  status text not null default 'pending', -- pending|approved|rejected
  confidence int not null default 0,       -- 0..100
  diff jsonb not null default '{}'::jsonb, -- OCR vs normalized diffs
  decision jsonb not null default '{}'::jsonb, -- {approved:boolean, reason, notes}
  decided_by uuid,
  decided_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists conferences_motor_id_idx on public.conferences (motor_id);
create index if not exists conferences_status_idx on public.conferences (status);
create index if not exists conferences_created_at_idx on public.conferences (created_at desc);

create or replace function public.conferences_set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_conferences_updated_at on public.conferences;
create trigger trg_conferences_updated_at
before update on public.conferences
for each row execute function public.conferences_set_updated_at();

commit;

