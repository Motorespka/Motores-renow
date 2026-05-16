# Auditoria extração Gemini (determinística)

- Gerado: `2026-05-16T21:18:55Z`
- Entrada: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_47_flash_candidates.csv`
- Últimas linhas: **14**
- Total auditado: **14**

## Resumo

| Métrica | Valor |
|---|---:|
| Verdes sem alerta | 9 |
| Verdes com alerta | 4 |
| Amarelos | 1 |
| Vermelhos | 0 |

## Top motivos de alerta (todos os códigos)

- `A08_rpm_absoluto_absurdo_rpm=15190`: **2**
- `A02_mono_sem_fio_espiras_passo_auxiliar`: **1**
- `A08_rpm_fora_faixa_polos_4p_(1200-1900)_rpm=790`: **1**
- `S_pipeline_AMARELO_REVISAR`: **1**
- `A08_rpm_absoluto_absurdo_rpm=14000`: **1**
- `A08_rpm_fora_faixa_polos_4p_(1200-1900)_rpm=4210`: **1**

## Top alertas críticos (prefixo `A`, heurísticas de campo)

- `A08_rpm_absoluto_absurdo_rpm=15190`: **2**
- `A02_mono_sem_fio_espiras_passo_auxiliar`: **1**
- `A08_rpm_fora_faixa_polos_4p_(1200-1900)_rpm=790`: **1**
- `A08_rpm_absoluto_absurdo_rpm=14000`: **1**
- `A08_rpm_fora_faixa_polos_4p_(1200-1900)_rpm=4210`: **1**

## Revisão manual sugerida

Arquivos com pelo menos um alerta **ou** status AMARELO/VERMELHO:

- `drive-download-20260403T124026Z-3-001_224929\1,8cv 4e8p nema42 2 50,60hz 30x68 605012085.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1.5cv 2,4p iec63r 2 260,150hz 70x56.4 605012237.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1.5cv 2p iec63r 2 260hz 30x48.8 605012162.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1.5cv 2p iec63r 2 260hz 30x48.8 605012206.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1.5cv 4p iec63r 2 150hz 50x56.4 605012172.pdf`

## Saídas

- CSV: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_47_flash.csv`
- JSON: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_47_flash.json`