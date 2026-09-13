# Versionamento e Sincronização Automática de Scripts de Hooks

Esta documentação detalha a arquitetura e o funcionamento do sistema de versionamento e sincronização automática dos scripts de Git hooks do GitPR. O sistema garante que os scripts de hooks instalados nos seus repositórios estejam sempre atualizados com a versão mais recente, respeitando as suas preferências de idioma.

---

## 1. Visão Geral

O GitPR inclui um sistema automático de versionamento para scripts de Git hooks (`pre-commit`, `prepare-commit-msg`, `pre-push`, `post-checkout`, `post-merge`). Sempre que executa `gitpr`, o sistema verifica silenciosamente se os hooks instalados correspondem à versão mais recente disponível. Se uma nova versão for detetada — ou se o idioma tiver sido alterado — os hooks são automaticamente descarregados e atualizados novamente.

Este mecanismo é independente do auto-updater principal do GitPR (`--update`) e opera numa cadência de versão separada, já que os scripts de hooks evoluem a um ritmo diferente do CLI em si.

---

## 2. Arquitetura

### 2.1 Marcadores de Versão

| Marcador | Localização | Finalidade |
|----------|-------------|------------|
| `__scripts_version__` | `src/updater.py` | Fonte única de verdade — define a versão atual dos scripts de hooks enviados com esta release do GitPR |
| `SCRIPTS_VERSION` | `~/.gitpr/.env` | Rastreia qual versão está atualmente instalada na máquina do utilizador |
| `SCRIPTS_LANG` | `~/.gitpr/.env` | **O idioma que pediu.** Vazio segue o idioma da interface. Editado no ecrã `gitpr config` |
| `SCRIPTS_INSTALLED_LANG` | `~/.gitpr/.env` | **O que está em disco.** Gravado pelo instalador, nunca pelo utilizador, e apresentado como apenas leitura no ecrã de configuração |

Os dois marcadores de idioma são deliberadamente separados. A auto-sincronização tem de detetar uma mudança de idioma, e isso exige comparar o que está instalado com o que é pretendido — dois valores independentes. Um único `SCRIPTS_LANG` gravado pelo instalador seria comparado consigo próprio, o que nunca pode diferir, pelo que mudar de idioma manteria os hooks silenciosamente no antigo.

### 2.2 Fluxo de Sincronização Automática

```
execução do gitpr
    │
    ├─ Lê SCRIPTS_VERSION e SCRIPTS_INSTALLED_LANG do ~/.gitpr/.env
    │
    ├─ Calcula o idioma pretendido: SCRIPTS_LANG (a escolha, do ficheiro)
    │  ou o idioma da interface em tempo real quando está vazio
    │
    ├─ Coincidem? → Saltar (via rápida — leitura única do .env, sem rede)
    │
    └─ Diferem ou ausentes? → Descarregar e instalar hooks no idioma pretendido
                               → Gravar SCRIPTS_VERSION + SCRIPTS_INSTALLED_LANG
```

A via rápida (quando as versões coincidem) é uma única leitura do ficheiro `.env` com zero I/O de rede.

O idioma pretendido é lido do ficheiro em vez de `os.getenv()`, e o idioma da interface é lido de `src.i18n` no momento da chamada em vez da cópia congelada que este módulo guarda — `set_lang()`, que é o que o `--lang` invoca, reatribui a constante em vez de a modificar. Sem ambos, `gitpr --lang fr_fr` instalaria os hooks no idioma em que o processo arrancou.

### 2.3 Idiomas Suportados

A interface escreve um idioma de uma forma e o ficheiro publicado escreve-o de outra, e as duas não são intercambiáveis: `GITPR_LANG` e `SCRIPTS_LANG` contêm `es_es`/`fr_fr`, enquanto os ficheiros no servidor se chamam `.es`/`.fr`. `HOOK_SCRIPT_SUFFIXES`, em `src/core.py`, é esse mapa, e nada mais pode assumir que os dois lados coincidem.

