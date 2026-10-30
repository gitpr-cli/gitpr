# Documentação Técnica: Geração de Mensagens de Commit com IA (--commit)

O comando `--commit` (`-c`) do GitPR gera automaticamente mensagens de commit no formato **Conventional Commits** usando inteligência artificial para analisar as suas alterações locais e oferece um fluxo TUI interativo completo para selecionar arquivos, revisar a mensagem e executar o commit.

---

## 1. Fluxo Interativo de Commit

```bash
gitpr -c
```

Ao executar em um terminal interativo, o GitPR guia você por um fluxo de 4 etapas:

1. **Seletor de Stage ("Arquivos fora do stage")**:
   - Se houver arquivos unstaged ou untracked, o GitPR abre o modal `StageFilesScreen` com caixas de seleção (checkboxes).
   - Você pode selecionar exatamente quais arquivos deseja adicionar ao stage (`git add`).
   - Use **"Selecionar Tudo"**, **"Desmarcar Tudo"**, **"Stage Selected"** (Adicionar Selecionados), **"Skip Staging"** (Pular Stage) ou **"Cancelar"**.
   - Se todas as alterações já estiverem no stage, esta tela é automaticamente ignorada.

2. **Geração da Mensagem com IA**:
   - Analisa o diff do stage (`git diff --cached`) aplicando as exclusões inteligentes (`SMART_EXCLUDES`).
   - Gera a mensagem no padrão Conventional Commits em segundo plano enquanto exibe um modal animado de progresso (`CommitProgressScreen`).

3. **Revisão e Edição da Mensagem**:
   - Exibe a mensagem gerada no modal `CommitMessageScreen`.
   - Você pode revisar e editar o texto diretamente antes de confirmar.
   - Clique em **"Confirmar"** para avançar ou **"Cancelar"** para abortar sem comitar.

4. **Execução Animada do Commit**:
   - Ao confirmar, exibe o modal `CommitProgressScreen` com a barra deslizante em degradê animada.
   - Executa o commit (`git commit -m "..."`) incluindo a assinatura de coautoria.
   - Apresenta os logs em tempo real e o hash do commit gerado, com o botão **"Fechar"** para encerrar.

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
gitpr --commit --hook <caminho-do-arquivo-temporario>
```

A flag `--hook` mantém a execução estritamente não-interativa: nenhuma tela TUI ou modal é aberta, e a mensagem sugerida é injetada diretamente no editor do Git.

---

## 4. Configuração de Staging e Automação

Você pode configurar o comportamento de staging através de variáveis de ambiente em `~/.gitpr/.env`:

- `GITPR_AUTO_STAGE=true`: Adiciona automaticamente todos os arquivos unstaged ao stage sem abrir o seletor.
- `GITPR_SKIP_UNSTAGED_CHECK=true`: Ignora a verificação de arquivos fora do stage.
- `--no-unstaged-check`: Flag de linha de comando para ignorar a verificação de arquivos fora do stage em uma execução pontual.

---

## 5. Customização via Skill

O comportamento da IA pode ser customizado através do arquivo `.gitpr.commit.md` em `.gitpr/skill/`:

```bash
gitpr -s          # Baixa o template .gitpr.commit.md
# Edite o arquivo conforme as convenções da sua equipe
gitpr -c          # A IA usará as suas regras customizadas
```

---

## 6. Seleção de Provedor de IA

```bash
gitpr -c -p gemini       # Força Google Gemini
gitpr -c -p deepseek     # Força DeepSeek
gitpr -c -p ollama       # Força Ollama local
```

---

## 7. Cache de Respostas

O GitPR gera um hash MD5 do seu diff do stage + instruções. Se executar `gitpr -c` novamente **sem alterar o código em stage**, a resposta é devolvida instantaneamente a partir do cache local, poupando cotas da API.

---

## 8. Assinatura de Coautoria

Toda mensagem de commit gerada pelo GitPR carrega automaticamente o trailer de coautoria:

```text
Co-Authored-By: Gitpr-cli <gitpr@natanfiuza.dev.br>
```

O trailer é anexado programaticamente (nunca pela IA) em todos os fluxos: TUI interativa de commit, hook `prepare-commit-msg`, auto-commit na publicação de PR e a ferramenta MCP `generate_commit_message`. Ele é separado da mensagem por linhas em branco extras para não aparecer de primeira vista nas prévias colapsadas de commits do GitHub, e nunca é duplicado quando a mensagem já o contém.

> **Nota:** Consulte também a [documentação principal (README.md)](../README.md) para visão geral de todas as funcionalidades.
