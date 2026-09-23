## [1.3.0] - 2026-09-23

### Resumo
Esta release amplia significativamente os recursos de apoio ao fluxo de trabalho com pull requests e à qualidade do código. Foram adicionados comandos que geram automaticamente suítes de testes com inteligência artificial, dividem alterações em commits atômicos e apresentam um guia para revisores, além de reforçar a segurança com verificações de análise estática e detecção de segredos embutidas no linter. A experiência de apresentação também melhora, com um selo de identificação incluído nos pull requests e nos READMEs, um tour guiado de demonstração baseado em exemplos gravados e um tutorial de atualização automática. Por fim, a documentação foi revisada e atualizada para refletir todas essas novidades.

### ✨ Funcionalidades
- add reviewer guide explain command and PR section ([6138cf1](https://github.com/gitpr-cli/gitpr/commit/6138cf1e5fe2001fb4be89b604f564f188ff5612)) · 2026-09-23
- add AI-powered test suite generation command ([7d84daf](https://github.com/gitpr-cli/gitpr/commit/7d84daf7ff8a8d5acf924547297c10b259ce1fff)) · 2026-09-22
- add Semgrep, Gitleaks and Bandit SAST bridges ([a799664](https://github.com/gitpr-cli/gitpr/commit/a799664dd0e79b8b1d81dc7985afb035780001f3)) — linter · 2026-09-22
- add embedded secret scanning ruleset to linter ([47784a7](https://github.com/gitpr-cli/gitpr/commit/47784a751cab2bb673be481c0046461e0e287d4c)) · 2026-09-21
- add command to split changes into atomic commits ([c38aed2](https://github.com/gitpr-cli/gitpr/commit/c38aed23a30d02e41a1de1e49157dba86c89ece3)) — split · 2026-09-21
- add GitPR badge to PR bodies and README snippet ([69f41ec](https://github.com/gitpr-cli/gitpr/commit/69f41ecd7f7bf7228959bfc83460e6572404039f)) · 2026-09-19
- add gitpr demo guided tour over recorded examples ([da162d0](https://github.com/gitpr-cli/gitpr/commit/da162d0d705664b5a710adf6b7d385b1fd7f22b3)) · 2026-09-18

### 📚 Documentação
- add auto update tutorial ([8920d13](https://github.com/gitpr-cli/gitpr/commit/8920d13e1bd58c80ac9c35ad7c2d2df4c0b1844d)) · 2026-09-18
- update docs files ([4218b5a](https://github.com/gitpr-cli/gitpr/commit/4218b5aae99adc6092315254b2090bf3e6084073)) · 2026-09-17

**Contribuidores:** [@natanfiuza](https://github.com/natanfiuza)
