# ADR-0022 — Fatiamento Intra-Arquivo e Limites de Tokens por Provider no Map-Reduce

- **Status:** Aceito
- **Data:** 2026-11-11
- **Decisores:** Natan Fiuza, Antigravity
- **Contexto:** Erros de estouro de janela de contexto (limite de 1.048.576 tokens / $2^{20}$ no Gemini) em execuções de Map-Reduce causados por arquivos gigantes indivisíveis e ausência de separação entre o teto de disparo e o teto por lote.
- **Relacionados:** [ADR-0014 (Canonical Package Version SSOT)](0014-canonical-package-version-ssot.md), [ADR-0021 (Strict Boolean Update Check Migration)](0021-strict-boolean-update-check-migration.md), [How GitPR Handles Huge Diffs (`docs/map-reduce-diff.md`)](../map-reduce-diff.md)
- **Glossário:** [CONTEXT.md](../../CONTEXT.md) (`Map-reduce trigger threshold`, `Map-reduce part size`, `Cascade chunking`)

---

## 1. Contexto

Para analisar alterações extensas de código sem estourar os limites de contexto das APIs de inteligência artificial, o GitPR emprega o padrão **Map-Reduce**: divide o diff em lotes parciais, extrai resumos técnicos em paralelo ou sequência (Map) e sintetiza o resultado final em uma chamada consolidada (Reduce).

### O Problema Identificado
1. **Arquivos Individuais Gigantes**: A implementação original do fatiador (`split_diff_into_chunks`) dividia o diff estritamente nas fronteiras de arquivos (`^diff --git a/`). Caso um único arquivo contivesse mais de 1.048.576 tokens (como arquivos de migração SQL massivos, lockfiles, código compilado/gerado ou datasets embutidos), ele era tratado como um bloco indivisível. Esse lote único gigantesco era enviado à API do provedor (ex.: Gemini), estourando o teto estrito de $2^{20}$ (1.048.576) tokens e disparando erro 400.
2. **Confusão entre Disparo e Tamanho de Lote**: O código empregava uma única constante (`max_tokens=90000`) tanto para decidir se entrava em modo Map-Reduce quanto para limitar os lotes.
3. **Rigidez e Falta de Customização por Provider**: Cada provedor de IA (Gemini, DeepSeek, Ollama) opera com janelas de contexto, latências e custos distintos. Não havia suporte para configurar limites independentes por provedor no `.env` ou via `gitpr config`.

---

## 2. Decisão

Formaliza-se a separação de responsabilidades e a cascata de fatiamento no pipeline Map-Reduce:

1. **Separação entre Limite de Disparo e Tamanho por Lote**:
   - **Gatilho do Map-Reduce (`MAX_TOKENS`)**: Limite de tokens totais do diff para acionar o pipeline Map-Reduce. Padrão: **90.000 tokens**.
   - **Tamanho Máximo de Cada Lote (`MAX_PART_TOKENS`)**: Teto estrito de tokens que cada lote individual enviado na etapa de Map pode ter. Padrão: **50.000 tokens**. Garante-se sempre que `max_part_tokens <= max_tokens`.

2. **Configuração Hierárquica por Provider**:
   Suporte a variáveis dedicadas por provedor com fallback global:
   - Gatilho: `GITPR_MAP_REDUCE_MAX_TOKENS_<PROVIDER>` (`_GEMINI`, `_DEEPSEEK`, `_OLLAMA`) ➔ `GITPR_MAP_REDUCE_MAX_TOKENS` ➔ `90000`.
   - Tamanho por Lote: `GITPR_MAP_REDUCE_MAX_PART_TOKENS_<PROVIDER>` (`_GEMINI`, `_DEEPSEEK`, `_OLLAMA`) ➔ `GITPR_MAP_REDUCE_MAX_PART_TOKENS` ➔ `50000`.
   Exposição no catálogo do `gitpr config` sob a categoria `ai`, filtrado condicionalmente via `show_if` pelo provedor ativo.

3. **Fatiamento em Cascata (Arquivo ➔ Hunk ➔ Linhas)**:
   - Se o diff total exceder o gatilho, ele é dividido por arquivos (`diff --git`).
   - Se um arquivo individual exceder `MAX_PART_TOKENS`, ele é fatiado em seus hunks (`@@ -... +... @@`).
   - Se um único hunk ainda exceder `MAX_PART_TOKENS`, ele é fatiado por quebras de linha (`\n`) ou fatias de caracteres.
   - Em cada sublote gerado, o cabeçalho original do arquivo é preservado e complementado pelo marcador contextual `# [<filename> - part X]`, mantendo o entendimento semântico pela IA.

4. **Fallback para Diffs sem Cabeçalho Padrão**:
   Caso o texto não contenha marcadores `diff --git`, o particionador aciona fallback automático baseado em linhas, garantindo que nenhum bloco ultrapasse `MAX_PART_TOKENS`.

5. **Salvaguarda na Etapa de Reduce**:
   Se a junção dos resumos parciais (`diff_unificado`) ultrapassar o limite de disparo, o pipeline executa uma redução intermediária (pré-reduce) em blocos antes da chamada de síntese final.

---

## 3. Consequências

### Positivas
- **Eliminação Total de Estouro de Contexto**: Nenhum lote jamais ultrapassa `MAX_PART_TOKENS` (50k tokens), ficando muito distante do teto de 1.048.576 tokens do Gemini ou de janelas de 64k/128k do DeepSeek.
- **Flexibilidade Operacional**: Usuários e runners de CI podem ajustar o disparo e o tamanho de lote de acordo com suas cotas de modelo e limites de hardware.
- **Preservação de Contexto**: A repetição do cabeçalho de arquivo e o marcador de partes asseguram que a IA compreenda exatamente o escopo do código analisado em cada lote.

### Negativas / Riscos
- Diffs contendo arquivos únicos gigantescos resultarão em um número maior de chamadas parciais de API, aumentando o tempo total de execução proporcionalmente ao volume de fatias.
