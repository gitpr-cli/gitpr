# Documentação Técnica: Geração de Mensagens de Commit com IA (--commit)

O comando `--commit` (`-c`) do GitPR gera automaticamente mensagens de commit no formato **Conventional Commits** usando inteligência artificial para analisar as suas alterações locais.

---

## 1. Utilização Básica

```bash
gitpr -c
```

A ferramenta analisa o `git diff HEAD` e apresenta a mensagem sugerida diretamente na consola:

```
📝 Sugestão de Commit:

feat: adiciona validacao de email no formulario de registo

- Implementa regex de validacao RFC 5322
- Adiciona mensagens de erro localizadas (pt-BR)
- Corrige edge case de emails com dominios internacionais
```

---

## 2. Formato Conventional Commits

A IA é instruída a gerar mensagens no padrão:

```
tipo: descricao curta

Corpo opcional com detalhes adicionais
```

**Tipos utilizados:** `feat`, `fix`, `refactor`, `test`, `chore`, `docs`

---

## 3. Integração com Git Hooks

O `--commit` é usado internamente pelo hook `prepare-commit-msg`. Quando instalado via `gitpr -ih`, o hook executa:

```bash
gitpr --commit --hook <caminho-do-ficheiro-temporario>
```

A flag `--hook` (interna/oculta) faz com que a mensagem sugerida seja injetada diretamente no editor do Git, em vez de ser apresentada na consola.

---

## 4. Personalização via Skill

O comportamento da IA pode ser personalizado através do ficheiro `.gitpr.commit.md` na raiz do projeto:

```bash
gitpr -s          # Descarrega o template .gitpr.commit.md
# Edite o ficheiro conforme as convenções da sua equipa
gitpr -c          # A IA usará as suas regras personalizadas
```

---

## 5. Seleção de Fornecedor de IA

```bash
gitpr -c -p gemini       # Força Google Gemini
gitpr -c -p deepseek     # Força DeepSeek
```

---

## 6. Cache de Respostas

O GitPR gera um hash MD5 do seu diff + instruções. Se executar `gitpr -c` novamente **sem alterar o código**, a resposta é devolvida instantaneamente a partir do cache local, poupando quotas da API.

> **Nota:** Consulte também a [documentação principal (README.md)](../README.md) para uma visão geral de todas as funcionalidades.
