## Resumo batch rebobinagem (2026-05-19 07:52:45)

- **input**: `C:\Users\micke\Desktop\O rebobinador\_extraidos_motor`
- **work_queue_csv**: `exports/review/pass1_v2_block_65_only_41.csv`
- **output_tag**: `extraidos_motor_fase7a_pass1_v2_block_65_flash`
- **dry-run**: `False` (sem chamadas Gemini à API)
- **processados**: `1`
- **cache respostas**: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\logs\extraidos_motor_fase7a_pass1_v2_block_65_41_gemini_cache`

### Fontes

- tentativas pipeline local (PDF texto / Tesseract / EasyOCR): 1
- com texto local não vazio: 0
- chamadas API Gemini: 1
- imagens com fallback Gemini (contagem interna): 1
- respostas servidas do cache (sem API): 0

### Economia de chaves / cache

- pastas cache consultadas: 1
- **cache_hits**: 0
- **cache_misses** (resolveu por API): 1
- **gemini_calls_real**: 1
- **gemini_calls_avoided_by_cache**: 0
- **quota_429**: 0
- **quota_429_consecutive_max**: 0
- skipped_existing_green: 0
- skipped_existing_success: 0

### Status

- VERDE_AUTO_LOCAL: 0
- VERDE_AUTO_GEMINI: 1
- AMARELO_REVISAR: 0
- VERMELHO_REVISAR: 0
- PAUSA_INFRA_SEM_CHAVE: 0
- PAUSA_LIMITE_CHAMADAS: 0
- PAUSA_LOTE_INTERROMPIDO: 0

- PAUSA_TODAS_CHAVES_COOLDOWN: 0
- PAUSA_LIMITE_POR_CHAVE: 0
- PAUSA_SEM_CHAVE_OK: 0

### Chaves Gemini usadas (alias)

- UQ_1: 1

### Uso por chave (detalhado)

- rotation_strategy: `round_robin`
- max_calls_per_key_per_run: `2`

- UQ_1 | status=ok | eligible_end=1 | calls=1 | ok=1 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_10 | status=ok | eligible_end=1 | calls=0 | ok=0 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_11 | status=ok | eligible_end=1 | calls=0 | ok=0 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_12 | status=ok | eligible_end=1 | calls=0 | ok=0 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_13 | status=ok | eligible_end=1 | calls=0 | ok=0 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_14 | status=ok | eligible_end=1 | calls=0 | ok=0 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_2 | status=ok | eligible_end=1 | calls=0 | ok=0 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_3 | status=ok | eligible_end=1 | calls=0 | ok=0 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_4 | status=ok | eligible_end=1 | calls=0 | ok=0 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_5 | status=ok | eligible_end=1 | calls=0 | ok=0 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_6 | status=ok | eligible_end=1 | calls=0 | ok=0 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_7 | status=ok | eligible_end=1 | calls=0 | ok=0 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_8 | status=ok | eligible_end=1 | calls=0 | ok=0 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_9 | status=ok | eligible_end=1 | calls=0 | ok=0 | quota=0 | errors=0 | cooldown= | blocked=

### Top 10 motivos de bloqueio

- baixa_confianca_local: 1

### Top 11–20 (extra)


### Exemplos (até 10) problemáticos

