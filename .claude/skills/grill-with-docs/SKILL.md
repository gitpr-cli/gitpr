---
name: grill-with-docs
description: A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go.
disable-model-invocation: true
---

Call the Skill tool twice, for "grilling" and "domain-modeling".

## Salvamento automático do Plano

Quando a fronteira for esgotada e o entendimento compartilhado confirmado salve automaticamente o plano de execução da sessão em:
`docs/plans/{branch}/{YYYYMMDD}_{task_name}_plansfacts.md`

- `{branch}`: nome da branch atual 
- `{YYYYMMDD}`: data local sem separadores (ex.: 20260907).
- `{task_name}`: identificador curto da task em lowercase/underscores.
- Crie `docs/plans/` na raiz do repo onde a skill foi acionada, se não existir.


## Salvamento automático do survey

Ao final da sessão de grill (fronteira esgotada e entendimento compartilhado confirmado), salve automaticamente o levantamento completo — contexto da tarefa, decisões das rodadas e relatório de fatos levantados — em:

`docs/survey/{YYYYMMDD}_{task_name}_surveyfacts.md`

- `{YYYYMMDD}`: data local sem separadores (ex.: 20260907).
- `{task_name}`: identificador curto da task em lowercase/underscores.
- Crie `docs/survey/` na raiz do repo onde a skill foi acionada, se não existir.
- Sobrescreva se já houver arquivo do mesmo dia/task (task rodou novamente).
