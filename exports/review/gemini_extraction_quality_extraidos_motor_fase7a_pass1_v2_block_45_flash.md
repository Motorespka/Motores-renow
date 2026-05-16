# Auditoria extração Gemini (determinística)

- Gerado: `2026-05-16T20:40:37Z`
- Entrada: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_45_flash_candidates.csv`
- Últimas linhas: **14**
- Total auditado: **14**

## Resumo

| Métrica | Valor |
|---|---:|
| Verdes sem alerta | 0 |
| Verdes com alerta | 9 |
| Amarelos | 4 |
| Vermelhos | 1 |

## Top motivos de alerta (todos os códigos)

- `A10_tipo_vazio_ou_desconhecido`: **6**
- `A07_potencia_decimal_sem_evidencia_frac_potencia_cv=12,5`: **4**
- `A03_trifasico_com_auxiliar_preenchido`: **4**
- `S_pipeline_AMARELO_REVISAR`: **4**
- `A09_tensao_vazia`: **3**
- `A03b_trifasico_principal_vazio_aux_preenchido`: **2**
- `A08_rpm_fora_faixa_polos_4p_(1200-1900)_rpm=3583`: **1**
- `S_pipeline_VERMELHO_REVISAR`: **1**

## Top alertas críticos (prefixo `A`, heurísticas de campo)

- `A10_tipo_vazio_ou_desconhecido`: **6**
- `A07_potencia_decimal_sem_evidencia_frac_potencia_cv=12,5`: **4**
- `A03_trifasico_com_auxiliar_preenchido`: **4**
- `A09_tensao_vazia`: **3**
- `A03b_trifasico_principal_vazio_aux_preenchido`: **2**
- `A08_rpm_fora_faixa_polos_4p_(1200-1900)_rpm=3583`: **1**

## Revisão manual sugerida

Arquivos com pelo menos um alerta **ou** status AMARELO/VERMELHO:

- `drive-download-20260403T124026Z-3-001_224929\605028115.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605028315.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605028715.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605029715.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605041001.pdf`
- `drive-download-20260408T000443Z-3-001_253069\BOBI.PDF`
- `drive-download-20260408T000443Z-3-001_253069\EST.PDF`
- `drive-download-20260408T000443Z-3-001_253069\Esquema Eletrico Geradores Branco.pdf`
- `drive-download-20260408T000443Z-3-001_253069\GERADOR 15 KVA (1).pdf`
- `drive-download-20260408T000443Z-3-001_253069\REGULADOR CR.pdf`
- `drive-download-20260408T000443Z-3-001_253069\REGULADOR EB.pdf`
- `drive-download-20260408T000443Z-3-001_253069\REGULADOR ESCOVA.pdf`
- `drive-download-20260408T000443Z-3-001_253069\ROT.PDF`
- `drive-download-20260408T000443Z-3-001_253069\TC.PDF`

## Saídas

- CSV: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_45_flash.csv`
- JSON: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_45_flash.json`