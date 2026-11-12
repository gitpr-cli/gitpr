# Implementation Plan — Auditoria e Encerramento da Nota de Migração do `-c` Interativo

## Goal Description
Formalizar o fechamento e a auditoria técnica do item herdado do relatório [`relatorio_estado_v0.0.23.md`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/reports/relatorio_estado_v0.0.23.md):
> *Nota de migração do `-c` interativo: o `commit-message-ia` descreve o fluxo novo; vale dizer explicitamente que sem TTY ele cai no console e que `--hook` continua sendo o caminho de CI. Item herdado, ainda aberto (a guarda de TTY reduziu o impacto).*

A auditoria comprovou que no commit `1995213` (09/11/2026) a documentação técnica foi atualizada nos 5 idiomas com callouts de aviso explícitos e o modelo de domínio no `CONTEXT.md` foi refinado, tendo sido o item marcado como concluído no [`relatorio_estado_v0.0.24.md`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/reports/relatorio_estado_v0.0.24.md).

## User Review Required
> [!NOTE]
> Conforme acordado na rodada de Grill (Q1 = Opção 1, Q2 = Opção 1), nenhuma alteração no código fonte (`src/`) ou na documentação dos 5 idiomas (`docs/commit-message-ia.*.md`) é necessária. O objetivo é a certificação da conformidade dos testes de roteamento com/sem TTY e o encerramento documental do item.

## Proposed Changes
Não há alterações de código funcional ou de documentação técnica existentes a aplicar.

### Auditoria e Verificação de Conformidade
- Verificar a paridade dos 5 arquivos de documentação técnica:
  - [`docs/commit-message-ia.md`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/commit-message-ia.md)
  - [`docs/commit-message-ia.pt_br.md`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/commit-message-ia.pt_br.md)
  - [`docs/commit-message-ia.pt_pt.md`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/commit-message-ia.pt_pt.md)
  - [`docs/commit-message-ia.es_es.md`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/commit-message-ia.es_es.md)
  - [`docs/commit-message-ia.fr_fr.md`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/commit-message-ia.fr_fr.md)
- Verificar a definição de `Commit flow` em [`CONTEXT.md`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/CONTEXT.md).

## Verification Plan

### Automated Tests
Executar os testes de roteamento e comportamento de `CommitApp` com e sem TTY:
```bash
python -m pytest tests/test_commit_app.py -v
```

### Manual Verification
- Validar se o callout `> [!WARNING]` está formatado corretamente e legível nas documentações técnicas.
- Validar se os artefatos de governança (`docs/survey/`, `docs/plans/`, `docs/gemini/`) refletem o status concluído do item.
