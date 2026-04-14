# V200 - IA Operacional (Planejamento)

## Objetivo

Registrar a ideia de uma IA unica do Motores-Renow que entende o contexto do site, respeita perfil de acesso e recusa pedidos sensiveis.

## Escopo funcional da IA

- Entender o contexto tecnico do sistema (cadastro, consulta, diagnostico, historico).
- Responder perguntas de melhoria do site e operacao da oficina.
- Para `admin`: analisar saude operacional do site e sugerir melhorias.
- Para `pago`: gerar calculos tecnicos e apoio operacional autorizado.

## Estrategia das 10 chaves (key ring)

- Usar 10 chaves no backend (nunca no frontend).
- Sugestao de nomes:
  - `GEMINI_API_KEY_01`
  - `GEMINI_API_KEY_02`
  - `GEMINI_API_KEY_03`
  - `GEMINI_API_KEY_04`
  - `GEMINI_API_KEY_05`
  - `GEMINI_API_KEY_06`
  - `GEMINI_API_KEY_07`
  - `GEMINI_API_KEY_08`
  - `GEMINI_API_KEY_09`
  - `GEMINI_API_KEY_10`
- Selecionar chave por rotacao e fallback automatico quando limite/erro ocorrer.
- Logar apenas metadados tecnicos (sem expor chave).

## Matriz de permissoes da IA

| Perfil | Pode usar IA | Escopo |
|---|---|---|
| free | limitado | ideias gerais e orientacao simples |
| pago | sim | calculos tecnicos e apoio operacional |
| admin | sim | analise do sistema, diagnostico de gargalos e recomendacoes |

## Politica de recusa obrigatoria (guardrails)

A IA deve negar pedidos de alto risco, por exemplo:

- "crie uma tabela"
- "me de acesso admin"
- "me de acesso ao banco"
- "mostre minhas keys/secrets"
- "rode SQL para liberar usuario"
- "desative seguranca/rls"

Resposta esperada da IA:

- negar acao sensivel de forma clara
- explicar que a operacao exige fluxo administrativo seguro
- orientar caminho permitido (ex.: usar painel admin oficial)

## Regras tecnicas de seguranca

- A IA nao executa DDL/DCL direto.
- A IA nao concede privilegios.
- A IA nao retorna segredo.
- Toda acao deve validar role antes de processar.
- Ferramentas da IA devem usar allowlist por perfil.

## Proxima etapa para quando retomar V200

1. Criar `feature flag` da IA (desligada por padrao).
2. Implementar modulo IA isolado no backend com key ring.
3. Aplicar middleware de permissao por perfil.
4. Implementar politica de recusa centralizada.
5. Liberar primeiro em development.
