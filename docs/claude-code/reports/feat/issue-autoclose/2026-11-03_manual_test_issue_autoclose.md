# Roteiro — Teste manual §12 da feature `issue-autoclose`

- **Data:** 2026-11-03
- **Branch:** `feat/issue-autoclose`
- **SPEC:** `docs/specs/issue-autoclose/00-SPEC.md` §12 (critério de aceite §8)
- **Quem executa:** o usuário, em um repositório de teste no GitHub
- **Quem registra:** as evidências voltam para o relatório final em
  `docs/claude-code/reports/feat/issue-autoclose/2026-11-03_final_issue_autoclose_closure.md`

## Antes de começar — leia

1. **Use `python run.py`, nunca `gitpr`.** O executável do PATH é a release
   antiga do PyPI e não tem a feature. Todos os comandos abaixo partem da raiz
   deste repositório, com o ambiente do projeto ativo (`pipenv run python run.py`
   ou `python run.py`).
2. **Utilize um repositório de teste no GitHub**, clonado e com permissão de
   escrita. O fluxo cria issues e pull requests reais, e o teste remove o
   registro local — não há como fazê-lo sem tocar a forge.
3. **Token.** `~/.gitpr/.env` precisa de `GITPR_SCM_TOKEN` (ou
   `GITPR_SCM_TOKEN_ENCRYPTED` configurado por `python run.py --init`). O fluxo
   lê o provider do remoto `origin`.
4. **A feature precisa estar ativa.** `GITPR_ISSUE_AUTOCLOSE` não pode estar
   em `false`. Verifique com:

   ```bash
   python run.py --status
   ```

   (a saída lista a configuração local; `GITPR_ISSUE_AUTOCLOSE` e
   `GITPR_ISSUE_AUTOCLOSE_TIMEOUT` pertencem à categoria **Issue**).
5. **Estado inicial limpo:** `git status` sem `.gitpr/conf/github.yml` e sem
   `close #` pendente no `.gitignore` de execuções anteriores. Se o registro
   sobrou de um teste antigo, remova-o (`rm .gitpr/conf/github.yml`).
6. **Deixe um diff publicável na branch.** A feature só aparece no fluxo do PR
   quando há código novo; um repositório de teste sem diff para a branch-base
   para o fluxo com "nenhum código novo".

## Evidência de cada passo

Cole de volta, no chat, os blocos indicados em **Evidência**. Sem eles o passo
não pode ser registrado como aprovado no relatório final.

---

## Passo 1 — `gitpr -is` grava o registro e o `.gitignore`

**Comando**

```bash
python run.py -is
```

Na TUI: revise o rascunho gerado pela IA e pressione **F3** (criar a issue no
GitHub). Anote o número da issue criada.

**Resultado esperado**

- A mensagem final da TUI mostra a URL da issue e, na primeira gravação,
  acrescenta: *"ℹ️ .gitpr/conf/github.yml adicionado ao .gitignore para o
  registro local da issue ficar fora do repositório."* (em inglês, se o idioma
  da interface for `en_us`).
- O arquivo `.gitpr/conf/github.yml` existe com esta forma:

  ```yaml
  schema_version: 1
  last_issue:
    repo: owner/repo-do-teste
    number: 123
    title: Título da issue criada
    url: https://github.com/owner/repo-do-teste/issues/123
    created_at: '2026-11-03T14:22:05'
    branch: minha-branch
  ```

- O `.gitignore` do repositório de teste ganhou **uma única** linha:
  `.gitpr/conf/github.yml` (e não `.gitpr/conf/` inteiro).
- `git status` **não** lista `.gitpr/conf/github.yml` como arquivo novo.

**Evidência**

```bash
cat .gitpr/conf/github.yml
grep -n "github.yml" .gitignore
git check-ignore -v .gitpr/conf/github.yml
git status --short
```

Cole a saída dos quatro comandos.

---

## Passo 2 — `gitpr` pergunta antes da TUI de stage e insere `close #N`

**Comando**

```bash
python run.py
```

**Resultado esperado**

1. **Antes** do aviso de arquivos não-staged (a TUI/prompt de stage), o terminal
   mostra a pergunta:

   ```text
   Issue #123 – Título da issue está aberta. Adicionar "close #123" ao final da descrição do pull request? [Y/n]:
   ```

   (em inglês, se o idioma da interface for `en_us`; o número e o título são os
   da issue do Passo 1). **A pergunta vem antes de qualquer prompt de stage de
   arquivos** — essa é a ordem exigida pelo ADR-005.
2. Responda **Sim** (`y` + Enter).
3. Siga o fluxo normal até o PR ser publicado.
4. No corpo do PR, `close #123` aparece **no fim**, imediatamente antes do badge
   do GitPR, e **uma única vez**.

