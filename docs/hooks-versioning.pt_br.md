# Versionamento e Sincronização Automática de Scripts de Hooks

Esta documentação detalha a arquitetura e o funcionamento do sistema de versionamento e sincronização automática dos scripts de Git hooks do GitPR. O sistema garante que os scripts de hooks instalados nos seus repositórios estejam sempre atualizados com a versão mais recente, respeitando suas preferências de idioma.

---

## 1. Visão Geral

O GitPR inclui um sistema automático de versionamento para scripts de Git hooks (`pre-commit`, `prepare-commit-msg`, `pre-push`, `post-checkout`, `post-merge`). Toda vez que você executa `gitpr`, o sistema verifica silenciosamente se os hooks instalados correspondem à versão mais recente disponível. Se uma nova versão for detectada — ou se o idioma tiver sido alterado — os hooks são automaticamente baixados e atualizados novamente.

Este mecanismo é independente do auto-updater principal do GitPR (`--update`) e opera em uma cadência de versão separada, já que os scripts de hooks evoluem em um ritmo diferente do CLI em si.

---

## 2. Arquitetura

### 2.1 Marcadores de Versão

| Marcador | Localização | Finalidade |
|----------|-------------|------------|
| `__scripts_version__` | `src/updater.py` | Fonte única de verdade — define a versão atual dos scripts de hooks enviados com esta release do GitPR |
| `SCRIPTS_VERSION` | `~/.gitpr/.env` | Rastreia qual versão está atualmente instalada na máquina do usuário |
| `SCRIPTS_LANG` | `~/.gitpr/.env` | Rastreia o idioma dos scripts instalados (ex.: `pt_br`, `fr`) |

### 2.2 Fluxo de Sincronização Automática

```
execução do gitpr
    │
    ├─ Lê SCRIPTS_VERSION e SCRIPTS_LANG do ~/.gitpr/.env
    │
    ├─ Compara com __scripts_version__ e CURRENT_LANG
    │
    ├─ Coincidem? → Pular (via rápida — leitura única do .env, sem rede)
    │
    └─ Diferem ou ausentes? → Baixar e instalar hooks no idioma atual
                               → Gravar SCRIPTS_VERSION + SCRIPTS_LANG
```

A via rápida (quando as versões coincidem) é uma única leitura do arquivo `.env` com zero I/O de rede.

### 2.3 Idiomas Suportados

| Idioma | Código | Sufixo do Script | Exemplo |
|--------|--------|------------------|---------|
| Inglês (padrão) | `en` | *(sem sufixo)* | `pre-commit-template.sh` |
| Português (Brasil) | `pt_br` | `.pt_br` | `pre-commit-template.pt_br.sh` |
| Português (Portugal) | `pt_pt` | `.pt_pt` | `pre-commit-template.pt_pt.sh` |
| Francês | `fr` | `.fr` | `pre-commit-template.fr.sh` |
| Espanhol | `es` | `.es` | `pre-commit-template.es.sh` |

O inglês é o idioma padrão e de fallback. Se um script em um idioma específico não for encontrado no servidor (HTTP 404), o sistema automaticamente utiliza a versão em inglês.

---

## 3. Como Funciona

### 3.1 Primeira Execução (Sem Hooks Instalados)

Quando um usuário executa `gitpr --installhooks` ou `gitpr --install` pela primeira vez:

1. O GitPR detecta o idioma atual (`CURRENT_LANG`) do SO ou do `.env`
2. Baixa primeiro os scripts específicos do idioma (ex.: `pre-commit-template.pt_br.sh`)
3. Usa o fallback em inglês se a variante de idioma não estiver disponível (HTTP 404)
4. Aplica permissões de execução (`chmod +x`)
5. Grava `SCRIPTS_VERSION` e `SCRIPTS_LANG` no `~/.gitpr/.env`

### 3.2 Execuções Seguintes (Sincronização Automática)

Em toda execução do `gitpr`:

1. `check_and_update_hooks_scripts()` lê `SCRIPTS_VERSION` e `SCRIPTS_LANG` do `.env`
2. Compara com `__scripts_version__` (do código) e `CURRENT_LANG`
3. Se ambos coincidirem → nada acontece (via rápida)
4. Se a versão diferir → os hooks são baixados novamente no idioma atual
5. Se o idioma diferir → os hooks são baixados novamente para corresponder ao novo idioma
6. Em caso de sucesso → os marcadores são atualizados para que execuções futuras pulem a rede

**Invocações protegidas:** A sincronização automática é ignorada durante chamadas internas do CLI (`--quiet`, `--hook`, `--mcp`) para evitar latência de rede em contextos automatizados.

### 3.3 Gravação Somente com Sucesso Total

O marcador `SCRIPTS_VERSION` só é gravado quando **todos os 5 hooks** são baixados e instalados com sucesso. Se algum hook falhar (erro de rede, download parcial), o marcador não é atualizado, garantindo que a instalação com falha seja tentada novamente na próxima execução do `gitpr`.

---

## 4. Tipos de Scripts de Hook

O sistema gerencia 5 tipos de hooks do Git:

| Hook | Template de Script | Finalidade |
|------|-------------------|------------|
| `pre-commit` | `pre-commit-template.sh` | Executa o linter estático antes de cada commit |
| `prepare-commit-msg` | `prepare-commit-msg-template.sh` | Gera mensagens de commit com IA |
| `pre-push` | `pre-push-template.sh` | Valida o código antes de enviar para o remote |
| `post-checkout` | `post-checkout-template.sh` | Ações após troca de branch |
| `post-merge` | `post-merge-template.sh` | Ações após um merge bem-sucedido |

