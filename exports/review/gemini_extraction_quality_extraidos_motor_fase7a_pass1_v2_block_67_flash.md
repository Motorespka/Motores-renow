# Auditoria extração Gemini (determinística)

- Gerado: `2026-05-19T22:14:44Z`
- Entrada: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_67_flash_candidates.csv`
- Últimas linhas: **14**
- Total auditado: **14**

## Resumo

| Métrica | Valor |
|---|---:|
| Verdes sem alerta | 1 |
| Verdes com alerta | 2 |
| Amarelos | 10 |
| Vermelhos | 1 |

## Top motivos de alerta (todos os códigos)

- `S_pipeline_AMARELO_REVISAR`: **10**
- `A10_tipo_vazio_ou_desconhecido`: **7**
- `A09_tensao_vazia`: **5**
- `A01_mono_sem_fio_espiras_passo_principal`: **2**
- `A02_mono_sem_fio_espiras_passo_auxiliar`: **2**
- `A10_WARNING_tipo_inferido_com_evidencia=monofasico;auxiliar_e/ou_capacitor_preenchidos`: **2**
- `A06_WARNING_espiras_normalizada_rastreavel`: **1**
- `S_pipeline_VERMELHO_REVISAR`: **1**
- `A07_potencia_decimal_sem_evidencia_frac_potencia_cv=12.5`: **1**
- `A10_WARNING_tipo_inferido_com_evidencia=trifasico;tensao_tripla_sem_auxiliar`: **1**

## Top alertas críticos (prefixo `A`, heurísticas de campo)

- `A10_tipo_vazio_ou_desconhecido`: **7**
- `A09_tensao_vazia`: **5**
- `A01_mono_sem_fio_espiras_passo_principal`: **2**
- `A02_mono_sem_fio_espiras_passo_auxiliar`: **2**
- `A07_potencia_decimal_sem_evidencia_frac_potencia_cv=12.5`: **1**

## Revisão manual sugerida

Arquivos com pelo menos um alerta **ou** status AMARELO/VERMELHO:

- `drive-download-20260408T000443Z-3-001_253069\REGULADOR CR.pdf`
- `drive-download-20260408T000511Z-3-001_428675\esquema vent. de ar.pdf`
- `drive-download-20260408T000529Z-3-001_185960\1d217467-02db-4a7f-8017-ea2f9ac0a715.jpg`
- `drive-download-20260408T000529Z-3-001_185960\1d9b3430-0b16-4701-b724-661974ff8b49.jpg`
- `drive-download-20260408T000529Z-3-001_185960\324e6cbc-2bab-43ed-9303-2d560b1da7ec.jpg`
- `drive-download-20260408T000529Z-3-001_185960\8bc49b76-90d1-4f38-bd2f-86cd93ad3689.jpg`
- `drive-download-20260408T000529Z-3-001_185960\VENTILADOR 3 VELOCIDADES.pdf`
- `drive-download-20260408T000529Z-3-001_185960\bda2a6e0-62ba-4738-8a58-964852f4ad8d.jpg`
- `drive-download-20260408T000529Z-3-001_185960\dc81f9cf-0541-4d2d-87c5-686e9c194c01.jpg`
- `drive-download-20260408T000529Z-3-001_185960\f837d1fb-1d86-4e42-aa6a-9eaa9c696086.jpg`
- `drive-download-20260408T000605Z-3-001_290649\arno 4.jpg`
- `drive-download-20260408T000605Z-3-001_290649\arno.jpg`
- `drive-download-20260408T000620Z-3-001_132268\25.jpg`
- `drive-download-20260408T000620Z-3-001_132268\BRASIL 2.jpg`

## Saídas

- CSV: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_67_flash.csv`
- JSON: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_67_flash.json`