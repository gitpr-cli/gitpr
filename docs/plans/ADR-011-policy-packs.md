# ADR-011 — Policy Packs: manifesto declarativo sobre skills fixas

- **Status:** Aceito
- **Data:** 2026-10-09
- **Contexto:** spec [20261009_skill_gitpr_policy_packs_spec.md](20261009_skill_gitpr_policy_packs_spec.md), grill de 5 rodadas
- **Glossário:** [glossary-policy-packs.md](glossary-policy-packs.md)

## Contexto

O GitPR configura qualidade em quatro lugares que não se conhecem: as skills fixas em
`.gitpr/skill/.gitpr.<tipo>.md`, as regras de linter em `.gitpr/skill/.gitpr.linter.yml`, o
risco em `.gitpr/skill/gitpr.risk.yml`, e as variáveis em `~/.gitpr/.env`. Nada amarra o
conjunto, nada é versionável como uma unidade, e uma equipe que quer o mesmo gate em oito
repositórios copia oito vezes.

A spec quer um **Policy Pack**: um manifesto YAML versionável, aplicado por repositório, que
padroniza o gate sem virar um segundo sistema de skills dinâmicas.

Quatro fatos do código moldaram a decisão:

1. As skills são **fixas e registradas em código** (`SKILL_FILES_BY_TYPE`, 11 entradas), e a
   ADR anterior já estabeleceu que um arquivo não listado "não é uma skill".
2. O sistema de plugins é `os.listdir` — **não tem manifesto, versão, checksum, OTA nem
   registry**. Não há lifecycle a reutilizar.
3. O `skill_context` viaja em `instrucao_sistema`, **separado** do `prompt`. Como a chave de
   cache é o MD5 do prompt, mexer no skill context **não invalida cache**.
4. O linter tem **dois** níveis e nada entre eles — a ADR-007 registra a rejeição explícita de
   um terceiro.

## Decisão

1. **Packs não são skills.** Um pack pode ativar, parametrizar, complementar o contexto ou
   selecionar o formato de uma skill **já registrada**. Um pack não declara skill nova, não
   executa código, não chama shell e não baixa nada. Referência a skill fora de
   `config.SKILL_TYPES` é erro de validação **antes** da ativação, nunca um warning.

2. **Camadas novas sob a Clean Architecture vigente** (ADR-009/ADR-010):
   `src/domain/policy/` (tipos, manifesto, compatibilidade, resolver, checksum),
   `src/application/use_cases/` (validate, install, activate, resolve),
   `src/infrastructure/policy/` (loader e repositório local). O `policy_resolver` é o
   **único** lugar que faz parsing e composição de manifesto; nem `core.py`, nem o linter,
   nem os providers de IA leem `policy.yml`.

3. **`src/policy_packs/` e não `policy-packs/` na raiz.** O `pyproject.toml` empacota apenas
   `["src", "src.*"]` e não declara `package_data` — o wheel 1.3.0 contém somente `.py`. Um
   diretório na raiz simplesmente não chegaria ao usuário. Decorre daí o bloco
   `[tool.setuptools.package-data]` novo.

4. **`~/.gitpr/policies/` e não `~/.gitpr/plugins/`.** O plugin system não tem manifesto,
   versão nem checksum; herdá-lo significaria construir a distribuição dentro de uma
   estrutura que não a comporta, ou conviver com dois regimes de integridade. O pack da
   equipe, ainda não instalado, vive em `.gitpr/policies/<nome>/` dentro do repositório.

5. **Um único pack principal.** `gitpr policy use` **substitui** o pack ativo, e o lockfile
   registra a raiz mais o grafo `extends` resolvido. Composição multi-pack fica fora desta
   versão: a spec previa vários ativos, mas "vários packs somando" exige uma ordem estável
   entre pares sem relação de dependência — isto é, um segundo sistema de prioridades — e o
   caso de uso real (uma equipe, uma política) é a raiz com dependências.

