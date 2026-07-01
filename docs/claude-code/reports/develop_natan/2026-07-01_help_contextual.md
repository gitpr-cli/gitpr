## Relatório de Conclusão — Help Contextual para GitPR CLI

### O que foi feito
- Implementado sistema de ajuda contextual: `gitpr -h` mostra help padrão; `gitpr -h --issue` mostra help específico da feature com link para documentação detalhada
- Criados 7 novos arquivos de documentação técnica em `docs/` para flags que não tinham documentação dedicada
- Atualizado README.md com links para todos os novos guias e seção de documentação reorganizada
- Alterado mecanismo de help de `@click.help_option` (que intercepta antes do `cli()`) para flag regular `-h`/`--help`, permitindo detetar combinações de flags
- Adicionado dicionário `HELP_MAP` (flag → título, descrição, URL da doc) e `HELP_PRIORITY` (prioridade para múltiplas flags)

### Arquivos alterados

| Arquivo | Tipo de mudança | Descrição |
|---|---|---|
| `src/main.py` | feat | Substitui `@click.help_option` por flag regular; adiciona dispatcher de help contextual (~50 linhas); adiciona `HELP_MAP` e `HELP_PRIORITY` (~120 linhas); ajusta validação do `--input` com guard `not help_flag` |
| `README.md` | docs | Adiciona descrição da flag `-h`/`--help` com ajuda contextual; atualiza seção de documentação com 10+ links para guias detalhados |
| `docs/code-review-ia.md` | docs (novo) | Guia dos modos `--review`, `--fullreview` e `--input`: uso, output, integração com linter, customização |
| `docs/commit-message-ia.md` | docs (novo) | Guia do `--commit`: Conventional Commits, integração com hooks, customização via skill |
| `docs/blame-arqueologo.md` | docs (novo) | Guia do `--blame`: formatos de sintaxe, classificação ORIGEM/REFATORACAO, integração com `--issue` |
| `docs/skill-template.md` | docs (novo) | Guia do `--skill`: templates disponíveis, customização, política de não-sobrescrita |
| `docs/auto-update.md` | docs (novo) | Guia do `--update`: hot-swap, verificação diária, pip vs binário |
| `docs/pr-descricao-padrao.md` | docs (novo) | Guia do modo padrão: fluxo fetch→diff→IA→.md, customização, cache |
| `docs/providers-ia.md` | docs (novo) | Guia do `--provider`: Gemini vs DeepSeek, configuração, modelos, fallback |

### Impacto
- **Funcionalidade:** `gitpr -h` (sozinho) mantém comportamento original; `gitpr -h --<flag>` agora mostra ajuda contextual com link para documentação detalhada no GitHub. Funciona com todas as 12 flags não-hidden.
- **Performance:** Sem impacto — o dispatcher de help é um bloco O(n) simples que só executa quando `-h` é usado.
- **Compatibilidade:** Nenhuma quebra. A flag `-h` continua funcionando como antes quando usada sozinha. A remoção do `exists=True` do `--input` é compensada por validação explícita no corpo da função com guard `not help_flag`.

### Próximos passos (se aplicável)
- Resolver o circular import pré-existente entre `src/core.py` e `src/cache.py` para restaurar a executabilidade dos testes unitários
- Considerar adicionar `-h` contextual para combinações como `gitpr -h -r -i` (review + input) mostrando a intersecção das docs
- Adicionar testes unitários para o dispatcher de help contextual
