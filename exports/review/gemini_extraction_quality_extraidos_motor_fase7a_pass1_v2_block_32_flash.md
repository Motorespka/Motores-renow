# Auditoria extração Gemini (determinística)

- Gerado: `2026-05-15T00:50:39Z`
- Entrada: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_32_flash_candidates.csv`
- Últimas linhas: **14**
- Total auditado: **14**

## Resumo

| Métrica | Valor |
|---|---:|
| Verdes sem alerta | 12 |
| Verdes com alerta | 0 |
| Amarelos | 2 |
| Vermelhos | 0 |

## Top motivos de alerta (todos os códigos)

- `S_pipeline_AMARELO_REVISAR`: **2**

## Top alertas críticos (prefixo `A`, heurísticas de campo)

- *(nenhum nos registros auditados)*

## Revisão manual sugerida

Arquivos com pelo menos um alerta **ou** status AMARELO/VERMELHO:

- `drive-download-20260403T124026Z-3-001_224929\605060004.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605061007.pdf`

## Saídas

- CSV: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_32_flash.csv`
- JSON: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_32_flash.json`