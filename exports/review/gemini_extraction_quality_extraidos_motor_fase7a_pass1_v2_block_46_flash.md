# Auditoria extração Gemini (determinística)

- Gerado: `2026-05-16T21:03:37Z`
- Entrada: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_46_flash_candidates.csv`
- Últimas linhas: **14**
- Total auditado: **14**

## Resumo

| Métrica | Valor |
|---|---:|
| Verdes sem alerta | 13 |
| Verdes com alerta | 0 |
| Amarelos | 1 |
| Vermelhos | 0 |

## Top motivos de alerta (todos os códigos)

- `A11_WARNING_diametro_normalizado_rastreavel`: **6**
- `A02_mono_sem_fio_espiras_passo_auxiliar`: **1**
- `A08_rpm_fora_faixa_polos_4p_(1200-1900)_rpm=790`: **1**
- `S_pipeline_AMARELO_REVISAR`: **1**

## Top alertas críticos (prefixo `A`, heurísticas de campo)

- `A02_mono_sem_fio_espiras_passo_auxiliar`: **1**
- `A08_rpm_fora_faixa_polos_4p_(1200-1900)_rpm=790`: **1**

## Revisão manual sugerida

Arquivos com pelo menos um alerta **ou** status AMARELO/VERMELHO:

- `drive-download-20260403T123335Z-3-001_145302\VOGE MONOFASICO CAP. PERMANENTE BK  1 2 CV-C 80 A -220- 6P.pdf`
- `drive-download-20260403T123335Z-3-001_145302\VOGE MONOFASICO CAP. PERMANENTE BK  1 2 CV-C80A -110-220- 6P.pdf`
- `drive-download-20260403T123335Z-3-001_145302\VOGE MONOFASICO CAP. PERMANENTE BK  1 2 CV-C80A -127- 6P.pdf`
- `drive-download-20260403T123335Z-3-001_145302\VOGE MONOFASICO CAP. PERMANENTE BK  3 4 CV-C80B -110-220- 6P.pdf`
- `drive-download-20260403T123335Z-3-001_145302\VOGE MONOFASICO CAP. PERMANENTE BK  3 4 CV-C80B -127- 6P.pdf`
- `drive-download-20260403T123335Z-3-001_145302\VOGE MONOFASICO CAP. PERMANENTE BK  3 4 CV-C80B -220- 6P.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1,8cv 4e8p nema42 2 50,60hz 30x68 605012085.pdf`

## Saídas

- CSV: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_46_flash.csv`
- JSON: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_46_flash.json`