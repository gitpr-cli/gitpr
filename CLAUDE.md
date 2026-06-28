# CLAUDE.md - GitPR CLI

## Sobre o projeto

**GitPR** é uma CLI em Python para automação de Pull Requests, commits, code review e criação de issues usando IA (Google Gemini e DeepSeek). Distribuído via PyPI (`pip install gitpr-cli`) e como executável standalone (PyInstaller).

- **Autor:** Natan Fiuza (contato@natanfiuza.dev.br)
- **Versão atual:** 0.0.14
- **Python:** >= 3.10
- **Branch principal:** `main`
- **Branch de desenvolvimento:** `develop_natan`
- **Licença:** LGPL-2.1

## Arquitetura

```
src/
├── main.py           # CLI (Click) — roteamento de comandos e flags
├── core.py           # Orquestração — git ops, prompts IA, cache, skills
├── config.py         # Configuração, .env, chaves de API, modelos
├── security.py       # Criptografia Fernet (chaves de API em repouso)
├── cache.py          # Cache local de respostas da IA (MD5)
├── ai_providers.py   # Camada unificada de chamada IA (Gemini + DeepSeek)
├── linter_engine.py  # Análise estática com regex (regras YAML)
├── blame_engine.py   # Arqueologia de código com git blame + IA
├── issue_engine.py   # Criação de rascunho de issues via IA
├── tui_issue.py      # Validação de token GitHub e entrada da TUI
├── ui/               # Sub-package: componentes da TUI (Textual)
│   ├── help_screen.py    # Modal de ajuda (F4) — atalhos e instruções
│   └── issue_app.py      # App principal da TUI — edição e envio de issues
└── updater.py        # Verificação de versão (PyPI + GitHub) e hot-swap

scripts/
├── pre-commit-template.sh          # Hook pre-commit para lint local
└── prepare-commit-msg-template.sh  # Hook prepare-commit-msg para gerar mensagens

templates/            # Templates remotos servidos do GitHub (--skill)
├── gitpr.blame.md
├── gitpr.commit.md
├── gitpr.filereview.md
├── gitpr.issue.md
├── gitpr.linter.yml
├── gitpr.pr.md
└── gitpr.review.md

tests/
└── test_core.py      # Testes unitários (unittest + mock)

docs/
├── ARCHITECTURE.md
├── caveman-commit.md
├── git-hooks-locais.md
├── github-ci-linter.md
├── github-issue-prompt.md
├── github-pat-integration.md       # Segurança do token GitHub (PAT + Fernet)
├── issue-tui-help.md               # Guia da interface TUI de issues
├── guia-regex-gitpr.md
├── linter-regras-customizadas.md
├── otimizacao-de-tokens.md
├── testar_sem_usar_pypi.md
├── untracked-files.md
├── claude-code/reports/            # Relatórios de tarefas do Claude Code
├── plans/                          # Planos de desenvolvimento
└── assets/                         # logo.png, logo.psd, progit.pdf
```

**Padrões de projeto:** Facade/Mediator (`core.py`), Strategy (`ai_providers.py`), separação modular por responsabilidade. O sub-package `src/ui/` isola os componentes visuais (Textual) da lógica de negócio.

### Fluxo de comandos principais

| Flag                     | Ação                  | Pipeline                                                                |
|--------------------------|-----------------------|-------------------------------------------------------------------------|
| *(padrão)*               | PR description        | `git fetch` → diff contra `origin/main` → IA → `.md`                   |
| `-c` / `--commit`        | Commit message        | `git diff HEAD` → IA → console (Conventional Commits)                   |
| `-r` / `--review`        | Code review local     | `git diff HEAD` → IA + Linter → `.txt`                                  |
| `-f` / `--fullreview`    | Code review completo  | `git fetch` → diff contra base remota → IA + Linter → `.txt`            |
| `-i` / `--input`         | Auditoria de arquivo  | Arquivo inteiro → IA (usa `.gitpr.filereview.md`)                       |
| `-l` / `--linter`        | Linter estático       | `git diff` → regex YAML → console (sem IA)                              |
| `-is` / `--issue`        | Issue via TUI         | `git diff` → IA (rascunho) → TUI Textual → salvar .md ou POST GitHub   |
| `-b` / `--blame`         | Arqueologia           | `git blame` → IA classifica commits → timeline + sumário                |
| `-s` / `--skill`         | Baixar templates      | Download dos `.gitpr.*.md` do GitHub (não sobrescreve)                  |
| `-ih` / `--installhooks` | Instalar hooks        | Download + instala hooks no `.git/hooks/`                               |
| `-u` / `--update`        | Atualizar             | Verifica PyPI/GitHub Releases → hot-swap do binário                     |
| `--provider`             | Forçar IA             | `gemini` ou `deepseek` (ignora config padrão)                           |

