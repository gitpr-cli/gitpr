# ADR-002 — Primeiro subcomando do CLI (`gitpr release` via `click.group`)

- **Status:** Aceito
- **Data:** 2026-09-07
- **Contexto:** spec [20260904_skill_gitpr_release_notes_spec.md](20260904_skill_gitpr_release_notes_spec.md) §1/§7, grill rodada 2 (Q7)
- **Glossário:** [glossary-release-notes.md](glossary-release-notes.md)

## Contexto

Todo o CLI do GitPR é **um único `click.command`** com ~29 options e dispatch
por `if flag:` sequenciais dentro do callback ([main.py:266](../src/main.py#L266)) —
não existe suporte a subcomando. A spec propõe `gitpr release` com subflags
(`--draft`, `--since`, `--version`, `--publish`, `--format`), o que a superfície
flat atual não comporta de forma legível: o target version colidiria com o
`--version` de exibição do próprio Click, e cada subflag adicionaria ruído a um
dispatch já saturado.

## Decisão

Converter a raiz em **`click.group` com `invoke_without_command=True`**:

1. `cli` vira grupo; **sem subcomando invocado, o callback do grupo roteia para
   o dispatch legado atual** (todos os ~29 flags existentes comportam-se byte a
   byte como hoje) — a migração é aditiva, não uma reescrita.
2. `gitpr release` vira subcomando isolado, com namespace próprio de options
   (`--draft`, `--since <tag>`, `--version <x.y.z>`, `--publish`, `--format
   {markdown|json}`, `--force`) — sem colisão com o `--version` da raiz.
3. O `--version` de exibição da raiz é preservado no grupo.
4. Semântica das flags (rodada 1, Q4): default = gera + salva `CHANGELOG.md` +
   prévia em terminal, **não publica**; `--publish` publica após `click.confirm`;
   `--draft` = "criar como rascunho na forge" (GitHub), apenas com `--publish`.

### Alternativas consideradas

| Alternativa | Veredito |
|---|---|
| Flags flat na raiz (`gitpr --release --since …`) | Rejeitada — colisão do target version com o `--version` de exibição; mais flags sobre um dispatch de 29; leitura pobre do comando. |
| Reescrever todos os fluxos como subcomandos | Rejeitada — risco alto em 29 flags sem ganho imediato; a superfície legada permanece válida. |
| Grupo híbrido com fallback legado | **Escolhida** — caminho de menor risco que entrega `gitpr release` e abre espaço para futuros subcomandos (ex.: tier Team). |

## Desvios aprovados (vs. a spec §7)

1. A spec §7 descrevia `cmd_release(args)` no fluxo flat; a feature registra um
   **subcomando** `release` (decisão acima).
2. A spec §1 listava `--draft` como "gera e mostra sem publicar"; o termo foi
   redesenhado na rodada 1 (Q4): `--draft` = rascunho da forge; o modo local é o
   **default** do comando.
3. Novo flag `--force` (fora da spec §1) para a política de idempotência
   (rodada 1, Q2): seção de versão já existente aborta, `--force` regera.

## Consequências

**Positivas:**
- UX `gitpr release …` no padrão mental `git`/`gh`, com namespace de flags limpo.
- Base para subcomandos futuros sem nova migração estrutural.
- Risco contido: comportamento legado preservado quando nenhum subcomando é
  invocado.

**Negativas / custos:**
- O CLI passa a ter **dois paradigmas** (flags na raiz + subcomandos) — o help
  da raiz e a documentação precisam deixar isso explícito.
- Testes de superfície do entry point (`gitpr = src.main:cli`, CliRunner) devem
  cobrir o caminho default (sem subcomando) e o novo subcomando.
- Callback do grupo precisa do dispatch atual intacto como ramo default — a
  conversão deve ser feita em commit isolado e revisável (spec §9).
