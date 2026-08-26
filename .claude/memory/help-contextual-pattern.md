---
name: help-contextual-pattern
description: Padrão de help contextual com Click usando flag regular em vez de help_option
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-07-01_help_contextual.md
  date: 2026-07-01
  branch: develop_natan
---

O help contextual (`gitpr -h --issue`) exige que `-h`/`--help` seja uma flag Click regular
(`@click.option`) em vez de usar o decorador `@click.help_option`. O `@click.help_option`
intercepta a execução antes da função `cli()`, impedindo a detecção de combinações de flags.

A implementação usa dois dicionários em `src/main.py`:
- `HELP_MAP`: mapeia flag → (título, descrição, URL da documentação)
- `HELP_PRIORITY`: define prioridade quando múltiplas flags são passadas com `-h`

O dispatcher de help é um bloco O(n) que só executa quando `-h` está presente.
Funciona com todas as 12 flags não-hidden do GitPR.

**Why:** Sem isso, `gitpr -h --issue` mostraria apenas o help genérico do Click,
sem informação específica sobre a feature. A troca de `@click.help_option` por
flag regular foi o único jeito de permitir que o handler detectasse qual flag
acompanha o `-h`.

**How to apply:** Ao adicionar novas flags ao GitPR:
1. Adicionar entrada no `HELP_MAP` com título, descrição e URL da doc
2. Se a flag pode ser usada com outras, ajustar `HELP_PRIORITY`
3. A flag `-h` DEVE ser `is_flag=True, is_eager=False` (regular, não eager)
4. Flags com `exists=True` (como `--input`) precisam de guard `not help_flag`
   na validação, já que o Click não bloqueia mais automaticamente

**Gotcha de flags com hífen (corrigido em 2026-08-15):** o dispatcher fazia
`locals().get(param_name)` usando o nome da flag como está no `HELP_MAP`, então
nenhuma flag com hífen (`--linter-setup`, `--no-publish`, `--no-edit`,
`--no-unstaged-check`) era encontrada — o Click converte o nome do parâmetro para
snake_case. A correção é `param_name.replace('-', '_')` antes do lookup. Flags de
palavra única sempre funcionaram, o que escondeu o bug por meses.

Atenção: duas entradas do `HELP_MAP` apontam para docs inexistentes — ver
[[claude-md-desatualizado-vs-architecture]].
