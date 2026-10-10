# Glossário — Policy Packs

> Vocabulário canônico da feature Policy Packs (manifesto declarativo de política de
> engenharia, aplicável por repositório).
> Mantido junto da [spec](20261009_skill_gitpr_policy_packs_spec.md) e do
> [plano de implementação](develop_natan/20261009_policy_packs_plansfacts.md); a decisão
> arquitetural vive no [ADR-011](ADR-011-policy-packs.md).

## Termos de domínio

| Termo | Definição |
|---|---|
| **policy pack** | Manifesto declarativo e versionado (`policy.yml` + assets) que ativa, parametriza, complementa o contexto ou seleciona o formato de skills **já fixas** do GitPR, além de configurar linter, severidade, risco e convenções de PR/commit. Não é uma skill: não introduz nomes novos, não executa código e não faz download. |
| **manifest** | O `policy.yml` de um pack. Chaves obrigatórias: `schema_version`, `name`, `version`, `min_gitpr_version`. Schema **fechado** — chave desconhecida é erro de validação, nunca ignorada em silêncio. |
| **pack reference** | `PackReference` — nome (`namespace/nome`), versão (SemVer exato ou range) e a origem de onde o pack foi lido. |
| **policy source** | Enumeração `PolicySource` com as três origens possíveis: `BUNDLED` (`src/policy_packs/`, dentro do pacote instalado), `LOCAL_PATH` (`.gitpr/policies/<nome>/`, versionado no repositório da equipe) e `INSTALLED` (`~/.gitpr/policies/<nome>/`, instalado pelo usuário). |
| **dependency** | Pack referenciado no bloco `extends` de outro pack. Resolvido por grafo, em ordem topológica, **sem download remoto**. |
| **root pack** | O único pack principal ativo num repositório. `gitpr policy use` o substitui; dependências vêm por `extends`. |
| **skill policy** | `SkillPolicy` — a ativação de uma skill fixa e o `additional_context` que ela recebe. O `skill_name` tem de estar em `config.SKILL_TYPES` (11 entradas); qualquer outro nome é erro de validação. |
| **additional context** | Texto declarativo anexado ao `instrucao_sistema` de uma skill. **Não** entra no `prompt` — o que significa que sozinho ele não muda a chave de cache (ver *cache scope*). |
| **severity override** | `SeverityOverride` — a mudança do `level` de uma regra de linter, nomeando a regra por `rule_name` (a chave real é `name`). Os níveis válidos são `error` e `warning`, **os dois únicos que o motor tem**; não existe terceiro nível (ADR-007). |
| **downgrade** | Um severity override que **rebaixa**: `error` → `warning`. Exige `reason`, porque enfraquece o gate. Um override que mantém ou endurece (`warning` → `error`) tem `reason` opcional. |
| **rules file** | `linter.rules_file` — o YAML de regras que o pack traz, relativo ao diretório do pack e sem poder escapar dele. **Não** se chama "preset": no GitPR, *preset* já significa o binário externo configurado pelo wizard (PHPCS, ESLint, Stylelint). |
| **effective policy** | `EffectivePolicy` — o resultado da resolução: skills, linter, overrides de severidade, risco, PR, commit, caminhos protegidos, `provenance` e `warnings` já compostos, prontos para injeção. |
| **provenance** | O mapa `chave de configuração → pack ou override que a definiu`. É o que permite a `gitpr policy show` responder "de onde veio este valor". |
| **lockfile** | `.gitpr/policy.lock.yml` — registro do que está ativo **neste repositório**: nome e versão exata de cada pack resolvido, origem, checksums SHA-256, versão do GitPR que validou, data/hora de ativação, o grafo `extends` resolvido e o `schema_version`. É versionado no Git — é o que torna a política reproduzível em outra máquina. |
| **overrides file** | `.gitpr/policy.overrides.yml` — o ajuste local e auditável, por repositório. Aplica-se **depois** do pack principal e **antes** das flags de CLI. |
| **checksum** | SHA-256 do `policy.yml` mais os assets declarados. Divergência entre o checksum do lockfile e o conteúdo em disco **aborta** a execução: o pack mudou sem reativação explícita. |
| **cache scope** | Sufixo acrescentado **apenas à chave** do cache MD5, nunca ao prompt. A política contribui com `::policy::<nome>@<versão>::<checksum>`, o que faz uma troca de pack invalidar as respostas cacheadas — sem isso o review sairia idêntico e o rótulo estaria mentindo. |
| **stack detector** | Detector leve que reconhece a stack de um repositório pela presença de arquivos característicos (`composer.json` + `artisan` → Laravel; `package.json` + `vue` → Vue; …) para sugerir um pack em `gitpr policy init --stack`. |

## Precedência

Do menor para o maior — cada camada sobrescreve a anterior:

1. defaults internos do GitPR;
2. packs dependentes, em ordem topológica de `extends`;
3. pack principal ativo;
4. `.gitpr/policy.overrides.yml`;
5. configuração local já existente do projeto;
6. flags explícitas de CLI;
7. variáveis de ambiente.

A ordem 6 e 7 é a **do projeto**, não a da spec original: `--provider` vence
`DEFAULT_AI_PROVIDER` e `--base` vence `PR_DEFAULT_BASE` no código real.

Sem pack ativo nada disso se aplica: o resolver devolve uma política vazia e o GitPR se
comporta exatamente como antes — `load_risk_config()`, `load_linter_rules()` e
`get_skill_context()` ficam intocados.

## Regras de composição

- **Listas** (`critical_paths`, `test_patterns`, `protected_paths`, `required_sections`):
  união ordenada, sem duplicidade. Remoção só em override explícito com justificativa.
- **`additional_context`**: concatenado na ordem de precedência, com delimitador de origem,
  sob um teto de caracteres (`GITPR_POLICY_CONTEXT_MAX_CHARACTERS`, padrão 12000).
- **Regras de linter**: união por `name` com precedência — a camada superior redefine a regra
  de mesmo nome, regras únicas sobrevivem, e nunca há alerta duplicado.
- **Escalares entre packs irmãos**: erro de validação nomeando os dois packs e a chave. O
  GitPR nunca escolhe um vencedor em silêncio.
- **Falha de resolução**: pack ausente, versão fixada que sumiu após um upgrade, ou checksum
  divergente → **aborta**, nomeando o pack, o que aconteceu e o comando para reativar.
