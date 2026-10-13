## [1.4.0] - 2026-10-12

### Resumo
Esta release marca a versão 1.4.0 e traz avanços importantes para quem revisa e acompanha mudanças de código. Agora é possível suprimir avisos já conhecidos de forma persistente, tanto pela linha de comando quanto em fluxos de revisão, além de aplicar conjuntos de políticas configuráveis com suporte a múltiplos idiomas. A avaliação de risco de alterações e revisões passa a ser determinística, oferecendo resultados consistentes e previsíveis, e um novo modo de mentoria ajuda a explicar as revisões em linguagem mais didática, ideal para pessoas em início de carreira. O histórico de telemetria foi migrado para um armazenamento local mais robusto e confiável, e as notas de versão agora ficam vinculadas e ancoradas ao changelog, facilitando a consulta do que mudou. A documentação também foi atualizada para refletir todas essas novidades.

### ✨ Funcionalidades
- add baseline suppressions with CLI, MCP and PR support ([8450186](https://github.com/gitpr-cli/gitpr/commit/84501867ef98a7b44ead0495842665874cd376bf)) · 2026-10-10
- add policy packs with CLI, i18n and tests ([4d42d56](https://github.com/gitpr-cli/gitpr/commit/4d42d56736e857c91385ec49da1e98a79286a12d)) · 2026-10-10
- add deterministic risk scoring for diffs and reviews ([c46440f](https://github.com/gitpr-cli/gitpr/commit/c46440f9a0b94a8303dd69231cfd97a7de8c8227)) · 2026-10-08
- add junior mentor mode for code review explanations ([57c5140](https://github.com/gitpr-cli/gitpr/commit/57c51400bb3362f65ff2ed398df018b77a3a3569)) · 2026-10-07
- replace JSON telemetry with SQLite ledger ([811651f](https://github.com/gitpr-cli/gitpr/commit/811651f040b80db3250d91e377f4c1cb5f27ac59)) — metrics · 2026-09-29
- add linked release notes anchored on the changelog ([c561664](https://github.com/gitpr-cli/gitpr/commit/c561664916900e46e06eba920da558a810ba1b1b)) · 2026-09-23

### 📚 Documentação
- update docs files ([e1cfb11](https://github.com/gitpr-cli/gitpr/commit/e1cfb11bca4c420b76810d983c17869f5746fc20)) · 2026-10-09
- update docs files ([4380ce8](https://github.com/gitpr-cli/gitpr/commit/4380ce82818d84bec727f2bef98c9c446a596f89)) · 2026-09-24
- update docs files ([64a406f](https://github.com/gitpr-cli/gitpr/commit/64a406f4d02274d6f5576be9bc727ae644f768f1)) · 2026-09-24

### 🔧 Tarefas
- bump version to 1.4.0 and update lang/scripts versions ([af35270](https://github.com/gitpr-cli/gitpr/commit/af352702ff60abbf7b4ebc9f8c2ed574377611fa)) · 2026-10-12

**Contribuidores:** [@natanfiuza](https://github.com/natanfiuza)
