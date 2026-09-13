## [1.1.0] - 2026-09-13

### Resumo
Esta release amplia significativamente o assistente GitPR, adicionando integração com editores, prompts baseados em templates, um assistente interativo de configuração e instalação e suporte a chat em terminal com múltiplos provedores, incluindo Ollama. O fluxo de pull requests foi reforçado com publicação, push, tratamento de PRs existentes, merge e revisores sugeridos, enquanto a geração de issues padronizadas e a arqueologia de código ganharam novas telas e recursos. Também foram introduzidos sistema global de plugins, processamento map-reduce para diffs grandes, filtros inteligentes e exclusões locais e remotas para reduzir tokens, além de métricas e telemetria com exportação e dashboard. A experiência multilíngue foi expandida e corrigida, com internacionalização de chaves, traduções para vários idiomas e ajustes de consistência. Por fim, foram feitas melhorias de segurança e confiabilidade, como prevenção de injeção de shell, limites de rede e DNS, melhor tratamento de commits e erros, e a distribuição passa a exigir atualização via PyPI, descontinuando releases binárias.

### ✨ Funcionalidades
- enforce mandatory update via PyPI and drop binary release (f108c4c)
- add interactive config TUI, usage log and i18n keys (bf9f1b9) — config

**Contribuidores:** Nataniel Fiuza