**Evidência**

- O trecho do terminal com a pergunta e a resposta.
- O corpo do PR publicado, via `gh` **ou** o `.md` local gerado
  (`{branch}_{datetime}_PR_DESC.md` na raiz do repositório de teste):

  ```bash
  gh pr view <numero> --json body --jq .body | tail -8
  ```

  (ou `tail -12 <arquivo>_PR_DESC.md`).

---

## Passo 3 — o registro é removido após o PR publicado

**Comando**

```bash
ls -l .gitpr/conf/github.yml; echo "exit=$?"
```

**Resultado esperado**

- O arquivo **não existe** mais (`ls` falha, `exit=2`). O
  `IssueRegistry.clear()` o desvincula quando o PR é publicado com sucesso —
  a remoção só acontece depois de o corpo ter sido realmente enviado à forge
  (ADR-007).

**Evidência**

Cole a saída do comando acima e a mensagem de sucesso do PR do Passo 2.

---

## Passo 4 — issue fechada não pergunta e limpa o registro

**Preparação**

1. Crie uma **segunda** issue, agora pelo próprio GitHub (web ou `gh issue
   create`), e **feche-a**.
2. Grave-a como se o `-is` a tivesse criado. A forma mais simples é reexecutar
   o Passo 1 e depois fechar a issue no GitHub:

   ```bash
   python run.py -is        # F3 → cria a issue; anote o número
   gh issue close <numero>  # fecha no GitHub
   ```

**Comando**

```bash
python run.py
```

**Resultado esperado**

- **Nenhuma** pergunta sobre a issue no terminal.
- O registro `.gitpr/conf/github.yml` é removido (o motivo é
  `issue-not-open`, registrado na métrica `issue_autoclose`).
- O PR não recebe `close #N`.

**Evidência**

```bash
cat .gitpr/conf/github.yml 2>&1 || true
```

Cole a saída e o trecho do terminal mostrando o fluxo do PR **sem** pergunta.

---

## Passo 5 — `--no-close-issue` e execução sem TTY

### 5a — `--no-close-issue` mantém o registro e não pergunta

**Preparação:** repita o Passo 1 para ter um registro de uma issue **aberta**.

**Comando**

```bash
python run.py --no-close-issue
```

**Resultado esperado**

- Nenhuma pergunta sobre a issue.
- O PR não recebe `close #N`.
- O registro **continua existindo** depois do PR (a flag só pula a decisão;
  a limpeza não roda).

**Evidência**

```bash
cat .gitpr/conf/github.yml
```

### 5b — execução sem TTY não pergunta nem insere

Com o registro do Passo 5a ainda presente (issue aberta), rode em um terminal
sem entrada interativa:

```bash
cmd /c "python run.py --no-edit < nul"
```

(PowerShell: `Get-Content NUL | python run.py --no-edit`; bash:
`python run.py --no-edit < /dev/null`.)

**Resultado esperado**

- Nenhuma pergunta; `is_tty` é falso, então o motivo registrado é `no-tty`
  e o corpo do PR **não** recebe `close #N`.
- O registro **continua existindo** (nenhuma decisão foi tomada).

**Evidência**

- O trecho final do terminal.
- `cat .gitpr/conf/github.yml` (deve existir).
- O corpo do PR publicado (deve **não** conter `close #`).

> **Observação:** o `--no-edit` publica o PR direto, sem a TUI. Se o
> repositório de teste já tiver um PR aberto para a mesma branch, feche-o antes
> ou use outra branch.

---

## Limpeza após o teste

```bash
rm -f .gitpr/conf/github.yml
git checkout -- .gitignore   # se o repositório de teste não deve manter a linha
```

As issues e PRs de teste podem ser fechados no GitHub. Nenhum arquivo deste
repositório `gitpr` é alterado por este roteiro.

## Resumo para devolver

| Passo | O que comprovar | Evidência esperada |
| --- | --- | --- |
| 1 | Registro gravado e `.gitignore` com uma linha | `cat`, `grep`, `check-ignore`, `git status` |
| 2 | Pergunta antes do stage; `close #N` no fim do corpo, uma vez | terminal + corpo do PR |
| 3 | Registro removido após o PR | `ls` falhando |
| 4 | Issue fechada: sem pergunta e registro removido | terminal sem pergunta + `cat` |
| 5a | `--no-close-issue`: sem pergunta, registro mantido | terminal + `cat` |
| 5b | Sem TTY: sem pergunta, sem linha, registro mantido | terminal + `cat` + corpo do PR |

Se algo divergir do esperado, **pare e cole a saída completa** — a divergência
entra no relatório final e, se contradizer a SPEC, o plano de execução é
reavaliado antes do bump da versão.
