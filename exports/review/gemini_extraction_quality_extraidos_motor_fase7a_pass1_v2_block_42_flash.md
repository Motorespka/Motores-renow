# Auditoria extração Gemini (determinística)

- Gerado: `2026-05-16T19:40:53Z`
- Entrada: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_42_flash_candidates.csv`
- Últimas linhas: **14**
- Total auditado: **14**

## Resumo

| Métrica | Valor |
|---|---:|
| Verdes sem alerta | 9 |
| Verdes com alerta | 5 |
| Amarelos | 0 |
| Vermelhos | 0 |

## Top motivos de alerta (todos os códigos)

- `A07_potencia_decimal_sem_evidencia_frac_potencia_cv=12,5`: **4**
- `A08_rpm_fora_faixa_polos_4p_(1200-1900)_rpm=3583`: **1**

## Top alertas críticos (prefixo `A`, heurísticas de campo)

- `A07_potencia_decimal_sem_evidencia_frac_potencia_cv=12,5`: **4**
- `A08_rpm_fora_faixa_polos_4p_(1200-1900)_rpm=3583`: **1**

## Revisão manual sugerida

Arquivos com pelo menos um alerta **ou** status AMARELO/VERMELHO:

- `drive-download-20260403T124026Z-3-001_224929\605028115.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605028315.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605028715.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605029715.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605041001.pdf`

## Saídas

- CSV: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_42_flash.csv`
- JSON: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_42_flash.json`