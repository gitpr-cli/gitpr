## Contexto

Adicionar ao config TUI do GitPR uma nova seção "Skills" para editar as skills do próprio GitPR.

## Definições

- Skills são os arquivos armazenados em `./.gitpr/skill`.
- O conjunto de skills é fixo e definido pelo método `get_skill_context` em `core.py`.
- Cada skill corresponde a um arquivo individual dentro do diretório (ex.: Pull Request, Issue, etc.).

## Regras de implementação

- Criar uma nova seção "Skills" no config TUI.
- Consultar `get_skill_context` em `core.py` para determinar quais skills são suportadas.
- Listar no config apenas as skills suportadas, uma entrada por skill.
- Não exibir para edição arquivos presentes em `./.gitpr/skill` que não estejam entre as skills suportadas.
- Se uma skill suportada não tiver arquivo correspondente em `./.gitpr/skill`, tratar esse caso de forma consistente com o restante do TUI (ex.: indicar ausência ou permitir criação).
- Cada entrada da lista deve levar a uma tela/painel de edição do conteúdo do arquivo da skill correspondente.
- Persistir alterações diretamente no arquivo da skill em `./.gitpr/skill`.
- Seguir o padrão visual e de navegação já usado pelas demais seções do config TUI.
- Validar que o arquivo da skill existe e é gravável antes de habilitar a edição.
- Tratar e exibir erros de leitura/escrita de forma consistente com o restante do TUI.

---

## Status da execução — 2026-09-13

**Concluído.** Relatório: `docs/claude-code/reports/develop_natan/2026-09-13_config_tui_skills_section.md`.

Categoria **Skills** na tela, entre **Diff Filters** e **Advanced**. O registro `SKILL_FILES_BY_TYPE` em `src/config.py` é a única fonte: `get_skill_context()` passou a lê-lo (mesma semântica, inclusive o fallback para `review`), então a tela lista, por construção, o que os comandos carregam.

| Regra do plano | Como foi cumprida |
|---|---|
| Criar uma seção "Skills" | Categoria `skills`, posição 10 (imediatamente antes de `advanced`), `doc="skill-template.md"` |
| Consultar `get_skill_context` para saber as suportadas | O mapa foi extraído de `get_skill_context()` para `src/config.py` e o carregador passou a ler dele; `tests/test_skill_context.py` prova arquivo por arquivo |
| Listar só as suportadas, uma entrada por skill | Sete entradas, na ordem do registro; `.gitpr.linter.yml` (presente na pasta, não é skill) **não** aparece |
| Não exibir arquivos não suportados | `test_only_the_supported_skills_are_listed` semeia o linter e um `.gitpr.custom.md` a mais |
| Skill sem arquivo tratada de forma consistente | Entrada marcada `not in this project`, editor desabilitado com a explicação ("uma caixa vazia leria como 'esta skill está vazia', que é o oposto do verdadeiro") e botão 📥 que baixa o template publicado, como os botões das demais seções |
| Cada entrada leva a um painel de edição | Painel inline master-detail (`#skills_list` + `#skill_editor`), sem modal novo |
| Persistir direto no arquivo | `write_skill_file()` grava em `.gitpr/skill/` preservando o fim de linha que o arquivo já tinha, em temp file + `os.replace` |
| Padrão visual e de navegação das demais seções | Mesma marca de pendência no `F2`, mesmo `ConfirmDiscardScreen` no `Esc`, mesma doutrina de `_quiet_output()` e de veredito lido do arquivo em vez do retorno da função |
| Validar que existe e é gravável **antes** de habilitar a edição | `skill_file_status()` → `editable`/`missing`/`readonly`/`unreadable`; a gravação continua dentro de `try/except` porque só ela é a prova |
| Erros de leitura/escrita consistentes | Falha de gravação notifica pelo nome do arquivo e **mantém a edição pendente**; a falha de um arquivo não aborta os outros |

| Verificação | Resultado |
|---|---|
| Suíte completa | **1029 passed, 6 failed, 2 skipped** — as 6 são exatamente as pré-existentes. Baseline 998 → **+31 testes** |
| i18n | 20 passed; 15 chaves novas em cada um dos 6 arquivos (944 → 959), inserção cirúrgica |
| Sonda no repo real | 7 entradas na ordem do registro, `filereview` ausente e não editável, `.gitpr.linter.yml` fora da lista, linha `SKILLS_FOLDER` com o caminho resolvido, link `?lang=pt_br` |
| `F2` real sobre cópias dos arquivos do repo | Só `.gitpr.pr.md` mudou, uma linha adicionada, CRLF preservado (21 → 22) |
| Download real (`raw.githubusercontent.com`) | `✔ .gitpr.filereview.md downloaded.`, a marca de ausente some e o editor habilita |
| Passada visual com a janela real | **Não feita** — todas as verificações são headless |

**Desvios deliberados do plano:** o download real correu **num projeto de rascunho**, não na árvore do repositório (o plano previa criar `.gitpr/skill/.gitpr.filereview.md` aqui) — o caminho de código é o mesmo, porque a pasta é resolvida a partir do diretório de trabalho, e o repositório ficou intocado; o `F2` real correu sobre **cópias byte a byte** dos arquivos, com o `ENV_FILE` redirecionado, para não gravar nos arquivos versionados nem no `~/.gitpr/.env` do usuário.

**Fora de escopo, anotado:** `.gitpr.linter.yml` não é oferecido (não é de `get_skill_context`); as listas duplicadas em `src/mcp_server.py` e no dicionário de download de `generate_skill_template()` continuam lá, com um teste novo impedindo a divergência; `docs/config-tui.es_es.md:117` tem um `?lang=pt_br` pré-existente.
