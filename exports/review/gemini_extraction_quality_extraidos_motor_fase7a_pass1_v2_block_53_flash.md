# Auditoria extração Gemini (determinística)

- Gerado: `2026-05-17T18:39:47Z`
- Entrada: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_53_flash_candidates.csv`
- Últimas linhas: **14**
- Total auditado: **14**

## Resumo

| Métrica | Valor |
|---|---:|
| Verdes sem alerta | 10 |
| Verdes com alerta | 3 |
| Amarelos | 1 |
| Vermelhos | 0 |

## Top motivos de alerta (todos os códigos)

- `A02_mono_sem_fio_espiras_passo_auxiliar`: **1**
- `A08_rpm_fora_faixa_polos_4p_(1200-1900)_rpm=790`: **1**
- `S_pipeline_AMARELO_REVISAR`: **1**
- `A08_rpm_absoluto_absurdo_rpm=14000`: **1**
- `A08_rpm_absoluto_absurdo_rpm=15190`: **1**
- `A08_rpm_fora_faixa_polos_4p_(1200-1900)_rpm=3225`: **1**

## Top alertas críticos (prefixo `A`, heurísticas de campo)

- `A02_mono_sem_fio_espiras_passo_auxiliar`: **1**
- `A08_rpm_fora_faixa_polos_4p_(1200-1900)_rpm=790`: **1**
- `A08_rpm_absoluto_absurdo_rpm=14000`: **1**
- `A08_rpm_absoluto_absurdo_rpm=15190`: **1**
- `A08_rpm_fora_faixa_polos_4p_(1200-1900)_rpm=3225`: **1**

## Revisão manual sugerida

Arquivos com pelo menos um alerta **ou** status AMARELO/VERMELHO:

- `drive-download-20260403T124026Z-3-001_224929\1,8cv 4e8p nema42 2 50,60hz 30x68 605012085.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1.5cv 2,4p iec63r 2 260,150hz 70x56.4 605012237.pdf`
- `drive-download-20260403T124026Z-3-001_224929\506001026.pdf`
- `drive-download-20260403T124026Z-3-001_224929\506001031.pdf`

## Saídas

- CSV: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_53_flash.csv`
- JSON: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_53_flash.json`