| Idioma | Código de interface / `SCRIPTS_LANG` | Sufixo do Script | Exemplo |
|--------|--------------------------------------|------------------|---------|
| Inglês (padrão) | `en_us` | *(sem sufixo)* | `pre-commit-template.sh` |
| Português (Brasil) | `pt_br` | `.pt_br` | `pre-commit-template.pt_br.sh` |
| Português (Portugal) | `pt_pt` | `.pt_pt` | `pre-commit-template.pt_pt.sh` |
| Espanhol | `es_es` | `.es` | `pre-commit-template.es.sh` |
| Francês | `fr_fr` | `.fr` | `pre-commit-template.fr.sh` |

Um código fora do mapa instala o script base, que é o inglês. O inglês é também o fallback quando um script num idioma específico falta no servidor (HTTP 404).

---

## 3. Como Funciona

### 3.1 Primeira Execução (Sem Hooks Instalados)

Quando um utilizador executa `gitpr --installhooks` ou `gitpr --install` pela primeira vez:

1. O GitPR resolve o idioma efetivo: `SCRIPTS_LANG` quando escolheu um, o idioma da interface em tempo real caso contrário
2. Descarrega primeiro os scripts específicos do idioma (ex.: `pre-commit-template.pt_pt.sh`)
3. Usa o fallback em inglês se a variante de idioma não estiver disponível (HTTP 404)
4. Aplica permissões de execução (`chmod +x`)
5. Grava `SCRIPTS_VERSION` e `SCRIPTS_INSTALLED_LANG` no `~/.gitpr/.env`. `SCRIPTS_LANG` **não** é gravado — é a sua escolha, e um instalador que o sobrescrevesse apagaria o pedido que deve satisfazer

### 3.2 Execuções Seguintes (Sincronização Automática)

Em cada execução do `gitpr`:

1. `check_and_update_hooks_scripts()` lê `SCRIPTS_VERSION` e `SCRIPTS_INSTALLED_LANG` do `.env`
2. Compara com `__scripts_version__` (do código) e o idioma efetivo
3. Se ambos coincidirem → nada acontece (via rápida)
4. Se a versão diferir → os hooks são descarregados novamente no idioma efetivo
5. Se o idioma diferir → os hooks são descarregados novamente para corresponder ao novo idioma, uma vez; a execução seguinte volta a ser via rápida
6. Em caso de sucesso → os marcadores são atualizados para que execuções futuras saltem a rede

**Invocações protegidas:** A sincronização automática é ignorada durante chamadas internas do CLI (`--quiet`, `--hook`, `--mcp`) para evitar latência de rede em contextos automatizados.

### 3.3 Gravação Apenas com Sucesso Total

O marcador `SCRIPTS_VERSION` só é gravado quando **todos os 5 hooks** são descarregados e instalados com sucesso. Se algum hook falhar (erro de rede, descarregamento parcial), o marcador não é atualizado, garantindo que a instalação com falha seja tentada novamente na próxima execução do `gitpr`.

---

## 4. Tipos de Scripts de Hook

O sistema gere 5 tipos de hooks do Git:

| Hook | Template de Script | Finalidade |
|------|-------------------|------------|
| `pre-commit` | `pre-commit-template.sh` | Executa o linter estático antes de cada commit |
| `prepare-commit-msg` | `prepare-commit-msg-template.sh` | Gera mensagens de commit com IA |
| `pre-push` | `pre-push-template.sh` | Valida o código antes de enviar para o remoto |
| `post-checkout` | `post-checkout-template.sh` | Ações após troca de branch |
| `post-merge` | `post-merge-template.sh` | Ações após um merge bem-sucedido |

Todos os scripts de hook são **thin shims** — eles chamam o CLI `gitpr` internamente. A lógica real reside no código do CLI, não nos ficheiros de hook. Isto significa que, mesmo que os hooks estejam ligeiramente desatualizados, eles continuam a funcionar corretamente porque invocam sempre o CLI mais recente instalado.