6. **Precedência `defaults → deps → root → overrides → CLI → env`.** A ordem 5→6 e 6→7 da
   spec está invertida em relação ao projeto: `--provider` vence `DEFAULT_AI_PROVIDER` e
   `--base` vence `PR_DEFAULT_BASE` no código real. A hierarquia da spec seria uma segunda
   hierarquia isolada, exatamente o que a §6.1 proíbe.

7. **O resolver só é autoritativo com pack ativo.** Sem lockfile, a `EffectivePolicy` é vazia
   e `load_risk_config()`, `load_linter_rules()` e `get_skill_context()` seguem o caminho de
   hoje, intocados. A não-regressão da §12.10 vira consequência da arquitetura, não um teste
   que precisa ser lembrado.

8. **A identidade da política entra no `cache_scope`** — `::policy::<nome>@<versão>::<checksum>`,
   o mesmo mecanismo que o `DiffSource` já usa para a origem remota. Sem isso, ativar um pack
   sobre um diff já cacheado devolveria a resposta antiga enquanto a saída exibisse o rótulo
   `Policy: nome@versão` da §7.3 — a feature pareceria funcionar e não funcionaria.

9. **Validação estrita.** Chave desconhecida é erro; override para regra inexistente é erro;
   `name` com path traversal é erro; asset fora do diretório do pack é erro; segredo no
   manifesto é erro (reusando as regex de `src/security_ruleset.py`). O precedente do plugin
   linter — YAML de terceiro que entra sem validação nenhuma — é o que esta feature
   conscientemente inverte.

10. **Severidade com dois níveis e justificativa assimétrica.** `SeverityOverride` nomeia a
    regra por `rule_name` e muda o `level` entre `error` e `warning` — os dois que o motor
    tem. `reason` é **obrigatório ao rebaixar** (`error`→`warning`) e opcional ao endurecer:
    o custo de escrever uma linha é menor que o de descobrir depois por que o gate parou de
    bloquear.

11. **SemVer de verdade.** `packaging.specifiers.SpecifierSet` e `packaging.version.Version`,
    declarados em `pyproject.toml` e `Pipfile`. O `parse_version()` caseiro de `updater.py`
    devolve `(0,0,0)` para qualquer range — não serve.

12. **Falha de resolução aborta.** Pack removido de `~/.gitpr/policies/`, versão fixada que
    sumiu depois de um upgrade, checksum divergente: os três interrompem a execução com o
    nome do pack, o que aconteceu e o comando de reativação. Um pack ativo é uma promessa de
    gate; cumpri-la pela metade é pior que não cumpri-la.

## Consequências

**Positivas**

- Uma equipe versiona o gate junto do código (`.gitpr/policy.lock.yml` e
  `.gitpr/policies/`), e outra máquina reproduz a mesma política sem download.
- A proveniência é verificável: `gitpr policy show` responde de qual pack veio cada valor.
- `src/policy_packs/` sobrevive a `pip install --upgrade`, porque agora viaja no wheel.
- A superfície de ataque não cresce: nada de terceiro executa código no processo do GitPR.
- Risco de supply chain endereçado por checksum, não por assinatura (fora de escopo).

**Limitações e custos assumidos**

- Um pack por repositório. Quem quiser "somente as regras de segurança do pack X" precisa de
  um pack que `extends` X, não de dois ativos.
- `.gitpr/policies/<nome>/` versionado significa que editar o pack localmente **quebra o
  checksum** e exige reativação. É o preço de detectar alteração inesperada.
- O checksum cobre `policy.yml` e os assets declarados, não o conteúdo dos arquivos de skill
  em `.gitpr/skill/` — que continuam sendo configuração do projeto, não do pack.
- `RiskConfig.enabled` e `RiskConfig.include_in_review` seguem sendo código morto. Ficaram
  fora do schema do pack; a flag não foi consertada aqui.
