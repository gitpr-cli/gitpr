# Plano de Implementação — Tradução de `docs/review-pr.*.md` (Cobertura 5/5 Idiomas)

## 🎯 Objetivo
Completar a cobertura multilíngue da documentação da feature `gitpr review-pr`, que atualmente possui cobertura parcial de 2 dos 5 idiomas suportados (`review-pr.md` em inglês e `review-pr.pt_br.md` em português do Brasil). Serão criados os 3 documentos restantes (`.pt_pt.md`, `.es_es.md`, `.fr_fr.md`) e atualizados os arquivos de README correspondentes com os links canônicos para a documentação online.

---

## 🔍 Contexto e Alinhamento
- **Arquivos existentes:** `docs/review-pr.md` (EN) e `docs/review-pr.pt_br.md` (PT-BR).
- **Arquivos pendentes a criar:**
  1. `docs/review-pr.pt_pt.md` (Português de Portugal)
  2. `docs/review-pr.es_es.md` (Espanhol da Espanha)
  3. `docs/review-pr.fr_fr.md` (Francês da França)
- **Atualização de READMEs:** Inserir a entrada de `review-pr` sob a seção de Funcionalidades Principais (Core Features) nos READMEs que ainda não a continham (`README.pt_pt.md`, `README.es_es.md`, `README.fr_fr.md`).
- **Padrão de Links do Website de Documentação:**
  - EN: `https://gitpr.natanfiuza.dev.br/docs/review-pr`
  - PT-BR: `https://gitpr.natanfiuza.dev.br/docs/review-pr?lang=pt_br`
  - PT-PT: `https://gitpr.natanfiuza.dev.br/docs/review-pr?lang=pt_pt`
  - ES: `https://gitpr.natanfiuza.dev.br/docs/review-pr?lang=es`
  - FR: `https://gitpr.natanfiuza.dev.br/docs/review-pr?lang=fr`

---

## 📋 Alterações Propostas

### 1. Documentação (`docs/`)

#### [NEW] `docs/review-pr.pt_pt.md`
- Tradução fiel de `docs/review-pr.md` para Português de Portugal.
- Terminologia estritamente alinhada com `langs/pt_pt.json` e `docs/code-review-ia.pt_pt.md`:
  - "ficheiro" (não "arquivo"), "gravar" (não "salvar"), "ecrã" (não "tela"), "apontamentos" (não "achados").
  - Mensagens da tabela §4.2 e §4.3 idênticas às chaves do catálogo `langs/pt_pt.json`.
  - Links para documentos irmãos apontando para `https://gitpr.natanfiuza.dev.br/docs/...` ou referências locais correspondentes.

#### [NEW] `docs/review-pr.es_es.md`
- Tradução fiel de `docs/review-pr.md` para Espanhol da Espanha.
- Terminologia estritamente alinhada com `langs/es_es.json` e `docs/code-review-ia.es_es.md`:
  - "archivo", "guardar", "revisión", "hallazgos".
  - Mensagens da tabela §4.2 e §4.3 idênticas às chaves do catálogo `langs/es_es.json`.

#### [NEW] `docs/review-pr.fr_fr.md`
- Tradução fiel de `docs/review-pr.md` para Francês da França.
- Terminologia estritamente alinhada com `langs/fr_fr.json` e `docs/code-review-ia.fr_fr.md`:
  - "fichier", "enregistrer", "revue de code", "constats".
  - Mensagens da tabela §4.2 e §4.3 idênticas às chaves do catálogo `langs/fr_fr.json`.

---

### 2. Arquivos README (`README.*.md`)

#### [MODIFY] `README.pt_pt.md`
- Inserir na seção *Funcionalidades Principais*:
  ```markdown
  * [**Revisão de Pull Request Remoto (gitpr review-pr)**](https://gitpr.natanfiuza.dev.br/docs/review-pr?lang=pt_pt) — Como o subcomando `gitpr review-pr` revê um pull request já aberto na forge, obtendo o seu diff pela API sem fazer checkout da sua branch.
  ```

#### [MODIFY] `README.es_es.md`
- Inserir na seção *Funcionalidades Principais*:
  ```markdown
  * [**Revisión de Pull Request Remoto (gitpr review-pr)**](https://gitpr.natanfiuza.dev.br/docs/review-pr?lang=es) — Cómo el subcomando `gitpr review-pr` revisa un pull request ya abierto en la forge, obteniendo su diff por la API sin hacer checkout de su rama.
  ```

#### [MODIFY] `README.fr_fr.md`
- Inserir na seção *Funcionalidades Principais*:
  ```markdown
  * [**Revue de Pull Request Distante (gitpr review-pr)**](https://gitpr.natanfiuza.dev.br/docs/review-pr?lang=fr) — Comment la sous-commande `gitpr review-pr` examine une pull request déjà ouverte sur la forge, en récupérant son diff depuis l'API sans extraire sa branche.
  ```

---

## 🧪 Plano de Verificação

### Verificação Estrutural
- Confirmar paridade de seções (1 a 8) e subseções (1.1, 2.1 a 2.5, 3.1, 4.1 a 4.4) em todos os novos arquivos.
- Confirmar integridade de tabelas Markdown e blocos de código (`bash`, `diff`, `text`, `json`, `markdown`).
- Confirmar codificação UTF-8 sem BOM em todos os arquivos criados e editados.

### Verificação de Links
- Confirmar que as URLs formatadas em cada idioma direcionam para a documentação correta (`?lang=pt_pt`, `?lang=es`, `?lang=fr`).
