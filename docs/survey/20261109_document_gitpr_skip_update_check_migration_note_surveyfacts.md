# Survey and Facts — Documentação da Mudança de Semântica de GITPR_SKIP_UPDATE_CHECK

**Data:** 2026-11-09  
**Branch:** develop_natan  
**Task:** document_gitpr_skip_update_check_migration_note  

---

## 1. Contexto e Problema

GitPR é distribuído exclusivamente via PyPI e possui um portão obrigatório de atualização (*update gate*). Ao rodar a partir do código fonte (checkout local editável via `pip install -e .`), a versão reportada é lida da working tree local (`src/updater.py::__version__`). Se uma versão mais recente já tiver sido publicada no PyPI, o portão bloqueia a execução.

Para permitir desenvolvimento local e automações de teste offline, o GitPR possui uma chave de escape via variável de ambiente: `GITPR_SKIP_UPDATE_CHECK`.

### Histórico da Mudança Semântica (v1.4.3)
- **Antes da v1.4.3**: O código verificava a presença/truthiness simples de string da variável de ambiente no Python/shell (ex.: `bool(os.environ.get("GITPR_SKIP_UPDATE_CHECK"))`). Qualquer valor não vazio — inclusive strings como `"false"`, `"0"`, `"off"`, `"no"` — era avaliado como verdadeiro e silenciava a verificação de versão.
- **A partir da v1.4.3**: Foi implementado um parser booleano estrito em `src/updater.py`:
  ```python
  SKIP_UPDATE_CHECK_ENV = "GITPR_SKIP_UPDATE_CHECK"
  _SKIP_TRUTHY_VALUES = ("1", "true", "yes", "on", "y")

  def is_update_check_disabled():
      value = os.environ.get(SKIP_UPDATE_CHECK_ENV, "")
      return value.strip().lower() in _SKIP_TRUTHY_VALUES
  ```
- **A Armadilha (The Breaking Change)**:
  Automações, pipelines de CI ou scripts de desenvolvedores que configuravam `GITPR_SKIP_UPDATE_CHECK=false` (ou `=0`) esperando desligar o aviso / silenciar a checagem com base no comportamento antigo agora têm o valor avaliado como falso. Consequentemente, a verificação de atualização **permanece ativa** e pode bloquear o comando com código de saída diferente de zero.
- **Estado Atual da Documentação**:
  - `docs/tutorial/install-from-source.md` (e suas 4 traduções) lista os valores verdadeiros/falsos aceitos, mas não continha uma nota de migração destacando o impacto para automações legadas que usavam `=false`.
  - `docs/auto-update.md` (e suas 4 traduções) nem sequer mencionava o nome da variável de ambiente explicitamente, apenas apontando um link para o tutorial.
  - `CONTEXT.md` ainda não continha o termo canônico formalizado no modelo de domínio para o switch.

---

## 2. Decisões do Grill (Rodada 1)

1. **Localização Canônica da Nota de Migração**:
   - Atualizar tanto a documentação técnica central (`docs/auto-update.*.md`) quanto o tutorial prático (`docs/tutorial/install-from-source.*.md`).
2. **Paridade de Internacionalização**:
   - Manter paridade total em todos os 5 idiomas suportados pelo GitPR: Inglês (`.md`), Português do Brasil (`.pt_br.md`), Português de Portugal (`.pt_pt.md`), Espanhol (`.es_es.md`) e Francês (`.fr_fr.md`). Total de 10 arquivos de documentação sincronizados.
3. **Glossário e Modelo de Domínio (`CONTEXT.md`)**:
   - Registrar o termo **Update check switch** (`GITPR_SKIP_UPDATE_CHECK`) com sua definição estrita e termos a evitar.
4. **Estrutura da Nota de Migração**:
   - Utilizar alerta GitHub `> [!WARNING]` com descrição explícita do comportamento anterior (< 1.4.3), da quebra de expectativa em `=false`, e da remediação mandatória (`=1` ou `=true`).

---

## 3. Matriz de Arquivos Afetados

| Arquivo | Mudança | Idioma / Escopo |
|---|---|---|
| `CONTEXT.md` | Inclusão do termo `Update check switch` | Modelo de Domínio |
| `docs/auto-update.md` | Nova subseção com Nota de Migração | Inglês (Canônico) |
| `docs/auto-update.pt_br.md` | Nova subseção com Nota de Migração | Português (Brasil) |
| `docs/auto-update.pt_pt.md` | Nova subseção com Nota de Migração | Português (Portugal) |
| `docs/auto-update.es_es.md` | Nova subseção com Nota de Migração | Espanhol |
| `docs/auto-update.fr_fr.md` | Nova subseção com Nota de Migração | Francês |
| `docs/tutorial/install-from-source.md` | Callout de Nota de Migração na Seção 5 | Inglês (Canônico) |
| `docs/tutorial/install-from-source.pt_br.md` | Callout de Nota de Migração na Seção 5 | Português (Brasil) |
| `docs/tutorial/install-from-source.pt_pt.md` | Callout de Nota de Migração na Seção 5 | Português (Portugal) |
| `docs/tutorial/install-from-source.es_es.md` | Callout de Nota de Migração na Seção 5 | Espanhol |
| `docs/tutorial/install-from-source.fr_fr.md` | Callout de Nota de Migração na Seção 5 | Francês |