## Stack

| Componente       | Tecnologia                            |
|------------------|---------------------------------------|
| CLI framework    | Click >= 8.0.0                        |
| TUI (issues)     | Textual (ModalScreen, App, bindings)  |
| IA (Gemini)      | `google-genai` SDK                    |
| IA (DeepSeek)    | `openai` SDK (API compatível)         |
| GitHub API       | `requests` (REST, PAT via header)     |
| Config/Build     | `pyproject.toml` + setuptools >= 61   |
| Criptografia     | `cryptography.fernet` (simétrica)     |
| Linter           | `pyyaml` (regras) + regex             |
| Testes           | `pytest` + `unittest.mock`            |
| Empacotamento    | PyInstaller (`run.py` como entry)     |
| Ambiente virtual | Pipenv (Pipfile)                      |

## Comandos

```bash
# Instalar dependências (pipenv)
pipenv install --dev

# Instalar dependências (pip)
pip install -e .

# Executar (modo dev)
pipenv run python src/main.py
# ou
python -m src.main

# Rodar testes
pipenv run pytest -v
# ou
python -m pytest tests/ -v
python -m unittest discover tests -v

# Build com PyInstaller
pipenv run pyinstaller --noconfirm --onefile --icon=icon.ico --name gitpr run.py

# Publicar no PyPI
pipenv run python -m build
pipenv run twine upload dist/*
```

## Preferências de código

### Estilo Python
- **Encoding:** UTF-8 com `errors='replace'` em toda leitura de arquivo — NUNCA usar `errors='strict'` ou `errors='ignore'` puro
- **Docstrings:** Comentários em português, formato livre (não Google/NumPy estrito)
- **Tipagem:** Type hints são bem-vindos mas não obrigatórios — usar onde melhora a clareza
- **Organização:** Cada módulo tem uma responsabilidade única e clara. Componentes TUI isolados em `src/ui/`
- **Naming:** snake_case para funções/variáveis, UPPER_CASE para constantes, PascalCase para classes Textual
- **CLI:** Usar Click com decorators; flags curtas (`-c`, `-r`, `-f`, `-is`) com equivalentes longos
- **Imports:** stdlib primeiro, depois dependências externas, depois módulos internos (`from src.*`)
- **Sub-packages:** Criar `__init__.py` apenas se necessário; `src/ui/` atualmente não possui (importação direta)

### Respostas de IA
- Todas as chamadas de IA devem retornar JSON estruturado
- Temperatura 0.0 para output determinístico
- Retry automático (3 tentativas, 2s de intervalo)
- Cache MD5 obrigatório para evitar chamadas redundantes

### Mensagens e UI
- Todo texto exibido ao usuário em **português (Brasil)**
- Banner ASCII no início (suprimido em modo `--quiet` ou `--hook`)
- Usar `click.style()` ou `click.secho()` para cores no terminal
- Cores padronizadas: verde/cyan = sucesso/info, amarelo = warning, vermelho = erro
- TUI (Textual): usar `$surface`, `$accent`, `$background` do tema; footer com bindings visíveis

## Commits

### Estilo de mensagem
- **Idioma:** Português (Brasil)
- **Formato:** Conventional Commits — `tipo: descricao curta`
- **Tipos usados:** `feat`, `fix`, `refactor`, `test`, `chore`, `docs`
- **Descrições:** curtas, imperativas, sem ponto final
- **Exemplos:**
  - `feat: adiciona modulo de arqueologia de codigo com git blame`
  - `refactor: extrai componentes da TUI para sub-package src/ui/`
  - `fix: corrige encoding em ambientes com caracteres nao-UTF8`

### Regras de commit
- NÃO fazer amend em commits já pushados
- NÃO pular hooks (`--no-verify`, `--no-gpg-sign`)
- Commits devem ser atômicos — uma mudança lógica por commit
- Mensagens em português, sem acentos especiais (ASCII-only quando prático)
- Co-autoria em projetos colaborativos: `Co-Authored-By: Claude <noreply@anthropic.com>`

