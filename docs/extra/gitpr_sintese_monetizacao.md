# GitPR — Síntese das 5 Análises de Monetização (GPT, Grok, Claude/Sonnet, GLM, Kimi K3)

## 1. Consenso entre os 5 relatórios

Todos os modelos convergem em pontos-chave, o que os torna as apostas de **maior confiança**:

1. **Não cobrar pela IA em si (preservar BYOK/Ollama).** O core CLI local, LGPL-2.1, com BYOK deve permanecer grátis e completo — é o motor de aquisição e a base de confiança da comunidade open source. Monetizar em cima disso destruiria a reputação e contradiz a proposta de valor "local-first".
2. **O gap não é técnico, é de camada de equipe/colaboração.** Hoje tudo é local, single-player, por repositório. Não existe conceito de "time" — nenhuma sincronização de políticas, dashboard agregado ou visão organizacional. É aí que mercado paga (CodeRabbit, Qodo/PR-Agent, Greptile cobram exatamente por isso).
3. **Modelo open-core é o caminho, não SaaS puro.** Core aberto (CLI, MCP, BYOK, linter local, hooks) + camada paga de conveniência/colaboração/governança (policy sync, dashboard, SSO, auditoria, suporte).
4. **Multi-forge é urgente.** GitPR só suporta GitHub via PAT/REST. GitLab (forte no Brasil) e Bitbucket/Azure DevOps (governo) são mercados inteiros ainda não endereçados — e nichos onde ferramentas locais como o GitPR podem vencer por design (self-managed/air-gapped).
5. **Reaproveitar módulos já existentes é o caminho de menor esforço/maior retorno**: `blame_engine.py` → sugestão de reviewers; `-ht` (histórico de branch) → changelog/release notes automáticos; chat `/tests` → geração de testes versionada; auto-patch do chat (F5) → `gitpr fix` generalizado; `action.yml` já existente → GitHub Marketplace com anotações inline.
6. **Baseline/supressões para adoção em legado.** Nenhuma equipe adota uma ferramenta que trava o pipeline com milhares de problemas pré-existentes. É pré-requisito para venda corporativa.
7. **README/onboarding como alavanca de conversão.** Todos apontam que o README atual é denso e técnico demais — falta um "wow em 30-60 segundos", GIFs/demos da TUI, e uma jornada por persona/objetivo em vez de lista de flags.
8. **Preço de entrada abaixo dos concorrentes** (CodeRabbit US$12-48, Qodo US$19-30, Greptile US$30, Graphite US$40, Sourcery US$12): GitPR deveria ficar na faixa Pro US$6-12/mês e Team US$8-20/dev/mês, alavancando o posicionamento "mesma capacidade, self-hosted, sem lock-in de IA, mais barato".

## 2. Melhores sugestões de FUNCIONALIDADES (consolidado e deduplicado)

### Tier 1 — Alto impacto / baixo esforço (reaproveitam código existente)
- **Sugestão automática de reviewers** via `blame_engine.py` (quem mais tocou aquelas linhas).
- **Changelog / release notes automáticos** (`gitpr release`) a partir do histórico de branch/tags — motor de issues já existe.
- **`gitpr fix`** — generalizar o auto-patch já presente no chat (F5) para aplicar sugestões de review como commit/PR revisável (dry-run por padrão).
- **`gitpr --review-pr <n>`** — revisar PR já aberto puxando o diff da API, atendendo o revisor (não só o autor).
- **GitHub Marketplace Action com comentários inline** — o `action.yml` já existe; falta publicar e comentar linha a linha via Checks API.
- **Instaladores nativos** (brew, scoop, winget, curl one-liner) — o binário PyInstaller já existe, falta distribuição.
- **Modo `gitpr demo`** — diff de exemplo embutido, tour guiado sem precisar de PAT/API key, reduz time-to-value a segundos.
- **Badge/selo "Reviewed by GitPR"** no PR/README — marketing viral gratuito.

### Tier 2 — Diferenciação e retenção (médio esforço)
- **`gitpr split`** — separar mudanças misturadas em commits/PRs atômicos por hunk (feature "uau" para demos).
- **Scanner de segredos (secret scanning)** — extensão do linter regex já existente para um preset de segurança (chaves AWS, tokens, senhas hardcoded).
- **Bridge SAST** (Semgrep, Gitleaks, Bandit) — estende o padrão de bridge Checkstyle já implementado.
- **Geração de testes versionada** (`gitpr tests generate`) — evolução do `/tests` do chat.
- **Modo "Explain my PR"** — resumo em linguagem simples pensado para o revisor, não o autor.
- **Modo "Junior Mentor"** — skill que transforma review em feedback didático; nicho de branding forte, alinhado ao perfil de mentoria do usuário.
- **Risk scoring local** — calcular pontuação de risco por PR/arquivo (área crítica, sem testes, migrations, histórico de bugs) para priorizar atenção humana da IA e do revisor.
- **Policy Packs / Skills compartilháveis** — unificar skills + linter YAML + regras de severidade em um manifesto versionável (ex.: `laravel-enterprise.yml`), com packs prontos por stack (Laravel, Vue, PHP, Node).
- **Baseline e supressões auditáveis** (`gitpr baseline create`) — classifica achados como novos/existentes/resolvidos/dívida aceita; essencial para adoção em legado.
- **Saída SARIF + `gitpr check` unificado para CI** — integra com code scanning, GitHub Checks, pipelines; formatos sarif/json/junit.
- **Extensão VS Code/Cursor/JetBrains** (thin client sobre o MCP já existente) — canal de descoberta que o CLI/MCP sozinhos não entregam.

