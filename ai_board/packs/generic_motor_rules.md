# Generic Motor Rules

## Objetivo operacional
Base de raciocínio para manutenção, bancada/oficina, rebobinagem, cadastro técnico e consulta técnica quando dados de marca/modelo não forem suficientes.

## A) Identificação básica de motor
- Diferenciar motor monofásico e trifásico por indicação explícita, tipo de ligação, tensão nominal e contexto de aplicação.
- Tratar potência, tensão, corrente, frequência e rotação como bloco interdependente (não validar campo isolado).
- Usar noção prática de polos e rpm como teste de sanidade, considerando variações por escorregamento e condição real.
- Validar coerência básica CV ↔ kW (conversão aproximada), preservando sempre o valor original informado no cadastro.
- Distinguir cenários de aplicação leve/comercial e industrial para evitar recomendações incompatíveis com uso real.
- Considerar carcaça, aplicação e construção do conjunto antes de concluir equivalência.

## B) Coerência entre campos (checklist obrigatório)
Sempre avaliar:
1. Potência combina com corrente e tensão informadas?
2. Rotação é coerente com polos e frequência prováveis?
3. Tensão e tipo de motor parecem compatíveis?
4. Frequência está coerente com os demais campos?
5. Existem campos críticos ausentes (ex.: potência, tensão, rpm, ligação, carcaça)?
6. Há contradição entre nome/modelo e dados técnicos?

## C) Motores antigos, recondicionados e incompletos
- Em placa ruim/incompleta: reduzir confiança e elevar necessidade de revisão humana.
- Em cadastro incompleto: priorizar triagem (o que falta) antes de conclusão técnica.
- Em motor remontado/recondicionado: considerar possibilidade de peças trocadas e divergência entre placa e bancada.
- Em motor sem marca clara: aplicar regras genéricas e marcar inferências como hipótese.
- Em motor com marca declarada mas padrão estranho: não forçar encaixe de marca; revisar evidências físicas e históricas.

## D) Regra de cautela (formato obrigatório de resposta)
Separar sempre:
- **Fato observado:** dado explícito do cadastro, foto, placa ou medição.
- **Padrão provável:** comportamento comum de mercado/oficina.
- **Hipótese técnica:** inferência ainda não confirmada.
- **Recomendação de verificação:** ação concreta para validar hipótese.

## E) Regras de oficina e consulta rápida
- Priorizar primeiros campos que técnico experiente confere: potência, tensão, corrente, rpm, polos, frequência, ligação, carcaça e aplicação.
- Sinalizar cadastro suspeito quando houver conflito evidente entre campos nucleares.
- Tratar leitura mal feita como risco operacional (não como erro definitivo sem revisão).
- Destacar em consulta rápida o que impacta decisão imediata de manutenção/substituição.
- Em dúvida relevante, recomendar revisão humana antes de decisão comercial/técnica final.
