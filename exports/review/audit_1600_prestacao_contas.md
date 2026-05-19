# Prestação de Contas — Acervo Físico vs Manifesto OFICIAL

Gerado em: `2026-05-19T22:43:27Z`
Raiz varrida: `C:\Users\micke\Desktop\O rebobinador\_extraidos_motor`

## Tabela de Prestação de Contas

| Métrica | Quantidade | Notas |
| :--- | ---: | :--- |
| **Total de Arquivos Físicos no HD (acervo `_extraidos_motor`)** | **3,237** | PDF/JPG/JPEG em toda a árvore |
| SHAs únicos no disco | **1,077** | Motores distintos por hash |
| Arquivos Duplicados/Clones (mesmo SHA, 2ª+ cópia) | **2,101** | Aglutinados — não geram motor repetido |
| Caminhos canônicos OFICIAIS (1 por motor no manifesto) | **1,049** | Alinhado ao path do manifesto |
| **Motores OFICIAIS (SHA únicos no manifesto)** | **1,049** | `master_release_v2_manifest.csv` |
| Rejeitados/Lixo (**VERMELHO**, SHA não oficial) | **1** | Reguladores, esquemas vazios, dado ruim |
| Quarentena (**AMARELO**, SHA não oficial) | **10** | Ventiladores pendentes, dados incompletos |
| **Não Processados (cauda restante, SHA)** | **17** | Nunca passaram no pipeline 7C |

### Verificação matemática (SHAs únicos no acervo)

- OFICIAL + Rejeitados + Quarentena + Cauda = 1049 + 1 + 10 + 17 = **1077** (total único no disco: **1077**)

### Verificação matemática (caminhos físicos)

- Canônicos OFICIAIS + Clones duplicados + Caminhos não-oficiais = 1049 + 2101 + 87 = **3237**

## Meta ~1.600 (referência de negócio)

- Meta declarada no master build: **1600** cálculos úteis.
- Diferença meta − arquivos físicos: **-1637**
- Diferença meta − SHAs únicos: **+523**

> O acervo físico tem **mais caminhos** que 1.600 porque inclui pastas Drive (`drive-download-*`), réplicas do mesmo PDF e fotos auxiliares. A base **OFICIAL** conta **motores únicos por SHA**, não cópias de pasta.

## Detalhe por bucket (SHA)

- `nao_processado`: 17
- `oficial_sha`: 1049
- `quarentena_amarelo`: 10
- `rejeitado_vermelho`: 1

## Detalhe por bucket (caminhos)

- `duplicate_clone_path`: 2101
- `nao_processado_path`: 51
- `oficial_canonical_path`: 1049
- `quarentena_amarelo_path`: 33
- `rejeitado_vermelho_path`: 3
