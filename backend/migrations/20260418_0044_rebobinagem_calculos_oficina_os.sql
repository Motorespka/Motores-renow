-- Moto-Renow — Biblioteca de cálculos de rebobinagem + ordens de serviço (oficina)
-- Apply in Supabase SQL editor (same project as `motores`).
-- Cycle 0044

begin;

create extension if not exists "pgcrypto";

-- -----------------------------
-- rebobinagem_calculos: receitas reutilizáveis (pesquisa + revisões)
-- -----------------------------
create table if not exists public.rebobinagem_calculos (
  id uuid primary key default gen_random_uuid(),
  titulo text not null,
  notas text not null default '',
  tags text[] not null default '{}'::text[],
  fases text not null default '',
  potencia_cv double precision,
  rpm integer,
  polos integer,
  tensao_v double precision,
  ranhuras integer,
  payload jsonb not null default '{}'::jsonb,
  revision_of uuid references public.rebobinagem_calculos (id) on delete set null,
  revision_label text not null default '',
  created_by uuid,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists rebobinagem_calculos_updated_at_idx
  on public.rebobinagem_calculos (updated_at desc);

create index if not exists rebobinagem_calculos_tags_idx
  on public.rebobinagem_calculos using gin (tags);

create index if not exists rebobinagem_calculos_revision_of_idx
  on public.rebobinagem_calculos (revision_of);

create or replace function public.rebobinagem_calculos_set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_rebobinagem_calculos_updated_at on public.rebobinagem_calculos;
create trigger trg_rebobinagem_calculos_updated_at
before update on public.rebobinagem_calculos
for each row execute function public.rebobinagem_calculos_set_updated_at();

-- -----------------------------
-- oficina_ordens_servico: fluxo recebe → … → entrega
-- -----------------------------
create table if not exists public.oficina_ordens_servico (
  id uuid primary key default gen_random_uuid(),
  numero text not null unique,
  titulo text not null default '',
  motor_id text,
  etapa text not null default 'recebido',
  calc_id uuid references public.rebobinagem_calculos (id) on delete set null,
  payload jsonb not null default '{}'::jsonb,
  created_by uuid,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists oficina_os_motor_id_idx on public.oficina_ordens_servico (motor_id);
create index if not exists oficina_os_etapa_idx on public.oficina_ordens_servico (etapa);
create index if not exists oficina_os_updated_at_idx on public.oficina_ordens_servico (updated_at desc);

create or replace function public.oficina_ordens_servico_set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_oficina_os_updated_at on public.oficina_ordens_servico;
create trigger trg_oficina_os_updated_at
before update on public.oficina_ordens_servico
for each row execute function public.oficina_ordens_servico_set_updated_at();

commit;
