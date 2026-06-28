# CLAUDE.md - GitPR CLI

## Sobre o projeto

**GitPR** é uma CLI em Python para automação de Pull Requests, commits e code review usando IA (Gemini e DeepSeek). Distribuído via PyPI (`pip install gitpr-cli`) e como executável standalone (PyInstaller).

- **Autor:** Natan Fiuza (contato@natanfiuza.dev.br)
- **Versão atual:** 0.0.14
- **Python:** >= 3.10
- **Branch principal:** `main`
- **Branch de desenvolvimento:** `develop_natan`

## Arquitetura

```
src/
├── main.py           # CLI (Click) — roteamento de comandos
├── core.py           # Orquestração — git ops, prompts, cache
├── config.py         # Configuração, .env, chaves de API, modelos
├── security.py       # Criptografia Fernet (chaves de API em repouso)
├── cache.py          # Cache local de respostas da IA (MD5)
├── ai_providers.py   # Camada unificada de chamada IA (Gemini + DeepSeek)
├── linter_engine.py  # Análise estática com regex (regras YAML)
├── blame_engine.py   # Arqueologia de código com git blame + IA
├── issue_engine.py   # Criação de issues no GitHub via IA
├── tui_issue.py      # Interface TUI (Textual) para edição de issues
└── updater.py        # Verificação de versão (PyPI + GitHub) e hot-swap

scripts/
├── pre-commit-template.sh          # Hook pre-commit para lint local
└── prepare-commit-msg-template.sh  # Hook prepare-commit-msg para gerar mensagens

templates/            # Templates remotos servidos do GitHub
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
├── claude-code/      # Relatórios de tarefas gerados pelo Claude Code
│   └── reports/
├── plans/            # Planos de desenvolvimento
└── *.md              # Guias e documentação complementar
```

**Padrões de projeto:** Facade/Mediator (`core.py`), Strategy (`ai_providers.py`), separação modular por responsabilidade.

## Stack

| Componente         | Tecnologia                          |
|-------------------|-------------------------------------|
| CLI framework      | Click >= 8.0.0                      |
| TUI (issues)       | Textual (TextArea, Input, bindings) |
| IA (Gemini)        | `google-genai` SDK                  |
| IA (DeepSeek)      | `openai` SDK (API compatível)       |
| GitHub API         | `requests` (REST)                   |
| Config/Build       | `pyproject.toml` + setuptools >= 61 |
| Criptografia       | `cryptography.fernet`               |
| Linter             | `pyyaml` (regras) + regex           |
| Testes             | `unittest` + `unittest.mock`        |
| Empacotamento      | PyInstaller (run.py como entry)     |

## Comandos

```bash
# Instalar dependências
pip install -e .

# Executar (modo dev)
python -m src.main

# Rodar testes
python -m pytest tests/ -v
# ou
python -m unittest discover tests -v

# Build com PyInstaller
pyinstaller run.py --onefile --name gitpr

# Publicar no PyPI
python -m build
twine upload dist/*
```

## Preferências de código

### Estilo Python
- **Encoding:** UTF-8 com `errors='replace'` em toda leitura de arquivo — NUNCA usar `errors='strict'` ou `errors='ignore'` puro
- **Docstrings:** Comentários em português, formato livre (não Google/NumPy estrito)
- **Tipagem:** Type hints são bem-vindos mas não obrigatórios — usar onde melhora a clareza
- **Organização:** Cada módulo tem uma responsabilidade única e clara
- **Naming:** snake_case para funções/variáveis, UPPER_CASE para constantes
- **CLI:** Usar Click com decorators; flags curtas (`-c`, `-r`, `-f`) com equivalentes longos (`--commit`, `--review`, `--fullreview`)
- **Imports:** stdlib primeiro, depois dependências externas, depois módulos internos

### Respostas de IA
- Todas as chamadas de IA devem retornar JSON estruturado
- Temperatura 0.0 para output determinístico
- Retry automático (3 tentativas, 2s de intervalo)
- Cache MD5 obrigatório para evitar chamadas redundantes

