# Documentação Técnica: Geração de Mensagens de Commit com IA (--commit)

O comando `--commit` (`-c`) do GitPR gera automaticamente mensagens de commit no formato **Conventional Commits** usando inteligência artificial para analisar as suas alterações locais e disponibiliza um fluxo TUI interativo completo para selecionar ficheiros, rever a mensagem e executar o commit.

---

## 1. Fluxo Interativo de Commit

```bash
gitpr -c
```

Ao executar num terminal interativo, o GitPR guia o utilizador por um fluxo de 4 etapas:

1. **Seletor de Stage ("Ficheiros fora do stage")**:
   - Se existirem ficheiros unstaged ou untracked, o GitPR abre o modal `StageFilesScreen` com caixas de seleção.
   - Pode selecionar exatamente quais os ficheiros que deseja adicionar ao stage (`git add`).
   - Utilize **"Selecionar Tudo"**, **"Desmarcar Tudo"**, **"Stage Selected"** (Adicionar Selecionados), **"Skip Staging"** (Ignorar Stage) ou **"Cancelar"**.
   - Se todas as alterações já estiverem no stage, este ecrã é automaticamente ignorado.

2. **Geração da Mensagem com IA**:
   - Analisa o diff do stage (`git diff --cached`) aplicando as exclusões inteligentes (`SMART_EXCLUDES`).
   - Gera a mensagem no padrão Conventional Commits em segundo plano enquanto apresenta um modal animado de progresso (`CommitProgressScreen`).

3. **Revisão e Edição da Mensagem**:
   - Apresenta a mensagem gerada no modal `CommitMessageScreen`.
   - Pode rever e editar o texto diretamente antes de confirmar.
   - Clique em **"Confirmar"** para avançar ou **"Cancelar"** para cancelar sem efetuar o commit.

4. **Execução Animada do Commit**:
   - Ao confirmar, apresenta o modal `CommitProgressScreen` com a barra deslizante em degradê animada.
   - Executa o commit (`git commit -m "..."`) incluindo a assinatura de coautoria.
   - Apresenta os registos em tempo real e o hash do commit gerado, com o botão **"Fechar"** para terminar.

---

## 2. Formato Conventional Commits

A IA é instruída a gerar mensagens no padrão:

```
tipo: descricao curta

Corpo opcional com detalhes adicionais
```

**Tipos utilizados:** `feat`, `fix`, `refactor`, `test`, `chore`, `docs`

---

## 3. Integração com Git Hooks (Não-Interativo)

O `--commit` é usado internamente pelo hook `prepare-commit-msg`. Quando instalado via `gitpr -ih`, o hook executa:

```bash
gitpr --commit --hook <caminho-do-ficheiro-temporario>
```

A flag `--hook` mantém a execução estritamente não-interativa: nenhum ecrã TUI ou modal é aberto, e a mensagem sugerida é injetada diretamente no editor do Git.

---

## 4. Configuração de Staging e Automação

Pode configurar o comportamento de staging através de variáveis de ambiente em `~/.gitpr/.env`:

- `GITPR_AUTO_STAGE=true`: Adiciona automaticamente todos os ficheiros unstaged ao stage sem abrir o seletor.
- `GITPR_SKIP_UNSTAGED_CHECK=true`: Ignora a verificação de ficheiros fora do stage.
- `--no-unstaged-check`: Flag de linha de comandos para ignorar a verificação de ficheiros fora do stage numa execução pontual.

---

## 5. Personalização via Skill

O comportamento da IA pode ser personalizado através do ficheiro `.gitpr.commit.md` em `.gitpr/skill/`:

```bash
gitpr -s          # Descarrega o template .gitpr.commit.md
# Edite o ficheiro conforme as convenções da sua equipa
gitpr -c          # A IA usará as suas regras personalizadas
```

---

## 6. Seleção de Fornecedor de IA

```bash
gitpr -c -p gemini       # Força Google Gemini
gitpr -c -p deepseek     # Força DeepSeek
gitpr -c -p ollama       # Força Ollama local
```

---

## 7. Cache de Respostas

O GitPR gera um hash MD5 do seu diff do stage + instruções. Se executar `gitpr -c` novamente **sem alterar o código em stage**, a resposta é devolvida instantaneamente a partir do cache local, poupando quotas da API.

---

## 8. Assinatura de Coautoria

Todas as mensagens de commit geradas pelo GitPR incluem automaticamente o trailer de coautoria:

```text
Co-Authored-By: Gitpr-cli <gitpr@natanfiuza.dev.br>
```

O trailer é anexado programaticamente (nunca pela IA) em todos os fluxos: TUI interativa de commit, hook `prepare-commit-msg`, auto-commit na publicação de PR e a ferramenta MCP `generate_commit_message`. É separado da mensagem por linhas em branco extras para não aparecer à primeira vista nas prévias colapsadas de commits do GitHub, e nunca é duplicado quando a mensagem já o contém.

> **Nota:** Consulte também a [documentação principal (README.md)](../README.md) para uma visão geral de todas as funcionalidades.
