# Plano: Sincronizar chaves i18n de core.py com pt_br.json

## Contexto

O `src/core.py` contém 84 chamadas à função `__()` para internacionalização. O arquivo `langs/pt_br.json` é um dicionário flat (chave = string em inglês, valor = tradução pt-BR) com 486 entradas. Após cruzar as 84 chaves de core.py contra as 486 do pt_br.json, **3 chaves estão faltando** e precisam ser adicionadas com tradução para português do Brasil.

## Chaves faltantes (core.py → adicionar ao pt_br.json)

As 3 chaves são relacionadas à feature Smart Excludes (adicionada em 2026-07-18):

| #   | Chave (inglês)                                                         | Tradução (pt-BR)                                                             |
| --- | ---------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| 1   | `Changed documentation (content excluded from diff):\n`                | `Documentação alterada (conteúdo excluído do diff):\n`                       |
| 2   | `📄 {count} documentation file(s) excluded from diff (Smart Excludes).` | `📄 {count} arquivo(s) de documentação excluído(s) do diff (Smart Excludes).` |
| 3   | `Learn more:`                                                          | `Saiba mais:`                                                                |

## O que será feito

1. Adicionar as 3 entradas ao final de `langs/pt_br.json`, mantendo a estrutura flat existente
2. **Nunca remover** entradas existentes
3. Preservar placeholders `{count}` idênticos na tradução

## Arquivo modificado

- `langs/pt_br.json` — adicionar 3 novas chaves ao final do objeto JSON

## Verificação

```bash
# Confirmar que as 3 chaves agora existem
grep -c "Changed documentation" langs/pt_br.json
grep -c "Smart Excludes" langs/pt_br.json
grep -c "Learn more" langs/pt_br.json

# Validar JSON
python -c "import json; json.load(open('langs/pt_br.json'))"
```
