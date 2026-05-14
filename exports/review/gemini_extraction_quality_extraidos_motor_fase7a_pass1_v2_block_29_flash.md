# Auditoria extração Gemini (determinística)

- Gerado: `2026-05-14T22:57:36Z`
- Entrada: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_29_flash_candidates.csv`
- Últimas linhas: **14**
- Total auditado: **14**

## Resumo

| Métrica | Valor |
|---|---:|
| Verdes sem alerta | 11 |
| Verdes com alerta | 0 |
| Amarelos | 3 |
| Vermelhos | 0 |

## Top motivos de alerta (todos os códigos)

- `S_pipeline_AMARELO_REVISAR`: **3**

## Top alertas críticos (prefixo `A`, heurísticas de campo)

- *(nenhum nos registros auditados)*

## Revisão manual sugerida

Arquivos com pelo menos um alerta **ou** status AMARELO/VERMELHO:

- `drive-download-20260403T124026Z-3-001_224929\605046028.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605046031.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605052005.pdf`

## Saídas

- CSV: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_29_flash.csv`
- JSON: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_29_flash.json`