## Regras de tarefa (Task Workflow)

### Ao iniciar uma tarefa
1. **Ler o contexto:** Verificar `CLAUDE.md`, arquivos relevantes, diff atual
2. **Planejar antes de codar:** Para features não-triviais, usar plan mode ou apresentar abordagem antes de implementar
3. **Verificar o estado do git:** Branch correta, nada staged acidentalmente
4. **Verificar dependências:** `pipenv install --dev` se novos pacotes forem adicionados ao Pipfile

### Durante a tarefa
5. **Seguir o estilo existente:** Código novo deve parecer que sempre esteve lá
6. **Não quebrar a CLI:** Testar fluxos principais após alterações (`gitpr`, `gitpr -c`, `gitpr -r`)
7. **Manter cache em mente:** Mudanças em prompts devem considerar impacto no cache MD5
8. **Encoding sempre com `errors='replace'`:** Regra absoluta para qualquer `open()` ou `subprocess`
9. **Novas dependências:** Adicionar ao `pyproject.toml` (dependencies) e ao `Pipfile`

### Ao finalizar uma tarefa — RELATÓRIO OBRIGATÓRIO
10. **Gerar relatório de conclusão** com o seguinte formato:

```markdown
## Relatório de Conclusão — [Título da Tarefa]

### O que foi feito
- [Lista objetiva das alterações realizadas]
- [Arquivos modificados com paths relativos]

### Arquivos alterados
| Arquivo | Tipo de mudança | Descrição |
|---------|----------------|-----------|
| src/... | feat/fix/refactor | O que mudou |

### Impacto
- **Funcionalidade:** [O que mudou no comportamento]
- **Performance:** [Impacto se relevante]
- **Compatibilidade:** [Quebras de API, migrações necessárias]

### Próximos passos (se aplicável)
- [Tarefas pendentes ou sugestões de melhoria]
```

Este relatório é **obrigatório** ao final de toda tarefa de implementação — não apenas para o usuário, mas como documentação histórica do desenvolvimento.
Ele deve ficar em `docs/claude-code/reports/{branch}/{dataatual}_{taskname}.md`, onde `{dataatual}` é a data atual (formato `YYYY-MM-DD`), `{branch}` é a branch atual, e `{taskname}` é uma descrição curta da tarefa (apenas letras minúsculas, números e underscores, sem espaços ou caracteres especiais). Criar as pastas `docs/claude-code/reports/` caso não existam.

## Notas específicas do projeto

### Encoding
- Todo `subprocess.run()` que captura saída do git deve usar `encoding='utf-8'` com `errors='replace'`
- Arquivos de saída (PR, review, blame, issue) devem ser escritos com `encoding='utf-8'`
- O projeto lida com repositórios que podem conter caracteres não-UTF8 (legado)

### Sistema de "Skills" (Prompt Engineering)
- Arquivos locais `.gitpr.<tipo>.md` na raiz do projeto do usuário atuam como *System Instructions* da IA
- Tipos: `commit`, `pr`, `review`, `filereview`, `blame`, `issue`, `linter.yml`
- Templates remotos em `https://raw.githubusercontent.com/natanfiuza/gitpr/main/templates/`
- Comando `--skill` baixa os templates, mas **nunca sobrescreve** arquivos locais existentes
- `get_skill_context()` em `core.py` gerencia fallbacks (tenta `.gitpr.<tipo>.md`, depois legado `.gitpr.md`)

### Configuração do usuário
- Diretório global: `~/.gitpr/`
- Arquivo de config: `~/.gitpr/.env` (formato dotenv)
- Chave Fernet: `~/.gitpr/secret.key` (gerada automaticamente na primeira execução)
- Cache de respostas: `~/.gitpr/cache/prompts/<action_folder>/<md5>.json`
- Cache de update: `~/.gitpr/update_cache.json` (diário)
- Variáveis de ambiente: `DEFAULT_AI_PROVIDER`, `GEMINI_API_KEY_ENCRYPTED`, `DEEPSEEK_API_KEY_ENCRYPTED`, `GEMINI_API_MODEL`, `DEEPSEEK_API_MODEL`, `SECONDARY_GEMINI_API_MODEL`, `SECONDARY_DEEPSEEK_API_MODEL`, `OUTPUT_FILE_NAME_PR`, `OUTPUT_FILE_NAME_REVIEW`, `OUTPUT_FILE_NAME_ISSUE`, `GITHUB_TOKEN_ENCRYPTED`

