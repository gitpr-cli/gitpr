---
name: langs-ota-stale-race
description: Correções em langs/*.json exigem bump de __lang_version__; rodar código dev com marcador novo antes do main atualizado grava arquivo velho sob a versão nova
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e57845bb-2246-4f61-b6e4-220efa86d6ad
  modified: 2026-08-19T13:55:31.988Z
---

Tradução "Abort" chegou corrigida aos arquivos do repo (e2f0fa0) mas a máquina local do usuário manteve `"Abort": "Abort"` porque o arquivo antigo foi baixado sob `LANG_VERSION` igual ao marcador — o OTA nunca mais re-downloadou. Race: rodar o código de desenvolvimento (marcador novo) enquanto o `main` remoto ainda não tem os langs atualizados grava conteúdo velho com a versão nova.

**Why:** `get_translations()` só baixa quando `LANG_VERSION != __lang_version__`; o download busca em `raw.githubusercontent.com/.../main/langs/`.

**How to apply:**
- Sempre que mudar `langs/*.json`, bumpar `__lang_version__` em `src/updater.py` **após** o merge no main (senão clientes fixam conteúdo antigo sob o marcador novo).
- Para diagnosticar em máquinas: comparar `~/.gitpr/langs/{lang}.json` com `git show origin/main:langs/{lang}.json` e o `LANG_VERSION` no `~/.gitpr/.env`.
- O bump sozinho cura máquinas existentes: na próxima execução o download substitui o arquivo local.
- Ver [[version-marker-pattern]] e [[textual-modal-callback-dead-pump]].
