# Documentação Técnica: Auto-Updater (--update)

O GitPR é distribuído exclusivamente pelo PyPI. O **Auto-Updater** verifica diariamente se uma nova versão foi publicada e mantém a ferramenta sempre na release mais recente.

---

## 1. Verificação Manual

```bash
gitpr -u
# ou
gitpr --update
```

O comando força uma verificação imediata no PyPI e apresenta o comando de atualização. Ele **não** instala nada — a atualização em si é sempre feita pelo seu gestor de pacotes.

---

## 2. Bloqueio Obrigatório de Atualização

A cada execução do GitPR (exceto nos modos `--quiet`, `--hook` e `--mcp`), a ferramenta verifica se foi publicada uma versão mais recente. O resultado fica em cache durante **24 horas** no ficheiro `~/.gitpr/update_cache.json` para evitar chamadas repetidas à API.

Quando a versão publicada é mais recente que a local, o GitPR **bloqueia a execução**: apresenta as duas versões, mostra o comando `pip install --upgrade gitpr-cli` e termina com um estado diferente de zero, sem executar qualquer trabalho.

Não existe flag, fallback ou modo de compatibilidade que mantenha uma versão desatualizada a funcionar — atualizar é a única forma de continuar.

### Exceções

O bloqueio nunca é accionado para:

| Contexto | Motivo |
| --- | --- |
| `--quiet` | Scripts e automações que descartam a saída |
| `--hook` | Git hooks (`prepare-commit-msg`, métricas) — nunca podem quebrar um commit |
| `--mcp` / `gitpr-mcp` | Servidor MCP consumido por IDEs e agentes |
| `-u` / `--update` | É precisamente o comando que explica como atualizar |
| `-h --<flag>` | Ajuda contextual |

`--help` e `--version` também não são afetados: o Click resolve-os antes de o corpo do comando ser executado.

### Comportamento Offline

Quando não é possível determinar a versão publicada — sem internet e sem cache do dia atual — o GitPR é executado normalmente. Um utilizador offline nunca pode ficar preso a um comando que não consegue executar.

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
