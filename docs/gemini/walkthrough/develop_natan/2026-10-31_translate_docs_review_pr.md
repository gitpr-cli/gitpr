# Walkthrough — Tradução da Família `docs/review-pr.*.md`

Concluímos a tradução e sincronização de toda a família de documentação `docs/review-pr.*.md`, atingindo cobertura de 5 de 5 idiomas suportados pelo GitPR (EN, PT-BR, PT-PT, ES-ES, FR-FR), além de atualizar os índices dos arquivos README correspondentes.

## Alterações Realizadas

### 1. Documentações Técnicas Criadas
- `docs/review-pr.pt_pt.md`: Tradução completa em Português de Portugal com vocabulário estritamente alinhado a `langs/pt_pt.json` (*ficheiro*, *apontamentos*, *gravar*, etc.) e links apontando para `?lang=pt_pt`.
- `docs/review-pr.es_es.md`: Tradução completa em Espanhol (Espanha) alinhada a `langs/es_es.json` (*archivo*, *hallazgos*, *guardar*, etc.) e links apontando para `?lang=es`.
- `docs/review-pr.fr_fr.md`: Tradução completa em Francês alinhada a `langs/fr_fr.json` (*fichier*, *constats*, *enregistrer*, etc.) e links apontando para `?lang=fr`.

### 2. Documentações Existentes Atualizadas
- `docs/review-pr.md`: Atualizados links markdown internos para direcionarem para a documentação online em `https://gitpr.natanfiuza.dev.br/docs/...`.
- `docs/review-pr.pt_br.md`: Atualizados links markdown internos para a documentação online com `?lang=pt_br`.

### 3. Índices do README Atualizados
- `README.pt_pt.md`: Adicionado item `Revisão de Pull Request Remoto (gitpr review-pr)` apontando para `https://gitpr.natanfiuza.dev.br/docs/review-pr?lang=pt_pt`.
- `README.es_es.md`: Adicionado item `Revisión de Pull Request Remoto (gitpr review-pr)` apontando para `https://gitpr.natanfiuza.dev.br/docs/review-pr?lang=es`.
- `README.fr_fr.md`: Adicionado item `Revue de Pull Request Distante (gitpr review-pr)` apontando para `https://gitpr.natanfiuza.dev.br/docs/review-pr?lang=fr`.

---

## Verificação e Paridade
- **Paridade Estrutural:** Todos os 5 arquivos de `docs/review-pr.*.md` possuem exatamente 229 linhas, conservando todas as seções (§1 a §8), tabelas de referência, blocos de código (`bash`, `diff`, `json`, `text`, `markdown`) e rodapés de comentários.
- **Codificação:** Todos os arquivos salvos em UTF-8.
- **Links Validados:** Todos os links externos formatados segundo a convenção de parâmetros de idioma oficial do projeto.
