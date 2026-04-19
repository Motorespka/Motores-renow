-- Moto-Renow — RLS para biblioteca de cálculos + ordens de serviço (oficina)
-- Aplicar no Supabase SQL editor após 0044. Requer login (JWT) com role authenticated.
-- Linhas com created_by NULL continuam visíveis a qualquer utilizador autenticado (migração legada);
--   faça backfill de created_by se quiser restringir.

begin;

alter table if exists public.rebobinagem_calculos enable row level security;
alter table if exists public.oficina_ordens_servico enable row level security;

drop policy if exists "rebob_calc_select" on public.rebobinagem_calculos;
drop policy if exists "rebob_calc_insert" on public.rebobinagem_calculos;
drop policy if exists "rebob_calc_update" on public.rebobinagem_calculos;
drop policy if exists "rebob_calc_delete" on public.rebobinagem_calculos;

create policy "rebob_calc_select"
  on public.rebobinagem_calculos for select to authenticated
  using (created_by is null or created_by = auth.uid());

create policy "rebob_calc_insert"
  on public.rebobinagem_calculos for insert to authenticated
  with check (created_by is null or created_by = auth.uid());

create policy "rebob_calc_update"
  on public.rebobinagem_calculos for update to authenticated
  using (created_by is null or created_by = auth.uid())
  with check (created_by is null or created_by = auth.uid());

create policy "rebob_calc_delete"
  on public.rebobinagem_calculos for delete to authenticated
  using (created_by is null or created_by = auth.uid());

drop policy if exists "oficina_os_select" on public.oficina_ordens_servico;
drop policy if exists "oficina_os_insert" on public.oficina_ordens_servico;
drop policy if exists "oficina_os_update" on public.oficina_ordens_servico;
drop policy if exists "oficina_os_delete" on public.oficina_ordens_servico;

create policy "oficina_os_select"
  on public.oficina_ordens_servico for select to authenticated
  using (created_by is null or created_by = auth.uid());

create policy "oficina_os_insert"
  on public.oficina_ordens_servico for insert to authenticated
  with check (created_by is null or created_by = auth.uid());

create policy "oficina_os_update"
  on public.oficina_ordens_servico for update to authenticated
  using (created_by is null or created_by = auth.uid())
  with check (created_by is null or created_by = auth.uid());

create policy "oficina_os_delete"
  on public.oficina_ordens_servico for delete to authenticated
  using (created_by is null or created_by = auth.uid());

commit;
