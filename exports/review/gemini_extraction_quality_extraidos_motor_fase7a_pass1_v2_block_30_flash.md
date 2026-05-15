# Auditoria extração Gemini (determinística)

- Gerado: `2026-05-14T23:57:43Z`
- Entrada: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_30_flash_candidates.csv`
- Últimas linhas: **14**
- Total auditado: **14**

## Resumo

| Métrica | Valor |
|---|---:|
| Verdes sem alerta | 14 |
| Verdes com alerta | 0 |
| Amarelos | 0 |
| Vermelhos | 0 |

## Top motivos de alerta (todos os códigos)

- `A08_WARNING_rpm_leve_fora_faixa_mas_plausivel_2p_(2800-3700)_rpms=[2745, 3375]`: **1**

## Top alertas críticos (prefixo `A`, heurísticas de campo)

- *(nenhum nos registros auditados)*

## Revisão manual sugerida

Arquivos com pelo menos um alerta **ou** status AMARELO/VERMELHO:

- `drive-download-20260403T124026Z-3-001_224929\605057003.pdf`

## Saídas

- CSV: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_30_flash.csv`
- JSON: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_30_flash.json`