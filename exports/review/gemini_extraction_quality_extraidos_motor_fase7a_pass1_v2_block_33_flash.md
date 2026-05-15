# Auditoria extração Gemini (determinística)

- Gerado: `2026-05-15T00:59:25Z`
- Entrada: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_33_flash_candidates.csv`
- Últimas linhas: **14**
- Total auditado: **14**

## Resumo

| Métrica | Valor |
|---|---:|
| Verdes sem alerta | 10 |
| Verdes com alerta | 0 |
| Amarelos | 4 |
| Vermelhos | 0 |

## Top motivos de alerta (todos os códigos)

- `S_pipeline_AMARELO_REVISAR`: **4**

## Top alertas críticos (prefixo `A`, heurísticas de campo)

- *(nenhum nos registros auditados)*

## Revisão manual sugerida

Arquivos com pelo menos um alerta **ou** status AMARELO/VERMELHO:

- `drive-download-20260403T124026Z-3-001_224929\605064006.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605065007.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605065008.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605066008.pdf`

## Saídas

- CSV: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_33_flash.csv`
- JSON: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_33_flash.json`