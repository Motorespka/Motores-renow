## Resumo batch rebobinagem (2026-05-19 00:06:58)

- **input**: `C:\Users\micke\Desktop\O rebobinador\_extraidos_motor`
- **work_queue_csv**: `exports/review/pass1_v2_block_62.csv`
- **output_tag**: `extraidos_motor_fase7a_pass1_v2_block_62_flash`
- **dry-run**: `False` (sem chamadas Gemini à API)
- **processados**: `14`
- **cache respostas**: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\logs\extraidos_motor_fase7a_pass1_v2_block_62_flash_gemini_cache_fresh`

### Fontes

- tentativas pipeline local (PDF texto / Tesseract / EasyOCR): 18
- com texto local não vazio: 2
- chamadas API Gemini: 9
- imagens com fallback Gemini (contagem interna): 9
- respostas servidas do cache (sem API): 5

### Economia de chaves / cache

- pastas cache consultadas: 1
- **cache_hits**: 5
- **cache_misses** (resolveu por API): 9
- **gemini_calls_real**: 9
- **gemini_calls_avoided_by_cache**: 5
- **quota_429**: 0
- **quota_429_consecutive_max**: 0
- skipped_existing_green: 0
- skipped_existing_success: 0

### Status

- VERDE_AUTO_LOCAL: 0
- VERDE_AUTO_GEMINI: 2
- AMARELO_REVISAR: 8
- VERMELHO_REVISAR: 1
- PAUSA_INFRA_SEM_CHAVE: 3
- PAUSA_LIMITE_CHAMADAS: 0
- PAUSA_LOTE_INTERROMPIDO: 0

- PAUSA_TODAS_CHAVES_COOLDOWN: 0
- PAUSA_LIMITE_POR_CHAVE: 0
- PAUSA_SEM_CHAVE_OK: 0

### Chaves Gemini usadas (alias)

- UQ_1: 1
- UQ_12: 1
- UQ_13: 1
- UQ_2: 1
- UQ_5: 1
- UQ_7: 1
- cache: 5

### Uso por chave (detalhado)

- rotation_strategy: `round_robin`
- max_calls_per_key_per_run: `2`

- UQ_1 | status=ok | eligible_end=1 | calls=1 | ok=1 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_10 | status=quota_exhausted | eligible_end=0 | calls=1 | ok=0 | quota=1 | errors=1 | cooldown=2026-05-19T03:24:44Z | blocked=require_ok;cooldown
- UQ_11 | status=quota_exhausted | eligible_end=0 | calls=1 | ok=0 | quota=1 | errors=1 | cooldown=2026-05-19T03:25:14Z | blocked=require_ok;cooldown
- UQ_12 | status=ok | eligible_end=1 | calls=1 | ok=1 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_13 | status=ok | eligible_end=1 | calls=1 | ok=1 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_14 | status=quota_exhausted | eligible_end=0 | calls=1 | ok=0 | quota=1 | errors=1 | cooldown=2026-05-19T03:26:48Z | blocked=require_ok;cooldown
- UQ_2 | status=ok | eligible_end=1 | calls=1 | ok=1 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_3 | status=quota_exhausted | eligible_end=0 | calls=1 | ok=0 | quota=1 | errors=2 | cooldown=2026-05-19T03:28:48Z | blocked=require_ok;cooldown
- UQ_4 | status=quota_exhausted | eligible_end=0 | calls=1 | ok=0 | quota=1 | errors=2 | cooldown=2026-05-19T03:30:43Z | blocked=require_ok;cooldown
- UQ_5 | status=ok | eligible_end=1 | calls=1 | ok=1 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_6 | status=quota_exhausted | eligible_end=0 | calls=1 | ok=0 | quota=1 | errors=1 | cooldown=2026-05-19T03:31:54Z | blocked=require_ok;cooldown
- UQ_7 | status=ok | eligible_end=1 | calls=1 | ok=1 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_8 | status=quota_exhausted | eligible_end=0 | calls=1 | ok=0 | quota=1 | errors=1 | cooldown=2026-05-19T03:32:39Z | blocked=require_ok;cooldown
- UQ_9 | status=quota_exhausted | eligible_end=0 | calls=1 | ok=0 | quota=1 | errors=1 | cooldown=2026-05-19T03:36:55Z | blocked=require_ok;cooldown

### Top 10 motivos de bloqueio

- baixa_confianca_local: 9
- faltando_obrigatorio: 4
- infra:gemini_indisponivel_ou_quota: 3

### Top 11–20 (extra)


### Exemplos (até 10) problemáticos

- drive-download-20260408T000443Z-3-001_253069\REGULADOR CR.pdf: faltando_obrigatorio;baixa_confianca_local missing=['tensao']
