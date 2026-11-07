## [1.6.0] - 2026-11-07

### Resumo
Esta versão traz melhorias na gestão de configurações e automação de issues, incluindo configurações de gerenciamento de código-fonte por repositório e plataforma, além de suporte ao autofechamento de issues em múltiplos forges. A experiência de commit fica mais segura em ambientes sem terminal interativo, enquanto as sugestões de revisão agora consideram arquivos com e sem histórico de autoria. Foram adicionados recursos para inicializar arquivos de configuração de projeto, novos gráficos de tendência de tokens e latência, e uma interface de configuração de exclusões inteligentes com sobreposições por projeto e centralização de padrões. Também há melhorias em ajuda e documentação, com links sensíveis ao idioma e direcionamento para a documentação de autofechamento de issues, recolhimento de trechos binários e ampliação das exclusões inteligentes. A publicação de extensões foi reforçada com metadados de marketplace e a versão foi atualizada para 1.6.0.

### ✨ Funcionalidades
- scope SCM forge settings per repository and forge ([ee012fa](https://github.com/gitpr-cli/gitpr/commit/ee012fa51c1b8b353f58ebb61dbb9a337e1538d6)) · 2026-11-07
- add multiforge issue autoclose support ([fe35c96](https://github.com/gitpr-cli/gitpr/commit/fe35c969b150f2f1c3127ec7f38409bae7c5c115)) · 2026-11-07
- track files with and without blame in reviewer suggestions ([405dc7c](https://github.com/gitpr-cli/gitpr/commit/405dc7c1114f2854e02127ae91906ef0b6f4d862)) · 2026-11-05
- add seed command for project configuration files ([d934f21](https://github.com/gitpr-cli/gitpr/commit/d934f2142160592b5f5b3a050eb3309e10d14e58)) · 2026-11-05
- add token trend and latency histogram charts ([67a9e77](https://github.com/gitpr-cli/gitpr/commit/67a9e77d1a388dad9ce297beeb69422382144a98)) · 2026-11-05
- add locale-aware docs site links in help screens ([ffa9b9e](https://github.com/gitpr-cli/gitpr/commit/ffa9b9e55ad11b61e43e79eb4f4513f2ae134be1)) · 2026-11-05
- collapse binary hunks and expand smart excludes ([988dbbc](https://github.com/gitpr-cli/gitpr/commit/988dbbc6dbe0da4ae76c87fa1350e0325f4178b4)) · 2026-11-05
- add check config category and centralize defaults ([74f8c38](https://github.com/gitpr-cli/gitpr/commit/74f8c38478d2bef4dcf8065d6ab3fdaf269de713)) · 2026-11-05
- add Smart Excludes config TUI with project overrides ([b3e547d](https://github.com/gitpr-cli/gitpr/commit/b3e547dfdc7e9ae18980df9131e81b25fea455be)) · 2026-11-04

### 🐛 Correções
- avoid interactive commit TUI without a TTY ([869e2a1](https://github.com/gitpr-cli/gitpr/commit/869e2a18811d21ab328654b4f17f450d2a5fa181)) · 2026-11-06
- stabilize commit app headless test flow ([f57e869](https://github.com/gitpr-cli/gitpr/commit/f57e869a84a197bf5ca41f7c9708be3b88bee677)) · 2026-11-05
- point close-issue help links to autoclose docs ([a33bbbb](https://github.com/gitpr-cli/gitpr/commit/a33bbbb1b6f1f2fa39fb4b8f15b59d006adc3339)) · 2026-11-04

### 📚 Documentação
- add project status report v0.0.22 ([4723bd5](https://github.com/gitpr-cli/gitpr/commit/4723bd59d86696554a4303e052171b88bdb7b96d)) · 2026-11-04

### 🔧 Tarefas
- bump version to 1.6.0 and lang to v0.0.41 ([fedebfd](https://github.com/gitpr-cli/gitpr/commit/fedebfdba72772f9ccad8b4ee223539862846d4b)) · 2026-11-07
- bump version to 1.5.0 and lang to v0.0.38 ([2589338](https://github.com/gitpr-cli/gitpr/commit/25893388d5bcf7053d71d815845fa53f329c1252)) · [#260](https://github.com/gitpr-cli/gitpr/pull/260) · 2026-11-04

### 📦 Outras Alterações
- harden extension publish workflow and add marketplace metadata ([613af18](https://github.com/gitpr-cli/gitpr/commit/613af1800edeac8fa624f1ce0102a5e3eb583a14)) · 2026-11-05
- add docs parity tests for check ci migration ([d1a06f3](https://github.com/gitpr-cli/gitpr/commit/d1a06f3ca96acdad2d2d107961f31e89aae09493)) · 2026-11-05

**Contribuidores:** [@natanfiuza](https://github.com/natanfiuza)
