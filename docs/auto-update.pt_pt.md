# Documentação Técnica: Auto-Updater (--update)

O GitPR é distribuído exclusivamente pelo PyPI. O **Auto-Updater** verifica a cada execução se foi publicada uma nova versão, guardando a resposta durante no máximo uma hora, e mantém a ferramenta sempre na release mais recente.

---

## 1. Verificação Manual

```bash
gitpr -u
# ou
gitpr --update
```

O comando força uma verificação imediata no PyPI — ignora a cache — e apresenta o comando de atualização. Ele **não** instala nada — a atualização em si é sempre feita pelo seu gestor de pacotes.

---

## 2. Bloqueio Obrigatório de Atualização

A cada execução do GitPR (exceto nos modos `--quiet`, `--hook` e `--mcp`), e antes dos subcomandos interativos, a ferramenta verifica se foi publicada uma versão mais recente. O resultado fica em cache durante **1 hora** — uma janela móvel, não o dia do calendário local — no ficheiro `~/.gitpr/update_cache.json` para evitar chamadas repetidas à API. `gitpr -u`/`--update` ignora sempre a cache.

Quando a versão publicada é mais recente que a local, o GitPR **bloqueia a execução**: apresenta as duas versões, mostra o comando `pip install --upgrade gitpr-cli` e termina com um estado diferente de zero, sem executar qualquer trabalho.

As versões são comparadas segundo o PEP 440: um pré-release remoto é ignorado enquanto a versão instalada é estável (o pip não o instala sem `--pre`), e uma versão remota que não possa ser interpretada conta como desconhecida.

Não existe flag, fallback ou modo de compatibilidade que mantenha uma **release instalada** desatualizada a funcionar — atualizar é a única forma de continuar. Um checkout usado para desenvolvimento local tem uma única chave de escape, documentada em [Instalar o GitPR a partir do código-fonte](tutorial/install-from-source.pt_pt.md).

### Exceções

O bloqueio nunca é accionado para:

| Contexto | Motivo |
| --- | --- |
| `--quiet` | Scripts e automações que descartam a saída |
| `--hook` | Git hooks (`prepare-commit-msg`, métricas) — nunca podem quebrar um commit |
| `--mcp` / `gitpr-mcp` | Servidor MCP consumido por IDEs e agentes |
| `-u` / `--update` | É precisamente o comando que explica como atualizar |
| `-h --<flag>` | Ajuda contextual |
| `gitpr <subcomando>` sem terminal | CI, pipes e cron nunca podem ser bloqueados — o gate de subcomando só é accionado quando a execução pode perguntar ao utilizador |
| `gitpr <subcomando> -h` / `--help` | Ler a ajuda nunca pode ser bloqueado |

`--help` e `--version` também não são afetados: o Click resolve-os antes de o corpo do comando ser executado. A ajuda de subcomando é isenta pela linha de comandos em bruto. Invocações pela superfície de flags (`gitpr --status`, `gitpr -c`, …) mantêm o comportamento original e são bloqueadas independentemente do terminal.

### Comportamento Offline

Quando não é possível determinar a versão publicada — sem internet e sem cache com menos de uma hora, ou uma resposta que não é uma versão válida — o GitPR é executado normalmente. Um utilizador offline nunca pode ficar preso a um comando que não consegue executar.

---

## 3. Aplicar a Atualização

```bash
pip install --upgrade gitpr-cli
```

Utilizadores de `pipx`, `uv` ou `poetry` devem atualizar através da própria ferramenta (`pipx upgrade gitpr-cli`, `uv tool upgrade gitpr-cli`, …).

---

## 4. Guardião de Conexão

Antes de qualquer operação de rede, o GitPR verifica a conectividade via socket `8.8.8.8:53`. Se não houver internet, a ferramenta opera normalmente em modo offline — sem travar ou mostrar erros de conexão.

---

## 5. Fonte de Versão

| Fonte | Uso |
| --- | --- |
| **PyPI** (`pypi.org/pypi/gitpr-cli/json`) | Fonte única da versão publicada |

A versão local é definida em `src/updater.py` (`__version__`) e incrementada a cada release.

> **Nota:** Consulte também a [documentação principal (README.md)](../README.md) para informações sobre instalação e configuração inicial.
