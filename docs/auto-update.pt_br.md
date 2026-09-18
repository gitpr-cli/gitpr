# Documentação Técnica: Auto-Updater (--update)

O GitPR é distribuído exclusivamente pelo PyPI. O **Auto-Updater** verifica diariamente se uma nova versão foi publicada e mantém a ferramenta sempre na release mais recente.

---

## 1. Verificação Manual

```bash
gitpr -u
# ou
gitpr --update
```

O comando força uma verificação imediata no PyPI e exibe o comando de atualização. Ele **não** instala nada — a atualização em si é sempre feita pelo seu gerenciador de pacotes.

---

## 2. Bloqueio Obrigatório de Atualização

A cada execução do GitPR (exceto nos modos `--quiet`, `--hook` e `--mcp`), a ferramenta verifica se uma versão mais nova foi publicada. O resultado fica em cache por **24 horas** no arquivo `~/.gitpr/update_cache.json` para evitar chamadas repetidas à API.

Quando a versão publicada é mais nova que a local, o GitPR **bloqueia a execução**: exibe as duas versões, mostra o comando `pip install --upgrade gitpr-cli` e encerra com status diferente de zero, sem executar nenhum trabalho.

Não existe flag, fallback ou modo de compatibilidade que mantenha uma **release instalada** desatualizada rodando — atualizar é a única forma de continuar. Um checkout usado para desenvolvimento local tem uma única chave de escape, documentada em [Instalando o GitPR do código-fonte](tutorial/install-from-source.pt_br.md).

### Exceções

O bloqueio nunca dispara para:

| Contexto | Motivo |
| --- | --- |
| `--quiet` | Scripts e automações que descartam a saída |
| `--hook` | Git hooks (`prepare-commit-msg`, métricas) — nunca podem quebrar um commit |
| `--mcp` / `gitpr-mcp` | Servidor MCP consumido por IDEs e agentes |
| `-u` / `--update` | É justamente o comando que explica como atualizar |
| `-h --<flag>` | Ajuda contextual |

`--help` e `--version` também não são afetados: o Click os resolve antes do corpo do comando rodar.

### Comportamento Offline

Quando não é possível determinar a versão publicada — sem internet e sem cache do dia atual — o GitPR executa normalmente. Um usuário offline nunca pode ficar preso a um comando que não consegue rodar.

---

## 3. Aplicando a Atualização

```bash
pip install --upgrade gitpr-cli
```

Usuários de `pipx`, `uv` ou `poetry` devem atualizar pela própria ferramenta (`pipx upgrade gitpr-cli`, `uv tool upgrade gitpr-cli`, …).

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