Todos os scripts de hook são **thin shims** — eles chamam o CLI `gitpr` internamente. A lógica real reside no código do CLI, não nos arquivos de hook. Isso significa que, mesmo que os hooks estejam ligeiramente desatualizados, eles continuam funcionando corretamente porque sempre invocam o CLI mais recente instalado.

---

## 5. Configuração

### 5.1 Variáveis de Ambiente

| Variável | Arquivo | Descrição |
|----------|---------|-----------|
| `SCRIPTS_VERSION` | `~/.gitpr/.env` | Versão dos scripts de hook instalados (gerenciado automaticamente) |
| `SCRIPTS_LANG` | `~/.gitpr/.env` | Idioma dos scripts instalados (gerenciado automaticamente) |
| `GITPR_LANG` | `~/.gitpr/.env` | Idioma de interface preferido do usuário |

### 5.2 Constantes do Código Fonte

| Constante | Arquivo | Descrição |
|-----------|---------|-----------|
| `__scripts_version__` | `src/updater.py` | Versão atual dos scripts de hooks |
| `_SCRIPT_LANG_SUFFIXES` | `src/core.py` | Conjunto de sufixos de idioma suportados |
| `SCRIPTS_BASE_URL` | `src/core.py` | URL base para download dos scripts |

### 5.3 Adicionando um Novo Idioma

Para adicionar suporte a um novo idioma:

1. Crie 5 arquivos `.sh` traduzidos no diretório `scripts/` (um por tipo de hook)
2. Adicione o código do idioma a `_SCRIPT_LANG_SUFFIXES` no `src/core.py`
3. O sistema de sincronização automática detectará e servirá automaticamente o novo idioma

### 5.4 Incrementando a Versão dos Scripts

Quando os scripts de hook forem modificados:

1. Incremente `__scripts_version__` no `src/updater.py`
2. Na próxima execução do `gitpr`, todos os clientes instalados detectarão a diferença e atualizarão seus hooks automaticamente

---

## 6. Solução de Problemas

### Os hooks não estão atualizando

**Sintoma:** Executar `gitpr` não atualiza os hooks instalados mesmo que exista uma nova versão.

**Solução:**
- Verifique se o diretório `.git/hooks` existe no seu projeto
- Verifique `SCRIPTS_VERSION` no `~/.gitpr/.env` — se corresponder a `__scripts_version__`, nenhuma atualização é necessária
- Exclua manualmente `SCRIPTS_VERSION` do `.env` para forçar um novo download na próxima execução
- Execute `gitpr --installhooks` para forçar uma instalação nova

### Idioma errado nos hooks

**Sintoma:** Os scripts de hook exibem mensagens no idioma errado.

**Solução:**
- Verifique `GITPR_LANG` no `~/.gitpr/.env`
- Exclua `SCRIPTS_LANG` do `.env` para forçar a redetecção do idioma
- Execute `gitpr --installhooks` para reinstalar no idioma correto

### Instalação parcial

**Sintoma:** Alguns hooks estão instalados, mas `SCRIPTS_VERSION` não foi gravado.

**Solução:**
- Isso é intencional — o marcador só é gravado quando todos os 5 hooks são bem-sucedidos
- Verifique sua conexão de rede
- Execute `gitpr --installhooks` novamente para tentar novamente os downloads com falha

---

## 7. Referência da API

### `check_and_update_hooks_scripts()`

```python
# src/core.py
def check_and_update_hooks_scripts():
    """Silent auto-sync of installed Git hooks (version + language gated).

    Called on every gitpr execution. Compares SCRIPTS_VERSION and
    SCRIPTS_LANG in ~/.gitpr/.env against the shipped constants. When
    they match the check is a single .env read with no network I/O.

    When they differ (or are missing) and the current project has a
    .git/hooks directory, hooks are re-downloaded in the current language.
    On success the markers are stamped so future runs skip the network.
    """
```

### `install_git_hooks()`

```python
# src/core.py
def install_git_hooks():
    """Downloads and installs Git hook scripts with i18n support.

    Detects the current language (CURRENT_LANG) and tries to download
    language-specific scripts first (e.g. pre-commit-template.pt_br.sh).
    Falls back to the English base version when a translation is unavailable.

    After a successful install, stamps SCRIPTS_VERSION and SCRIPTS_LANG
    in ~/.gitpr/.env so the auto-sync check can skip network calls.

    Returns True when all 5 hooks installed successfully.
    """
```

---

## 8. Decisões de Design

- **Marcador de versão independente:** `__scripts_version__` é separado de `__lang_version__` porque os scripts de hooks mudam em uma cadência diferente dos recursos de idioma
- **Marcador complementar `SCRIPTS_LANG`:** Impede a alternância de idioma quando usuários executam `gitpr --lang fr` uma vez — a sincronização automática não baixa novamente a menos que a versão OU o idioma sejam diferentes
- **Abordagem de whitelist:** Apenas 4 sufixos explícitos (`pt_br`, `pt_pt`, `fr`, `es`) acionam downloads específicos de idioma; qualquer outro idioma utiliza o inglês (sem cascata de 404)
- **Marcador global (não por projeto):** O marcador `SCRIPTS_VERSION` reside em `~/.gitpr/.env` (global). Após um incremento de versão, o primeiro projeto que executa `gitpr` é atualizado e grava o marcador; os hooks de outros projetos são atualizados na próxima execução do `gitpr` neles. Como os hooks são thin shims, hooks desatualizados ainda funcionam — a lógica real reside no CLI
- **Sincronização protegida:** A sincronização automática é ignorada durante invocações `--quiet`, `--hook` e `--mcp` para evitar latência de rede em contextos automatizados