---

## 5. Configuração

### 5.1 Variáveis de Ambiente

| Variável | Ficheiro | Descrição |
|----------|----------|-----------|
| `SCRIPTS_VERSION` | `~/.gitpr/.env` | Versão dos scripts de hook instalados (gerido automaticamente) |
| `SCRIPTS_INSTALLED_LANG` | `~/.gitpr/.env` | Idioma dos scripts em disco (gerido automaticamente) |
| `SCRIPTS_LANG` | `~/.gitpr/.env` | Idioma que quer para os hooks. Vazio segue `GITPR_LANG`. Editado no ecrã `gitpr config`, em **Avançado → Git Hooks** |
| `GITPR_LANG` | `~/.gitpr/.env` | Idioma de interface preferido do utilizador |

### 5.2 Constantes do Código Fonte

| Constante | Ficheiro | Descrição |
|-----------|----------|-----------|
| `__scripts_version__` | `src/updater.py` | Versão atual dos scripts de hooks |
| `HOOK_SCRIPT_SUFFIXES` | `src/core.py` | Código do idioma da interface → sufixo do script publicado |
| `effective_hook_lang()` | `src/core.py` | `SCRIPTS_LANG` quando definido, o idioma da interface em tempo real caso contrário |
| `SCRIPTS_BASE_URL` | `src/core.py` | URL base para descarregamento dos scripts |

### 5.3 Adicionar um Novo Idioma

Para adicionar suporte a um novo idioma:

1. Crie 5 ficheiros `.sh` traduzidos no diretório `scripts/` (um por tipo de hook)
2. Adicione o mapeamento a `HOOK_SCRIPT_SUFFIXES` no `src/core.py` — a chave é o código da interface (`es_es`), o valor é o sufixo do ficheiro (`.es`)
3. O sistema de sincronização automática detetará e servirá automaticamente o novo idioma

### 5.4 Incrementar a Versão dos Scripts

Quando os scripts de hook forem modificados:

1. Incremente `__scripts_version__` no `src/updater.py`
2. Na próxima execução do `gitpr`, todos os clientes instalados detetarão a diferença e atualizarão os seus hooks automaticamente

---

## 6. Resolução de Problemas

### Os hooks não estão a atualizar

**Sintoma:** Executar `gitpr` não atualiza os hooks instalados mesmo que exista uma nova versão.

**Solução:**
- Verifique se o diretório `.git/hooks` existe no seu projeto
- Verifique `SCRIPTS_VERSION` no `~/.gitpr/.env` — se corresponder a `__scripts_version__`, nenhuma atualização é necessária
- Elimine manualmente `SCRIPTS_VERSION` do `.env` para forçar um novo descarregamento na próxima execução
- Execute `gitpr --installhooks` para forçar uma instalação nova

### Idioma errado nos hooks

**Sintoma:** Os scripts de hook exibem mensagens no idioma errado.

**Solução:**
- Verifique `SCRIPTS_LANG` no `~/.gitpr/.env`, ou o campo **Hooks Language** em **Avançado → Git Hooks** no ecrã `gitpr config`. Vazio segue `GITPR_LANG`
- Compare com `SCRIPTS_INSTALLED_LANG`, que regista o que está realmente em disco — a diferença entre os dois é o sinal de que há uma reinstalação pendente
- Execute `gitpr --installhooks` para reinstalar de imediato, ou execute apenas qualquer comando `gitpr`: a auto-sincronização reinstala uma vez e depois volta à via rápida

### Instalação parcial

**Sintoma:** Alguns hooks estão instalados, mas `SCRIPTS_VERSION` não foi gravado.

**Solução:**
- Isto é intencional — o marcador só é gravado quando todos os 5 hooks são bem-sucedidos
- Verifique a sua ligação de rede
- Execute `gitpr --installhooks` novamente para tentar novamente os descarregamentos com falha

---

## 7. Referência da API

### `check_and_update_hooks_scripts()`

