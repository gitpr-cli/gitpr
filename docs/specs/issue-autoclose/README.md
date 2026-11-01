# Pacote de especificação — Fechamento automático de issue no `gitpr`

Conteúdo:

| Arquivo | Para quê |
|---|---|
| `00-SPEC.md` | Especificação principal, com tarefas T0 a T9, para o Claude Code executar. |
| `PROMPT-CLAUDE-CODE.md` | Prompt pronto para colar no Claude Code. |
| `entrevista.md` | Perguntas, respostas e premissas que sustentam a spec. |
| `glossario.md` | Termos usados nos documentos. |
| `adrs/ADR-001..007` | Decisões de arquitetura, todas com status "Aceito". |

## 1. Salvar no projeto

Na raiz do repositório do gitpr:

```bash
mkdir -p docs/specs
unzip /caminho/para/issue-autoclose.zip -d docs/specs/
# resultado: docs/specs/issue-autoclose/00-SPEC.md ...
git add docs/specs/issue-autoclose
git commit -m "docs(specs): adiciona spec de fechamento automático de issue"
```

No Windows, use o botão direito > Extrair tudo e copie a pasta `issue-autoclose` para `docs\specs\`.
Se o projeto usa outra pasta de documentação, ajuste o caminho e atualize a primeira linha de `PROMPT-CLAUDE-CODE.md`.

## 2. Executar a SPEC no Claude Code

1. Abra o Claude Code na raiz do repositório do gitpr, em uma branch nova (`feat/issue-autoclose`).
2. Abra `PROMPT-CLAUDE-CODE.md`, copie o conteúdo e cole na sessão.
3. O Claude Code começa pela tarefa **T0**, que é só investigação e não altera código. Ele entrega um relatório com o código real encontrado. Leia e responda às pendências antes de liberar a T1.
4. Libere uma tarefa por vez (T1, T2, ...). Cada tarefa termina com testes passando e um commit próprio.
5. Ao final da T9, rode a suíte completa e faça o teste manual descrito em `00-SPEC.md` (seção 12).
6. Se algo divergir do código real, o Claude Code deve parar e perguntar. Ajuste o ADR correspondente antes de continuar.