### Tier 3 — Expansão de mercado (alto esforço, alto retorno)
- **Multi-forge: GitLab, Bitbucket, Azure DevOps** — abstrair `ScmProvider`/`git_host.py` espelhando o Strategy Pattern já usado em `ai_providers.py`. GitLab é forte no Brasil; Azure DevOps em governo (relevante para MROSC).
- **GitHub App** (em vez de só PAT) — instalação de 1 clique, permissões mínimas, menos fricção/medo de token; abre porta para venda corporativa.
- **Índice local do repositório** (tree-sitter/embeddings) — contexto full-codebase (não só diff), o que justifica preços premium de concorrentes como Greptile (82% taxa de detecção).
- **Validação de ticket Jira/Linear no PR** — verificar se o PR atende aos critérios de aceite (diferencial do Qodo).

## 3. Melhores sugestões de MODELO DE MONETIZAÇÃO (síntese)

Estrutura de tiers recomendada, combinando os 5 relatórios:

| Tier | Conteúdo | Preço sugerido |
|---|---|---|
| **Community/Free** | CLI completa, BYOK, Ollama local, commit/PR/review/linter/hooks, MCP básico, SARIF local, packs públicos de stack | US$ 0 |
| **Cloud AI (opcional)** | Proxy de IA gerenciado com cota mensal — remove a fricção de precisar de chave própria; BYOK continua grátis e ilimitado em paralelo | Cota grátis + US$ 6–12/mês sem limite |
| **Pro (indivíduo)** | Multi-forge, SAST bridge, auto-fix, geração de testes, `release`/`fix`/`split`, risk scoring, dashboard sincronizado entre máquinas, secret scanning, changelog automático, suporte prioritário | US$ 8–12/mês |
| **Team** | Policy/Skills sync entre repositórios da org, dashboard web agregado, baseline compartilhado, quality gate travado por admin, sugestão de reviewer, webhooks Slack/Teams, registry privado de plugins | US$ 8–20/dev/mês (ou flat por time, ex. US$ 19–49/mês seats ilimitados) |
| **Enterprise** | SSO/SAML, RBAC, self-hosted/air-gapped com Ollama, auditoria e compliance (relevante para MROSC/governo), SLA, suporte dedicado | Contrato anual sob consulta |

### Estratégia de licenciamento e fases
- **LGPL-2.1 permite dual licensing** sem conflito: core aberto + módulo Pro proprietário, já que você é o único detentor de copyright (sem barreira de CLA).
- **Fase 1 (imediata, custo zero):** GitHub Sponsors / sponsorware com early access a novos providers e presets — valida disposição a pagar antes de construir infraestrutura.
- **Fase 2 (30-90 dias):** Pro individual com license key validada offline (consistente com posicionamento privacy-first) — não exige backend complexo.
- **Fase 3 (3-6 meses):** Team Hub — pode ser um container Docker self-hosted ou serviço cloud mínimo — centraliza políticas e métricas agregadas.
- **Fase 4 (6-12 meses):** Enterprise com self-hosted air-gapped completo.

### Receita complementar (não-assinatura)
- Serviços de implantação/onboarding para equipes (criação de policies, integração CI).
- Packs premium vendidos por organização/repositório.
- Consultoria de qualidade assistida (diagnóstico de dívida técnica usando a própria ferramenta como vitrine).
- Doações/Sponsors como validação inicial de baixo custo.
- Usar Merchant of Record (Paddle, Lemon Squeezy, Polar) para cobrança internacional e Pix/boleto em BRL — diferencial local.

## 4. Recomendações de posicionamento e aquisição

- **Frase-síntese de posicionamento:** "GitPR é um quality gate local-first com IA, políticas versionáveis e integração nativa com Git, CI e MCP."
- **Nicho de autoridade inicial:** Laravel/PHP/Vue — onde você (como especialista) pode oferecer regras muito mais específicas que um reviewer genérico, e onde já há packs sugeridos (`laravel-quality`, `php-security`).
- **Wedge de idioma:** i18n com 5 idiomas (incluindo PT-BR e ES) é vantagem competitiva real — nenhum concorrente grande localiza a interface. Conteúdo em português/espanhol (tutoriais, benchmarks, comparativos "GitPR vs CodeRabbit") pode dominar SEO nesse nicho sem concorrência.
- **Prova social de baixo custo:** GIFs/vídeos (VHS, asciinema) da TUI no README, benchmark público reproduzível do "quality gate de 3 camadas", submissão a diretórios (awesome-ai-code-review, Smithery/Glama/PulseMCP para MCP).
- **Pro grátis para projetos open source** — alavanca de crescimento comprovada (usada pelo CodeRabbit): projetos públicos se tornam vitrine permanente do produto.
- **Bump de versão para 1.0** — a maturidade real (264 testes, MCP com 12 tools, 5 idiomas) já justifica e reduz a percepção de imaturidade da numeração 0.0.x.
