-- Opcional: backfill de `created_by` em linhas antigas (NULL) antes de endurecer RLS.
-- Ajuste o UUID e execute no SQL Editor do Supabase apenas se fizer sentido para a vossa organizacao.
--
-- Exemplo: atribuir todas as OS sem dono ao utilizador atual de manutencao:
-- update public.oficina_ordens_servico
--   set created_by = '00000000-0000-0000-0000-000000000000'::uuid
-- where created_by is null;
--
-- update public.rebobinagem_calculos
--   set created_by = '00000000-0000-0000-0000-000000000000'::uuid
-- where created_by is null;

select 1 as note_run_updates_manually_after_review;
