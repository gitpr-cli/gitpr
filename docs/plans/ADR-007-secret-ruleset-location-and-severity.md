# ADR-007 — O security ruleset é embutido no pacote e usa apenas `error`/`warning`

- **Status:** Aceito
- **Data:** 2026-09-21
- **Contexto:** spec [20260921_skill_gitpr_secret_scanning_spec.md](20260921_skill_gitpr_secret_scanning_spec.md) §1, §2, §3 e §5; grill rodadas 1–3
- **Glossário:** [glossary-gitpr-secret-scanning.md](glossary-gitpr-secret-scanning.md)
- **Plano:** [20260921_skill_gitpr_secret_scanning_plan.md](20260921_skill_gitpr_secret_scanning_plan.md)

## Contexto

A spec pede três coisas que este código não oferece: um terceiro nível de severidade (`critical`, entre `blocker` e `warning`), um arquivo de regras em `presets/linter/security.yml`, e reaproveitamento do "mecanismo de override por regra já existente" — que não existe.

O motor de linter tem **dois** níveis e nada entre eles: `warning` é o único valor não bloqueante; qualquer outro — `critical`, `blocker`, um typo, ou a chave ausente — cai em `errors` e bloqueia ([src/linter_engine.py:57-63](../src/linter_engine.py#L57-L63)). E o bloqueio é real e multi-fluxo: `sys.exit(1)` no `-l` ([src/main.py:827](../src/main.py#L827)), `COMMIT BLOCKED!` no hook ([scripts/pre-commit-template.sh:16-32](../scripts/pre-commit-template.sh#L16-L32)), modal `--no-verify` no publish de PR ([src/ui/pr_publish_app.py:517-568](../src/ui/pr_publish_app.py#L517-L568)).

Duas armadilhas concretas motivam este ADR. A primeira: escrever `severity: critical` no arquivo de regras — como a spec faz — produz **exatamente o oposto** do pretendido, porque `severity` é chave ignorada e o default é bloqueante (oito fixtures de `tests/test_plugins.py` já carregam esse erro). A segunda: um ruleset embutido no wheel e ligado por padrão transforma um falso positivo em commit bloqueado **sem escape por linha**, porque nenhum mecanismo de supressão inline existe no repositório.

## Decisão

### 1. Dois níveis, sem extensão do vocabulário

O ruleset usa `error` e `warning` e mais nada. `error` fica reservado às cinco categorias em que o padrão regex é prova suficiente por si só (AWS Access Key ID, token GitHub, token Slack, chave de API do Google, bloco de chave privada). Connection string com credencial e atribuição genérica de credencial são `warning`: são os dois casos em que o mesmo formato aparece legitimamente em fixture, exemplo e documentação.

Estender o vocabulário para um nível intermediário foi rejeitado porque um nível entre `error` e `warning` ou (a) não bloqueia — e então é um `warning` com outro nome, ou (b) bloqueia — e então é um `error` com outro nome. Adicionar a palavra sem adicionar comportamento não paga o custo de mexer no schema de regra compartilhado, no bridge Checkstyle, no wizard `--linter-setup` e na documentação de regras. Se o produto quiser três níveis de verdade, é uma feature transversal do linter, com ADR próprio.

### 2. Regras embutidas em `src/`, fora do catálogo do usuário

O ruleset vive em módulo Python dentro de `src/` e entra na lista de regras em `load_linter_rules()` ([src/config.py:562-612](../src/config.py#L562-L612)), junto do catálogo do projeto e dos plugins globais. Não é um arquivo para o usuário editar, não é baixado, não é uma skill.

Os três canais alternativos foram descartados por fatos medidos, não por preferência:

- **`presets/linter/security.yml`** (o caminho da spec) exige mudança de empacotamento: [pyproject.toml:30-32](../pyproject.toml#L30-L32) inclui apenas `src`/`src.*`, sem `package-data` nem `MANIFEST.in` — o wheel publicado contém só `src/` e o `.dist-info`. Um diretório novo fora de `src/` simplesmente não seria distribuído.
- **Fundir no `.gitpr.linter.yml` do usuário** não alcança ninguém que já tenha o arquivo (o download nunca sobrescreve) e expõe as regras ao wizard `--linter-setup`, que reescreve o arquivo com `yaml.dump` e destrói comentários ([src/linter_wizard.py:186-192](../src/linter_wizard.py#L186-L192)).
- **Plugin global `~/.gitpr/plugins/linter/`** é descoberto por varredura e funciona hoje, mas é global à máquina, sem versionamento e sem i18n — serve para preferência pessoal, não para um gate de CI que precisa ser igual para todo o time.

### 3. Escape pela configuração, não por supressão inline

Duas chaves controlam o ruleset: `GITPR_LINTER_SECURITY` (liga/desliga o conjunto, default ligado) e `GITPR_LINTER_SECURITY_DISABLED_RULES` (lista separada por `;` de nomes de regra a desligar). Supressão por linha ou por arquivo — comentário inline tipo `# gitpr-ignore` — foi explicitamente deixada **fora** desta entrega: é capacidade transversal ao linter, não específica de segurança, e implementá-la aqui criaria um mecanismo de supressão que só metade das regras respeita.

### 4. Uma extensão mínima no motor: `extensions: ["*"]`

Sem ela, "aplica a todo arquivo" é inexprimível: `extensions` é obrigatório na prática e o match é por sufixo ([src/linter_engine.py:16](../src/linter_engine.py#L16)), então `.env`, `id_rsa`, `credentials` e `Dockerfile` ficariam de fora por construção — justamente os lugares onde segredo aparece. A mudança é a menor possível: `"*"` na lista dispensa a checagem de sufixo. Nenhuma outra linha do motor muda.

## Consequências

- **A partir da versão que trouxer a feature, `gitpr -l` e o hook `pre-commit` passam a bloquear commits que antes passavam**, porque o ruleset entra ligado por padrão. É o objetivo declarado, mas é mudança de comportamento para quem já usa a ferramenta — precisa constar da nota de release.
- O usuário não pode editar as regras de segurança; só ligar/desligar o conjunto ou regras individuais por `name`. Um ajuste fino de regex significa mudança no produto.
- **Risco operacional aceito:** regex inválida vira erro bloqueante ([src/linter_engine.py:64-71](../src/linter_engine.py#L64-L71)). Um typo no ruleset bloquearia todo commit do usuário, então a compilação de todas as regras precisa ser testada explicitamente.
- As mensagens passam a usar `__()` — vantagem que o YAML de regra nunca teve —, o que obriga a traduzir as chaves nos seis arquivos de idioma (`tests/test_i18n.py` exige paridade e tradução).
- **Ponto cego aceito:** `.md`, `.txt`, `*.log` e lockfiles nunca chegam ao linter, porque os smart excludes os removem do diff antes ([src/core.py:330](../src/core.py#L330), [:528](../src/core.py#L528)) e o merge de exclusões é união, não override ([src/core.py:259-265](../src/core.py#L259-L265)) — um projeto não pode reverter isso isoladamente.
- Segredo já commitado no histórico não é encontrado; a varredura é só do diff corrente.
- Erros e avisos de segurança **não podem ser redigidos depois**: sem objeto de finding, a mensagem é renderizada na hora ([src/linter_engine.py:51-55](../src/linter_engine.py#L51-L55)). A redação é automática hoje porque o motor só substitui `{file_name}` e `{line_number}` — e vira invariante testado justamente para que ninguém a quebre.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Terceiro nível `critical` no schema | Um nível sem comportamento distinto; mexeria no schema compartilhado, no bridge Checkstyle, no wizard e na doc para não mudar nada |
| Regras no `.gitpr.linter.yml` do usuário | Não alcança quem já tem o arquivo (nunca sobrescreve) e o wizard `--linter-setup` o reescreve destruindo comentários |
| `presets/linter/security.yml` (spec) | Não é distribuído no wheel: não há `package-data` para nada fora de `src/` |
| Template HTTP como os demais arquivos | Não existe offline; e quem já tem o projeto não o recebe sem rodar `--skill` |
| Plugin global `~/.gitpr/plugins/linter/` | Global à máquina, sem versionamento nem i18n; não serve como gate de time em CI |
| Supressão inline `# gitpr-ignore` nesta entrega | Capacidade transversal ao linter, não específica de segurança; meia-implementação vira surpresa |
| Incluir entropia/Gitleaks no v1 | Exige binário externo e não roda no diff remoto (`skip_external=True`); é a evolução já reservada ao tier pago |
