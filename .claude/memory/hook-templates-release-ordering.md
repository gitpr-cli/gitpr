---
name: hook-templates-release-ordering
description: Templates de hook devem chegar ao GitHub main antes do bump de __scripts_version__ no updater
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-08-12_fix_prepare_commit_msg_merge_skip.md
  date: 2026-08-12
  branch: develop_natan
---

Os templates de hook em `scripts/` são baixados do GitHub `main` pelo auto-sync
de hooks — `__scripts_version__` em `src/updater.py` controla quando os hooks
instalados nos repositórios são atualizados na próxima execução de `gitpr`.
Existe uma restrição de ordenação no processo de release: **os templates
corrigidos devem ser mergeados em `main` ANTES de bumpar `__scripts_version__`**
e lançar a CLI — senão o auto-sync baixa e instala os templates antigos,
reintroduzindo bugs recém-corrigidos silenciosamente.

Caso concreto: o fix de skip de merge-source nos hooks `prepare-commit-msg`
(v0.0.1 → v0.0.2) alterou os 5 templates `prepare-commit-msg-template.*.sh`;
o bump só podia entrar no release depois que os templates atualizados
estivessem disponíveis no GitHub `main`.

**Why:** O auto-sync sobrescreve os scripts de hook locais sem aviso. Se a CLI
nova referencia templates que ainda não chegaram ao `main`, o usuário recebe a
versão antiga dos hooks — exatamente o bug que o release pretendia corrigir.

**How to apply:** Em qualquer release que altere arquivos em `scripts/`,
mergear os templates em `main` primeiro e só então versionar/bumpar
`__scripts_version__` no `updater.py`. O mesmo vale para todo recurso remoto
controlado por marcador de versão — ver [[version-marker-pattern]].
