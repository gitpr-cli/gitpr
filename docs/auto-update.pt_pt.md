# Documentação Técnica: Auto-Updater (--update)

O GitPR possui um sistema de atualização automática (**Auto-Updater**) que mantém a ferramenta sempre na versão mais recente, com verificação diária e atualização via *hot-swap*.

---

## 1. Atualização Manual

```bash
gitpr -u
# ou
gitpr --update
```

O comando força a verificação e instalação imediata da versão mais recente.

---

## 2. Verificação Automática Diária

Em cada execução do GitPR (exceto nos modos `--quiet` e `--hook`), a ferramenta verifica silenciosamente se há uma nova versão disponível. O resultado é colocado em cache durante **24 horas** no ficheiro `~/.gitpr/update_cache.json` para evitar chamadas repetidas à API.

Se houver uma nova versão, é apresentada uma notificação no final da execução.

---

## 3. Métodos de Atualização

O Auto-Updater deteta automaticamente o método de instalação:

### 3.1 Instalação via pip

```bash
pip install --upgrade gitpr-cli
```

### 3.2 Instalação via Binário (PyInstaller)

O GitPR usa a técnica de **Hot-Swap** para binários standalone:

1. Verifica a versão mais recente nas [GitHub Releases](https://github.com/natanfiuza/gitpr/releases)
2. Descarrega o novo executável
3. Renomeia o `.exe` atual para `.exe.old`
4. Move o novo binário para o lugar
5. Em caso de falha, reverte para o `.exe.old` (rollback automático)
6. Na próxima execução, remove o `.old` automaticamente (limpeza)

---

## 4. Guardião de Ligação

Antes de qualquer operação de rede, o GitPR verifica a conetividade via socket `8.8.8.8:53`. Se não houver internet, a ferramenta opera normalmente em modo offline — sem bloquear ou mostrar erros de ligação.

---

## 5. Fontes de Versão

| Fonte | Utilização |
| --- | --- |
| **PyPI** | Versão para instalações pip (`pip install gitpr-cli`) |
| **GitHub Releases** | Versão para binários standalone (`.exe`) |

A versão local é definida em `src/updater.py` (`__version__`) e incrementada a cada release.

> **Nota:** Consulte também a [documentação principal (README.md)](../README.md) para informações sobre instalação e configuração inicial.