### Mensagens e UI
- Todo texto exibido ao usuário em **português (Brasil)**
- Banner ASCII no início (suprimido em modo quiet/hook)
- Usar `click.style()` ou `rich` para cores no terminal
- Cores padronizadas: verde = sucesso, amarelo = warning, vermelho = erro

## Commits

### Estilo de mensagem
- **Idioma:** Português (Brasil)
- **Formato:** Conventional Commits — `tipo: descricao curta`
- **Tipos usados:** `feat`, `fix`, `refactor`, `test`, `chore`, `docs`
- **Descrições:** curtas, imperativas, sem ponto final
- **Exemplos:**
  - `feat: adiciona modulo de arqueologia de codigo com git blame`
  - `refactor: remove fallback pipenv e adiciona errors='replace'`
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
2. **Planejar antes de codar:** Para features não-triviais, usar plan mode (`/plan`) ou apresentar abordagem antes de implementar
3. **Verificar o estado do git:** Branch correta, nada staged acidentalmente

### Durante a tarefa
4. **Seguir o estilo existente:** Código novo deve parecer que sempre esteve lá
5. **Não quebrar a CLI:** Testar fluxos principais após alterações
6. **Manter cache em mente:** Mudanças em prompts devem considerar impacto no cache MD5
7. **Encoding sempre com `errors='replace'`:** Regra absoluta para qualquer `open()` ou `subprocess`

### Ao finalizar uma tarefa — RELATÓRIO OBRIGATÓRIO
8. **Gerar relatório de conclusão** com o seguinte formato:

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
Ele deve ficar em `docs/claude-code/reports/{branch}/{dataatual}_{taskname}.md`,  {dataatual} deve ser a data atual, {branch} deve ser a branch atual, {taskname} deve ser uma descricao curta da tarefa, sem espaços ou caracteres especiais, apenas letras minusculas, separados por underscore. Criar pasta docs/claude-code e reports caso não exista. 

## Notas específicas do projeto

### Encoding
- Todo `subprocess.run()` que captura saída do git deve usar `encoding='utf-8'` com `errors='replace'`
- Arquivos de saída (PR, review, blame) devem ser escritos com `encoding='utf-8'`
- O projeto lida com repositórios que podem conter caracteres não-UTF8 (legado)

### Prompt templates (.gitpr.*.md)
- Arquivos locais `.gitpr.<tipo>.md` na raiz do projeto do usuário
- Servem como system instructions customizadas para a IA
- Templates remotos em `https://raw.githubusercontent.com/natanfiuza/gitpr/main/templates/`
- **Nunca sobrescrever** templates locais existentes ao baixar com `--skill`
- `get_skill_context()` em `core.py` gerencia fallbacks

### Configuração do usuário
- Diretório global: `~/.gitpr/`
- Arquivo de config: `~/.gitpr/.env`
- Chave Fernet: `~/.gitpr/secret.key`
- Cache de respostas: `~/.gitpr/cache/prompts/`
- Cache de update: `~/.gitpr/update_cache.json`

### AI Providers
- Gemini: modelo `gemini-2.5-flash` (primário) / `gemini-2.5-flash-lite` (secundário)
- DeepSeek: modelo `deepseek-chat` (primário) / `deepseek-chat` (secundário — mesmo modelo)
- Ambos configurados para output JSON e temperatura 0
- Fallback: se provider configurado falhar, tentar o outro automaticamente

### Linter customizado
- Regras definidas em `.gitpr.linter.yml` (YAML)
- Suporta `error` e `warning`
- Filtros: extensão de arquivo, `require_paths`, `ignore_paths`
- Regex com `ignore_comments` ignora linhas de comentário
- No modo diff, só verifica linhas adicionadas (`+`)

### Blame engine
- Profundidade máxima de rastreamento: 4 commits pai
- Modelo barato (secundário) para classificação de commits
- Modelo avançado (primário) para sumário executivo final
- Output: terminal colorido + relatório Markdown

## Diretrizes de Comportamento (Karpathy Skills)

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

