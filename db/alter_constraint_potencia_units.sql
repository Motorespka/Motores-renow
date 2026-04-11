begin;

alter table public.motores
  drop constraint if exists chk_motores_potencia;

alter table public.motores
  add constraint chk_motores_potencia
  check (
    potencia is null
    or potencia ~* '^[0-9]+([./][0-9]+)?\s*(cv|hp|kw|kva|kvw)$'
  );

commit;