```python
# src/core.py
def check_and_update_hooks_scripts():
    """Silent auto-sync of installed Git hooks (version + language gated).

    Called on every gitpr execution. Compares SCRIPTS_VERSION and
    SCRIPTS_INSTALLED_LANG in ~/.gitpr/.env against the shipped version
    and the wanted language. When they match the check is a single
    .env read with no network I/O.

    The language comparison is between what is ON DISK and what is
    WANTED, two independent sources: switching SCRIPTS_LANG on the
    configuration screen reinstalls once, and the next run goes back to
    the fast path.

    When they differ (or are missing) and the current project has a
    .git/hooks directory, hooks are re-downloaded in the wanted language.
    On success the markers are stamped so future runs skip the network.
    """
```

### `install_git_hooks()`

```python
# src/core.py
def install_git_hooks():
    """Downloads and installs Git hook scripts with i18n support.

    Installs the hooks in the effective language — SCRIPTS_LANG when the
    user chose one, the interface language otherwise — trying the
    language-specific scripts first (e.g. pre-commit-template.pt_br.sh)
    and falling back to the English base version when a translation is
    unavailable.

    After a successful install, stamps SCRIPTS_VERSION and
    SCRIPTS_INSTALLED_LANG in ~/.gitpr/.env so the auto-sync check can
    skip network calls. SCRIPTS_LANG is NOT written here: it is the
    user's choice, and comparing a choice against itself could never
    detect a language change.
    """
```

### `effective_hook_lang()`

```python
# src/core.py
def effective_hook_lang():
    """The language the hooks should be installed in.

    SCRIPTS_LANG is the user's choice, set on the configuration screen;
    empty means "follow the interface language". It is read from the FILE
    rather than os.getenv() because load_dotenv(override=False) lets a
    variable exported in the shell beat the value the user just edited.
    """
```

---

## 8. Decisões de Design

- **Marcador de versão independente:** `__scripts_version__` é separado de `__lang_version__` porque os scripts de hooks mudam numa cadência diferente dos recursos de idioma
- **Dois marcadores de idioma, não um:** `SCRIPTS_LANG` é o pedido e `SCRIPTS_INSTALLED_LANG` é o que o instalador deixou em disco. A auto-sincronização compara-os, pelo que mudar de idioma reinstala uma vez e depois estabiliza. Um único marcador — gravado pelo instalador e comparado consigo próprio — mantinha os utilizadores silenciosamente no idioma com que começaram, por muitas vezes que alterassem a definição
- **O instalador nunca grava o pedido:** sobrescreveria o próprio valor que deve satisfazer, e a comparação tornar-se-ia uma tautologia
- **O idioma da interface é lido em tempo real:** o `core.py` guarda uma cópia de `i18n.CURRENT_LANG` do momento da importação, e o `set_lang()` (o que o `--lang` invoca) reatribui o original. "Seguir o idioma da interface" lê-o no momento da chamada, pelo que `gitpr --lang fr_fr` instala hooks em francês
- **Abordagem de whitelist:** Apenas os 4 códigos mapeados (`pt_br`, `pt_pt`, `es_es`, `fr_fr`) acionam descarregamentos específicos de idioma; qualquer outro idioma utiliza o inglês (sem cascata de 404). O mapa é explícito porque o código da interface e o sufixo do ficheiro não coincidem — `es_es` é publicado como `.es`
- **Marcador global (não por projeto):** O marcador `SCRIPTS_VERSION` reside em `~/.gitpr/.env` (global). Após um incremento de versão, o primeiro projeto que executa `gitpr` é atualizado e grava o marcador; os hooks de outros projetos são atualizados na próxima execução do `gitpr` neles. Como os hooks são thin shims, hooks desatualizados ainda funcionam — a lógica real reside no CLI
- **Sincronização protegida:** A sincronização automática é ignorada durante invocações `--quiet`, `--hook` e `--mcp` para evitar latência de rede em contextos automatizados
