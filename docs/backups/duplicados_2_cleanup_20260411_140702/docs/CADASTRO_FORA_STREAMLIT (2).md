# Cadastro Fora do Streamlit (Etapa C)

## O que foi implementado

- Backend:
  - `POST /api/cadastro/analyze`
    - recebe upload multipart
    - valida tipo e tamanho de arquivo
    - executa Gemini no backend
    - tenta upload em bucket Supabase
    - retorna `normalized_data`, `warnings`, `image_urls`
  - `POST /api/cadastro/save`
    - recebe JSON revisado
    - enriquece com metadata de autor (`cadastrado_por_*`)
    - salva em `motores` com estrategias de fallback
- Frontend:
  - tela `frontend/src/app/cadastro/page.tsx`
  - upload de imagens
  - botao de analise
  - edicao/revisao do JSON tecnico
  - botao de salvar

## Permissao e seguranca

- Acesso protegido no backend com `require_cadastro`.
- `cadastro_allowed` calculado no backend por:
  - admin
  - plano pago
  - liberacao manual em `cadastro_access`
- Gemini key usada somente no backend (`GEMINI_API_KEY`).
- Frontend nunca recebe `service_role` nem `GEMINI_API_KEY`.

## Pendencias reais

- Adicionar rate limit em endpoints de cadastro (proteção de custo).
- Revisar policies RLS para insert em `motores` e leitura em `cadastro_access`.
- Ampliar validacao de conteudo (alem de mime/extensao/tamanho).
- Migrar UX completa do cadastro legado (mais campos e wizard detalhado).

## Riscos identificados

- Sem rate limit, upload/analise pode ser abusado e gerar custo no Gemini.
- Se policy RLS estiver permissiva demais, pode haver gravação indevida.
- Se bucket storage estiver publico sem controle, pode expor imagens sensiveis.
