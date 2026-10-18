## [1.4.1] - 2026-10-18

### Resumo
Esta release 1.4.1 traz uma atualização do pacote de idiomas e uma série de melhorias voltadas à experiência de uso e à integração com fluxos de trabalho de desenvolvimento. Agora o processo de merge exibe uma janela de progresso com mensagens traduzidas, oferecendo retorno claro sobre o andamento da operação. O carregamento de contexto foi tornado mais robusto: artefatos corrompidos deixam de causar falhas e passam a ser descartados automaticamente. Também foi adicionada uma extensão para o VS Code e novas ferramentas para verificar e publicar servidores MCP, ampliando as possibilidades de integração com o editor. Para equipes que usam integração contínua, há um novo comando unificado de verificação que gera relatórios em múltiplos formatos, facilitando o consumo dos resultados por diferentes ferramentas. Por fim, a documentação de changelog foi atualizada para refletir essas mudanças.

### ✨ Funcionalidades
- add merge progress modal with i18n feedback ([8557125](https://github.com/gitpr-cli/gitpr/commit/8557125561bf1baab3b380b4bdae8a8b19db5f0d)) · 2026-10-18
- add VS Code extension and MCP check/publish tools ([b6382b5](https://github.com/gitpr-cli/gitpr/commit/b6382b5f7e05df162a99b6b0a9f27edfa558191f)) · 2026-10-16
- add gitpr check unified CI command with SARIF/JSON/JUnit output ([a50f21c](https://github.com/gitpr-cli/gitpr/commit/a50f21c835a717a9933138939356b93634f42a5f)) · 2026-10-15

### 🐛 Correções
- strip corrupted PR skill artifact when loading context ([525a1ec](https://github.com/gitpr-cli/gitpr/commit/525a1ecf8309f8888fdb055ab76da9455e860176)) · 2026-10-17

### 📚 Documentação
- update changelog file ([fc9d400](https://github.com/gitpr-cli/gitpr/commit/fc9d4007cf61c02195ec837bb6024d1d06f874fb)) · 2026-10-12

### 🔧 Tarefas
- bump version to 1.4.1 and lang to v0.0.35 ([46c25c1](https://github.com/gitpr-cli/gitpr/commit/46c25c137b0a71c33cdccdbf650a0c20077564ff)) · 2026-10-18

### 📦 Outras Alterações
- update changelog file ([1abb1b5](https://github.com/gitpr-cli/gitpr/commit/1abb1b5cde042025174407edb534a4ee0aaed601)) · 2026-10-12

**Contribuidores:** [@natanfiuza](https://github.com/natanfiuza)
