# Data Consistency Rules

## Objetivo
Validar qualidade de cadastro para diagnóstico técnico e consulta futura.

## Tipos de problema a detectar
- contradição entre campos críticos;
- ausência de campo essencial;
- valor provável, porém não confirmado;
- valor atípico sem contexto;
- estrutura ruim para busca futura;
- redundância confusa entre campos textuais e técnicos;
- inconsistência entre marca declarada e padrão observado;
- inconsistência entre tipo de motor e dados preenchidos.

## Fluxo de validação sugerido
1. Validar campos nucleares (potência, tensão, corrente, rpm, frequência, fase, ligação).
2. Validar campos de construção/aplicação (carcaça, montagem, uso).
3. Identificar conflitos e lacunas.
4. Classificar risco do cadastro (baixo, moderado, alto).
5. Gerar ações objetivas para correção.

## Regra de resposta
Sempre diferenciar:
- inconsistente confirmado;
- provável inconsistência (a confirmar);
- informação insuficiente para conclusão.