### AI Providers (Arquitetura Multi-Model)
- **Gemini:** `gemini-2.5-flash` (primário/avançado) / `gemini-2.5-flash-lite` (secundário/simples)
- **DeepSeek:** `deepseek-chat` (primário e secundário — mesmo modelo)
- Ambos configurados para output JSON (`response_mime_type` no Gemini, `response_format` no DeepSeek)
- Temperatura 0.0 e top_p 0.1 para output determinístico
- Fallback: se provider configurado falhar, tentar o outro automaticamente
- Flag `--provider` força um motor específico na execução

### Linter estático local
- Regras definidas em `.gitpr.linter.yml` (YAML)
- Suporta `error` (bloqueante) e `warning` (informativo)
- Filtros: extensão de arquivo (`extensions`), `require_paths`, `ignore_paths`
- `ignore_comments: true` ignora linhas de comentário (regex de comentário por linguagem)
- No modo diff, só verifica linhas adicionadas (`+`) — focado e rápido

### Blame engine (Arqueologia de código)
- Profundidade máxima de rastreamento: 4 commits pai
- Modelo barato (secundário) para classificação de commits (`ORIGEM` vs `REFATORACAO`)
- Modelo avançado (primário) para sumário executivo final
- Output: terminal colorido (verde=origem, amarelo=refatoração) + relatório Markdown

### TUI de Issues (Textual)
- App principal: `src/ui/issue_app.py` → classe `IssueApp(App)`
- Modal de ajuda: `src/ui/help_screen.py` → classe `HelpScreen(ModalScreen)`
- Bindings: F2 (Salvar .md local), F3 (Criar issue via GitHub API), F4 (Ajuda), Esc (Sair)
- Token GitHub (PAT) validado em `src/tui_issue.py` → `validate_or_request_github_token()`
- Escopo do PAT: `repo` (gerado via URL dinâmica com parâmetros pré-preenchidos)
- Rascunho da issue gerado pela IA segue o padrão: O Que / Por Que / Onde / Como

### Auto-Updater (Hot-Swap)
- Verificação diária cacheada contra GitHub Releases (binário) ou PyPI (pip)
- `--update` força verificação e instalação imediata
- Hot-swap: renomeia `.exe` atual para `.old`, baixa novo, rollback em caso de falha
- Conexão verificada via socket `8.8.8.8:53` antes de qualquer operação de rede

## Diretrizes de Comportamento

**Tradeoff:** Estas diretrizes favorecem cautela sobre velocidade. Para tarefas triviais, use julgamento.

### 1. Pense Antes de Codar
- Declare suas suposições explicitamente. Se estiver incerto, pergunte.
- Se houver múltiplas interpretações, apresente-as — não escolha silenciosamente.
- Se algo não estiver claro, pare. Nomeie o que está confuso. Pergunte.

### 2. Simplicidade Primeiro
- Mínimo de código que resolve o problema. Nada especulativo.
- Sem features além do que foi solicitado.
- Sem abstrações para código de uso único.
- Sem "flexibilidade" ou "configurabilidade" não solicitada.
- Se você escrever 200 linhas e puder ser 50, reescreva.

### 3. Mudanças Cirúrgicas
- Toque apenas no que precisa. Limpe apenas sua própria bagunça.
- Não "melhore" código adjacente, comentários ou formatação.
- Não refatore coisas que não estão quebradas.
- Combine o estilo existente, mesmo que você faria diferente.
- Remova imports/variáveis/funções que SUAS mudanças tornaram não utilizadas.

### 4. Execução Orientada a Objetivos
- Defina critérios de sucesso. Execute em loop até verificar.
- Transforme tarefas em objetivos verificáveis:
  - "Adicionar validação" → "Escreva testes para inputs inválidos, então faça-os passar"
  - "Corrigir o bug" → "Escreva um teste que reproduz, então corrija"
- Para tarefas multi-etapa, declare um plano breve com verificações por etapa.

---
**Estas diretrizes estão funcionando se:** houver menos mudanças desnecessárias em diffs, menos reescritas por excesso de complexidade, e perguntas de esclarecimento vierem antes da implementação, não depois dos erros.
