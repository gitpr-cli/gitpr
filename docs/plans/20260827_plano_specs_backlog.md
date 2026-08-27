# GitPR — Specs de Tarefa do Backlog

> Geradas a partir do backlog bruto. Cada spec é autocontida e pronta para execução por um agente de desenvolvimento. Nenhuma implementação de código foi realizada nesta etapa.

---

## Item 1 — Guard de i18n para chaves `__()` sem entrada no dicionário

### Título
Estender `test_i18n.py` para detectar chamadas `__()` sem tradução registrada

### Objetivo
Garantir que qualquer nova chamada `__()` introduzida no código-fonte que não possua entrada correspondente no dicionário de traduções seja detectada automaticamente pela suíte de testes, fechando uma lacuna do guard atual que não cobre `missing == 0` para novas ocorrências.

### Escopo
- `test_i18n.py`
- Dicionário(s) de tradução consumido(s) pelo guard (ex.: arquivos de idioma em `lang/` ou equivalente)
- Não inclui alteração do mecanismo de extração de chamadas `__()` já existente, apenas sua extensão de verificação

### Critérios de Aceite
- O teste falha quando uma chamada `__()` referencia uma chave ausente no dicionário de traduções.
- O teste continua validando paridade entre idiomas, mangled keys e chaves identidade (comportamento atual preservado).
- A nova verificação cobre `missing == 0` como condição explícita de sucesso (zero chaves ausentes tolerado).
- Mensagem de falha do teste identifica claramente a(s) chave(s) ausente(s) e o arquivo/linha de origem, quando possível.
- Suíte de testes existente continua passando sem regressões.

### Casos de Teste
- Unitário: chamada `__('chave_existente')` — teste passa.
- Unitário: chamada `__('chave_inexistente')` injetada artificialmente (fixture/mock) — teste falha com mensagem indicando a chave ausente.
- Unitário: chave presente em um idioma mas ausente em outro — continua coberto pela validação de paridade já existente.
- Regressão: execução completa de `test_i18n.py` sobre o estado atual do código não deve introduzir falsos positivos.

### Riscos/Dependências
- Depende do inventário atual de todas as chaves `__()` usadas no código estar completo; falso negativo pode ocorrer se a extração de chamadas não cobrir todos os padrões de invocação (ex.: chamadas dinâmicas com variável).
- Pode expor débito técnico oculto (chaves já ausentes) ao ser ativado, exigindo triagem antes do merge.
- Não deve ser confundido com o item de remoção dos scripts one-off de i18n (item 4), que trata de scripts auxiliares, não do guard de teste.

### Fora de Escopo
- Geração automática de traduções faltantes.
- Alteração do processo de tradução/dicionário em si.
- Cobertura de chamadas `__()` dinâmicas construídas via concatenação de string em runtime (fora do padrão estático).

---

## Item 2 — Teste end-to-end manual do PR Publisher no fluxo TUI real

### Título
Documentar teste manual end-to-end do PR Publisher com diff que quebra o linter

### Objetivo
Definir e documentar um roteiro de teste manual, executado no fluxo TUI real (sem mocks), que valide o comportamento do PR Publisher diante de um diff que viola regras do linter, cobrindo um caminho não testável pela suíte headless atual.

### Escopo
- Documentação de teste manual (novo documento, ex.: `docs/testing/manual_pr_publisher_e2e.md` ou local equivalente ao padrão de documentação do projeto)
- Fluxo TUI do PR Publisher (`pr_publish_app.py` e integrações associadas), apenas como objeto de teste — não é alterado código nesta tarefa
- Não inclui automação do cenário; é exclusivamente roteiro manual

### Critérios de Aceite
- Documento descreve pré-condições (estado do repositório, branch, configuração de linter ativa).
- Documento descreve passo a passo a execução real da TUI, incluindo geração de um diff que aciona falha de linter.
- Documento descreve o resultado esperado (ex.: modal de linter exibido, bloqueio ou aviso de publicação, comportamento de fallback).
- Documento inclui critérios objetivos de PASS/FAIL para cada etapa.
- Roteiro é executável por qualquer desenvolvedor da equipe sem conhecimento prévio da implementação interna.

### Casos de Teste
- Manual: diff que introduz violação de linter em arquivo já rastreado — validar exibição do modal/aviso de linter na TUI real.
- Manual: diff que introduz violação de linter em arquivo novo (não rastreado anteriormente) — validar comportamento de detecção.
- Manual: fluxo de publicação após resolução da violação (usuário corrige e tenta novamente) — validar que o PR Publisher permite prosseguir.
- Manual: cancelamento do fluxo após aviso de linter — validar que nenhuma ação destrutiva ocorre (sem PR criado, sem commit indevido).

### Riscos/Dependências
- Requer ambiente com Git real, IA configurada e linter instalado — não pode ser executado em CI headless.
- Resultado depende de configuração local de linter (`.gitpr/conf/`), o que pode gerar inconsistência entre execuções de diferentes testadores; documento deve fixar a configuração de referência.
- Relacionado ao item 3 (cobertura de `pr_publish_app.py`), mas não a substitui — testes automatizados e manual são complementares.

### Fora de Escopo
- Automação do cenário via CI/CD.
- Cobertura de outros tipos de erro de publicação (ex.: falha de rede, conflito de merge) — foco exclusivo em falha de linter.
- Alteração de comportamento do PR Publisher.

---

## Item 3 — Cobertura de testes para `pr_publish_app.py` e `github_api.py`

### Título
Completar cobertura de testes automatizados de `pr_publish_app.py` e `github_api.py`

### Objetivo
Elevar a cobertura de testes automatizados dos módulos `pr_publish_app.py` e `github_api.py` para os fluxos ainda não exercitados, complementando o progresso já existente em `test_pr_publish_linter_modal.py`.

### Escopo
- `pr_publish_app.py`
- `github_api.py`
- Novos arquivos de teste (ex.: `test_pr_publish_app.py`, `test_github_api.py`), preservando `test_pr_publish_linter_modal.py` existente

### Critérios de Aceite
- Fluxos principais de `pr_publish_app.py` não cobertos por `test_pr_publish_linter_modal.py` (navegação da TUI, estados de sucesso/erro, cancelamento) possuem teste automatizado com mocks de Git/IA.
- Funções de `github_api.py` (autenticação, criação de PR, tratamento de erros de API) possuem teste unitário com mocks de chamadas HTTP.
- Cobertura de código dos dois módulos é reportada e documentada (percentual antes/depois).
- Nenhum teste novo depende de credenciais reais ou acesso à rede.
- Suíte existente (`test_pr_publish_linter_modal.py`) permanece passando sem alteração de comportamento.

### Casos de Teste
- Unitário: `github_api.py` — criação de PR com sucesso (mock de resposta 201).
- Unitário: `github_api.py` — tratamento de erro de autenticação (mock de resposta 401/403).
- Unitário: `github_api.py` — tratamento de rate limit da API do GitHub.
- Unitário: `pr_publish_app.py` — transição de estado da TUI ao publicar PR com sucesso.
- Unitário: `pr_publish_app.py` — transição de estado ao cancelar publicação.
- Integração: fluxo completo mockado (diff → linter OK → chamada a `github_api.py` → confirmação de PR criado).

### Riscos/Dependências
- Testes headless mockados não cobrem o cenário manual descrito no item 2; ambos são necessários para cobertura completa.
- Mudanças em `github_api.py` podem exigir alinhamento com a interface usada por outros módulos consumidores (verificar acoplamento antes de refatorar assinaturas).
- Depende de `test_pr_publish_linter_modal.py` como referência de padrão de mock já estabelecido no projeto.

### Fora de Escopo
- Teste end-to-end manual (tratado no item 2).
- Alteração de lógica de negócio de `pr_publish_app.py` ou `github_api.py`.
- Testes de performance/carga da API do GitHub.

---

## Item 4 — Avaliação de remoção/arquivamento dos scripts one-off de i18n

### Título
Avaliar remoção ou arquivamento dos scripts one-off de correção de i18n

### Objetivo
Determinar se os scripts `fix_pt_br.py`, `fix_pt_br_pass2.py`, `final_fix.py`, `_temp_check_i18n.py` e `generate_lang_files.py` em `scripts/` ainda possuem utilidade ativa, e executar sua remoção ou arquivamento formal caso contenham apenas tabelas inertes de chaves mangled.

### Escopo
- `scripts/fix_pt_br.py`
- `scripts/fix_pt_br_pass2.py`
- `scripts/final_fix.py`
- `scripts/_temp_check_i18n.py`
- `scripts/generate_lang_files.py`
- Possível diretório de arquivamento (ex.: `scripts/archive/` ou remoção via Git history)

### Critérios de Aceite
- Cada script é avaliado individualmente quanto a: (a) ser referenciado em algum pipeline, Makefile, CI ou documentação ativa; (b) conter lógica reutilizável fora do contexto pontual em que foi criado.
- Decisão documentada por script: manter, arquivar ou remover, com justificativa.
- Scripts confirmados como obsoletos são removidos do diretório `scripts/` (ou movidos para pasta de arquivo, conforme convenção do projeto) sem quebrar nenhuma referência ativa.
- Nenhuma automação (CI, Git hooks, comandos documentados) referencia os scripts removidos após a mudança.
- Decisão e resultado são registrados em changelog ou documentação equivalente.

### Casos de Teste
- Manual/verificação: busca textual no repositório por referências a cada script (imports, chamadas em CI, menções em documentação).
- Manual: execução de suíte de testes completa após remoção, confirmando ausência de dependência oculta.
- Manual: validação de que o guard estendido do item 1 não depende de nenhum desses scripts para funcionar.

### Riscos/Dependências
- Deve ser executado após ou em paralelo ao item 1, garantindo que o novo guard de `test_i18n.py` não dependa desses scripts como ferramenta de correção futura.
- Remoção prematura pode eliminar histórico útil para auditoria de como chaves mangled foram corrigidas no passado — considerar preservar via Git tag ou arquivamento em vez de exclusão definitiva.
- Requer confirmação explícita (regra de desenvolvimento) de que não há dependências ativas antes do arquivamento.

### Fora de Escopo
- Correção de novas chaves mangled encontradas durante a avaliação (deve virar item de backlog separado, se necessário).
- Reescrita ou modernização dos scripts mantidos.

---

## Item 5 — Atualização de `CLAUDE.md`

### Título
Corrigir versão e remover referência obsoleta em `CLAUDE.md`

### Objetivo
Atualizar `CLAUDE.md` para refletir a versão real do projeto e remover menção à flag `--publish`, descontinuada, estabelecendo `ARCHITECTURE.md` como fonte de verdade para detalhes arquiteturais.

### Escopo
- `CLAUDE.md`
- Referência cruzada para `ARCHITECTURE.md` (sem alterar o conteúdo de `ARCHITECTURE.md` nesta tarefa, apenas apontar para ele)

### Critérios de Aceite
- Versão declarada em `CLAUDE.md` é atualizada de `0.0.30` para `0.0.37`.
- Toda menção à flag `--publish` é removida do documento.
- Documento passa a indicar explicitamente `ARCHITECTURE.md` como referência primária para decisões arquiteturais, evitando duplicação de informação desatualizada.
- Nenhuma outra informação factual do documento é alterada além do escopo definido.
- Revisão confirma que nenhuma outra flag ou versão desatualizada permanece no arquivo (checagem pontual, não auditoria completa).

### Casos de Teste
- Manual: leitura completa de `CLAUDE.md` pós-edição confirmando ausência de `0.0.30` e de `--publish`.
- Manual: verificação de que o link/referência a `ARCHITECTURE.md` está correto e acessível.
- Regressão: nenhum teste automatizado deve depender do conteúdo textual de `CLAUDE.md` (verificar ausência de tal acoplamento).

### Riscos/Dependências
- Deve ser coordenado com o estado real do código: confirmar que `0.0.37` é de fato a versão vigente no momento da execução (ver item 13, que trata de versionamento de presets, para não confundir os dois marcadores de versão).
- Se `--publish` ainda for referenciada em outros documentos (ex.: `README.md`, `HELP_MAP`), essas ocorrências não são cobertas por esta tarefa e devem ser tratadas separadamente.

### Fora de Escopo
- Atualização de `ARCHITECTURE.md` em si.
- Remoção de `--publish` do código-fonte (esta tarefa é apenas documental).
- Correção de outras inconsistências não relacionadas a versão ou à flag `--publish`.

---

## Item 6 — Correção de referências quebradas no `HELP_MAP`

### Título
Corrigir links quebrados em `HELP_MAP`

### Objetivo
Atualizar as referências quebradas em `HELP_MAP` para apontar aos arquivos de ajuda corretos e existentes.

### Escopo
- Arquivo `HELP_MAP` (ou módulo/estrutura de dados equivalente que mapeia comandos a arquivos de ajuda)
- Confirmação de existência de `understanding_chat_functionality.md` e `metricas-telemetria.md`

### Critérios de Aceite
- Referência a `chat-interativo.md` é substituída por `understanding_chat_functionality.md`.
- Referência a `metricas_analytics_dashboard.md` é substituída por `metricas-telemetria.md`.
- Todos os demais links em `HELP_MAP` são verificados quanto à existência do arquivo de destino (checagem pontual associada a esta correção).
- Nenhum link do `HELP_MAP` aponta para arquivo inexistente após a mudança.

### Casos de Teste
- Unitário/script: iteração automatizada sobre todas as entradas de `HELP_MAP` verificando existência física de cada arquivo referenciado.
- Manual: acesso à ajuda via comando correspondente na TUI/CLI para `chat-interativo` e para `metricas-analytics-dashboard`, confirmando que o conteúdo correto é exibido.

### Riscos/Dependências
- Depende da existência confirmada e estável de `understanding_chat_functionality.md` e `metricas-telemetria.md` no momento da execução — caso ainda não existam, esta tarefa deve ser bloqueada até sua criação.
- Pode haver outras referências quebradas não listadas no backlog; a verificação automatizada proposta nos Critérios de Aceite deve capturá-las, mas correções fora das duas explicitamente citadas devem ser reportadas, não necessariamente corrigidas nesta mesma tarefa.

### Fora de Escopo
- Criação ou reescrita do conteúdo dos arquivos de ajuda referenciados.
- Reestruturação geral do sistema de ajuda/`HELP_MAP`.

---

## Item 7 — Gráficos ASCII/Textual no dashboard de métricas da TUI

### Título
Adicionar histograma de tempo e gráfico de tendência de tokens ao dashboard de métricas

### Objetivo
Enriquecer o dashboard de métricas da TUI com visualizações ASCII/Textual que exibam a distribuição de tempo de execução (histograma) e a tendência de consumo de tokens ao longo do tempo (gráfico de tendência).

### Escopo
- Módulo(s) do dashboard de métricas da TUI (componente Textual responsável pela tela de métricas)
- Fonte de dados de métricas já coletadas (tempo de execução e consumo de tokens), sem alterar o mecanismo de coleta

### Critérios de Aceite
- Dashboard exibe um histograma ASCII/Textual representando a distribuição de tempo de execução das operações registradas.
- Dashboard exibe um gráfico de tendência ASCII/Textual mostrando a evolução do consumo de tokens ao longo do tempo (por sessão ou por período configurável).
- Ambas as visualizações se ajustam corretamente a diferentes tamanhos de terminal (responsividade mínima do componente Textual).
- Visualizações são atualizadas corretamente quando novos dados de métricas são gerados (refresh do dashboard).
- Ausência de dados (ex.: nenhuma métrica coletada ainda) é tratada com estado vazio apropriado, sem erro visual ou exceção.

### Casos de Teste
- Unitário: geração do histograma com conjunto de dados conhecido — validar buckets e proporções corretos.
- Unitário: geração do gráfico de tendência com série temporal conhecida — validar ordenação cronológica e escala.
- Unitário: renderização com dataset vazio — validar mensagem de estado vazio sem exceção.
- Manual: visualização em terminal real com dados reais acumulados, validando legibilidade e ausência de quebra de layout.

### Riscos/Dependências
- Depende da disponibilidade e granularidade atual dos dados de métricas já coletados pelo GitPR; se a coleta não possuir granularidade temporal suficiente, o gráfico de tendência pode exigir ajuste na coleta (fora do escopo original, deve ser sinalizado como bloqueio).
- Terminais com largura muito reduzida podem exigir modo de exibição simplificado — validar com o padrão de responsividade já usado em outras telas Textual do projeto.

### Fora de Escopo
- Alteração do mecanismo de coleta ou armazenamento das métricas.
- Exportação dos gráficos para formatos externos (imagem, PDF, etc.).
- Novas métricas além de tempo de execução e consumo de tokens.

---

## Item 8 — Pipeline de release no GitHub Actions

### Título
Criar pipeline de release automatizado via GitHub Actions com PyInstaller

### Objetivo
Automatizar o processo de build e publicação de releases do GitPR, gerando executáveis via PyInstaller e publicando os artefatos como assets em GitHub Releases.

### Escopo
- Novo workflow em `.github/workflows/` (ex.: `release.yml`)
- Configuração de build do PyInstaller (spec file, se necessário)
- Não inclui alteração da lógica de negócio do GitPR

### Critérios de Aceite
- Workflow é disparado por evento definido (ex.: push de tag semver ou criação de release rascunho) e documentado claramente.
- Pipeline executa build completo via PyInstaller para a(s) plataforma(s)-alvo definida(s) (especificar Linux/Windows conforme suporte atual do projeto).
- Artefatos gerados são publicados automaticamente como assets anexados à GitHub Release correspondente.
- Pipeline falha de forma clara e visível caso o build do PyInstaller falhe, sem publicar release parcial ou corrompida.
- Versão do artefato publicado corresponde à tag/versão que disparou o workflow.

### Casos de Teste
- Integração (CI): disparo do workflow com tag de teste em branch isolada, validando build bem-sucedido e upload de asset.
- Integração (CI): simulação de falha de build (ex.: erro proposital de import) — validar que o workflow falha e não publica asset incompleto.
- Manual: download do asset publicado em ambiente limpo e execução para validar integridade do executável.

### Riscos/Dependências
- Depende da atualização correta de versão em `CLAUDE.md` (item 5) e do marcador `LINTER_PRESETS_VERSION` (item 13) estarem consistentes antes de um release oficial, para evitar publicar artefato com metadados de versão divergentes.
- Build multiplataforma via PyInstaller pode exigir runners específicos do GitHub Actions (ubuntu-latest, windows-latest) — checar suporte de dependências nativas do projeto em cada plataforma.
- Necessário definir política de assinatura/checksum dos artefatos, se exigido pela política de segurança do projeto (a confirmar antes da implementação).

### Fora de Escopo
- Publicação em outros canais de distribuição (PyPI, Snap, Homebrew, etc.).
- Geração de changelog automático (pode ser tratado como melhoria futura do pipeline).
- Assinatura de código/certificados de plataforma (Windows/macOS), salvo indicação explícita em revisão posterior.

---

## Item 9 — Comando `--init` local

### Título
Implementar comando `--init` para inicialização de configuração local

### Objetivo
Prover um comando `--init` que crie a estrutura `.gitpr/conf/` com templates padrão de configuração (smart-excludes, linter, entre outros), facilitando o primeiro uso do GitPR em um repositório.

### Escopo
- Novo módulo/comando CLI (ex.: `gitpr --init` ou subcomando equivalente ao padrão de CLI já usado no projeto)
- Templates de configuração a serem gerados em `.gitpr/conf/` (smart-excludes, linter, e outros arquivos de configuração já suportados pelo GitPR)

### Critérios de Aceite
- Execução de `--init` cria o diretório `.gitpr/conf/` (caso não exista) com templates padrão para smart-excludes, linter e demais configurações aplicáveis.
- Execução repetida de `--init` sobre uma configuração já existente é idempotente: não sobrescreve arquivos já presentes sem sinalização explícita do usuário (ex.: flag `--force` ou confirmação interativa).
- Comando informa claramente ao usuário quais arquivos foram criados, quais já existiam e foram preservados.
- Templates gerados são sintaticamente válidos e imediatamente utilizáveis pelo restante do GitPR sem edição manual obrigatória.
- Comando funciona corretamente tanto em repositório novo (sem `.gitpr/`) quanto em repositório com configuração parcial existente.

### Casos de Teste
- Unitário: `--init` em diretório sem `.gitpr/` — valida criação completa da estrutura e conteúdo dos templates.
- Unitário: `--init` repetido sem flag de força — valida que arquivos existentes não são sobrescritos.
- Unitário: `--init` com flag de força (ou fluxo de confirmação) sobre configuração existente — valida sobrescrita explícita e intencional.
- Unitário: `--init` com `.gitpr/conf/` parcialmente populado (ex.: só linter configurado) — valida que apenas os arquivos faltantes são criados.
- Integração: após `--init`, executar um fluxo básico do GitPR (ex.: geração de commit semântico) consumindo a configuração recém-criada, validando compatibilidade.

### Riscos/Dependências
- Depende de alinhamento com o item 12 (external_linters) e item 13 (LINTER_PRESETS_VERSION), já que os templates de linter gerados por `--init` devem seguir o mesmo padrão de versionamento de presets.
- Sobrescrita acidental de configuração local é um risco crítico — a regra de desenvolvimento exige idempotência e sinalização explícita, portanto a ausência de flag de força deve ser o comportamento seguro por padrão.

### Fora de Escopo
- Configuração interativa avançada (wizard completo de perguntas) além da geração de templates padrão — pode ser evolução futura.
- Migração automática de configurações antigas/incompatíveis para o novo formato.

---

## Item 10 — Suporte a novos provedores de IA (OpenAI direto e locais adicionais)

### Título
Adicionar suporte a OpenAI direto e provedores de IA locais adicionais

### Objetivo
Estender o GitPR para suportar OpenAI como provedor direto e provedores locais adicionais, preservando a interface comum já usada por Gemini, DeepSeek e Ollama.

### Escopo
- `ai_providers.py`
- Configuração de seleção de provedor (arquivo `.env` / `.gitpr/conf/`)
- Documentação de provedores suportados

### Critérios de Aceite
- Novo(s) provedor(es) implementam a mesma interface comum já usada pelos provedores existentes (mesmo contrato de métodos/assinatura de entrada e saída).
- Usuário pode selecionar OpenAI ou o(s) novo(s) provedor(es) local(is) via configuração, sem alteração de código.
- Troca de provedor não exige alteração em nenhum módulo consumidor de `ai_providers.py` (Code Review, geração de commit, geração de PR, etc.).
- Erros específicos de cada provedor (autenticação, rate limit, timeout) são tratados de forma consistente com o padrão já estabelecido para os provedores existentes.
- Documentação lista os provedores suportados e os requisitos de configuração de cada um (chave de API, endpoint local, etc.).

### Casos de Teste
- Unitário: chamada mockada ao provedor OpenAI retornando sucesso — validar parsing de resposta conforme interface comum.
- Unitário: chamada mockada ao provedor OpenAI retornando erro de autenticação — validar tratamento de erro padronizado.
- Unitário: chamada mockada ao(s) novo(s) provedor(es) local(is) — mesmas validações de sucesso/erro.
- Integração: alternância entre provedores (Gemini → OpenAI → provedor local) usando a mesma chamada de alto nível (ex.: geração de commit semântico), validando que o resultado segue o mesmo formato independentemente do provedor.
- Regressão: suíte de testes de Gemini, DeepSeek e Ollama permanece passando sem alteração de comportamento.

### Riscos/Dependências
- Depende diretamente do item 11 (hardening de timeout da SDK de IA) — o timeout default de ~600s deve ser aplicado uniformemente também aos novos provedores.
- Interface comum deve ser respeitada rigorosamente (regra de desenvolvimento); qualquer necessidade de estender a interface para acomodar peculiaridade de um novo provedor deve ser avaliada com cautela para não quebrar os provedores existentes.
- Provedores locais adicionais podem exigir descoberta de endpoint/porta configurável, análogo ao padrão já usado para Ollama.

### Fora de Escopo
- Fine-tuning ou treinamento de modelos.
- Suporte a streaming de resposta, salvo se já suportado pela interface comum atual.
- Provedores de IA não especificados nesta tarefa (avaliação de novos provedores além dos mencionados deve ser item de backlog separado).

---

## Item 11 — Hardening de subprocesso, timeouts e DNS-bounding

### Título
Eliminar `shell=True`, aplicar timeout explícito na SDK de IA e DNS-bounding em chamadas `urllib`

### Objetivo
Reduzir superfície de risco de segurança e travamento do GitPR substituindo execução de shell via f-string por lista de argumentos, definindo timeout explícito e configurável para a SDK de IA, e aplicando padrão de DNS-bounding às chamadas de rede via `urllib`.

### Escopo
- `_run_external_linter` (localização a confirmar, presumivelmente em módulo de execução de linter)
- `ai_providers.py` (configuração de timeout da SDK)
- `i18n.py` (usos de `urllib`)
- `ai_providers.py` (usos de `urllib`, se distintos da chamada de SDK)

### Critérios de Aceite
- `_run_external_linter` não utiliza mais `shell=True` com interpolação de f-string; comando é executado a partir de lista de argumentos (`shlex.split` ou construção direta de lista/argv).
- Toda chamada à SDK de IA em `ai_providers.py` possui timeout explícito, com valor default de aproximadamente 600 segundos, configurável via `.env` ou configuração equivalente.
- Usos de `urllib` em `i18n.py` e `ai_providers.py` aplicam o padrão de DNS-bounding já estabelecido no projeto (a ser referenciado/documentado, caso ainda não exista um padrão formalizado, este deve ser definido nesta tarefa).
- Comportamento funcional de linter e chamadas de IA permanece o mesmo para os fluxos existentes (nenhuma regressão funcional, apenas hardening).
- Testes de regressão cobrem os cenários alterados, conforme regra de desenvolvimento do projeto.

### Casos de Teste
- Unitário: `_run_external_linter` com comando contendo caracteres especiais (aspas, espaços, `;`, `&&`) — validar que a execução via lista de argumentos trata o comando como argumento único/seguro, sem interpretação de shell.
- Unitário: `_run_external_linter` com linter configurado corretamente — validar que a saída/comportamento permanece idêntico ao pré-mudança.
- Unitário: chamada à SDK de IA mockada que excede o timeout configurado — validar que a exceção de timeout é levantada corretamente e tratada.
- Unitário: configuração de timeout customizado (diferente do default) — validar que o valor configurado é respeitado.
- Unitário: chamada `urllib` em `i18n.py` e `ai_providers.py` — validar que resolução de DNS/conexão respeita o bounding definido (mock de resolução de host).
- Regressão: suíte completa de testes de linter e de provedores de IA permanece passando.

### Riscos/Dependências
- Mudança em `_run_external_linter` pode impactar diretamente o item 12 (suporte a `external_linters` em modo full-file), portanto a ordem de execução recomendada é concluir o hardening antes ou em conjunto com o item 12, para evitar retrabalho.
- Alteração de timeout na SDK de IA pode afetar os testes de novos provedores (item 10) — recomenda-se sincronizar a implementação de ambos os itens.
- Definição do "padrão de DNS-bounding" precisa estar clara antes da implementação; se o padrão ainda não existir formalmente no projeto, esta tarefa deve incluir sua definição mínima documentada.

### Fora de Escopo
- Auditoria de segurança completa do projeto (esta tarefa cobre apenas os pontos explicitamente listados).
- Sandbox completo de execução de subprocessos (ex.: containers, seccomp) — fora do escopo de hardening definido aqui.
- Alteração de comportamento de negócio do linter ou dos provedores de IA além do necessário para o hardening.

---

## Item 12 — Suporte a `external_linters` em modo full-file e correção de filtro Checkstyle

### Título
Suportar `external_linters` via `--input` em modo full-file e corrigir filtro XML do Checkstyle

### Objetivo
Permitir que linters externos configurados operem em modo full-file recebendo o conteúdo via `--input`, e corrigir o filtro de saída XML do Checkstyle para cruzar corretamente resultados por arquivo além de apenas por linha.

### Escopo
- Módulo de execução de `external_linters` (incluindo `_run_external_linter`, também tratado no item 11)
- Parser/filtro de saída XML do Checkstyle

### Critérios de Aceite
- Linter externo configurado para modo full-file recebe o conteúdo completo do arquivo via `--input` (ou parâmetro equivalente documentado), em vez de operar apenas sobre o diff.
- Filtro de resultados do Checkstyle cruza violações reportadas usando o identificador de arquivo (caminho) além do número de linha, evitando falso positivo/negativo quando duas alterações em arquivos diferentes têm números de linha coincidentes.
- Configuração existente de `external_linters` que já funcionava em modo diff/patch continua funcionando sem regressão.
- Erros de parsing do XML do Checkstyle (arquivo malformado ou ausente) são tratados sem interromper abruptamente o fluxo do GitPR.

### Casos de Teste
- Unitário: linter externo em modo full-file com `--input` apontando para arquivo de teste — validar que a saída é processada corretamente.
- Unitário: saída XML do Checkstyle contendo violações em dois arquivos diferentes com números de linha coincidentes — validar que o filtro atribui corretamente cada violação ao seu arquivo de origem.
- Unitário: saída XML do Checkstyle malformada — validar tratamento de erro sem crash.
- Integração: fluxo completo de PR Publisher (relacionado ao item 2/3) usando um `external_linter` em modo full-file configurado via `--init` (item 9), validando compatibilidade ponta a ponta.
- Regressão: suíte de testes de linter existente (incluindo `test_pr_publish_linter_modal.py`) permanece passando.

### Riscos/Dependências
- Depende do hardening do item 11 estar concluído ou ser feito em conjunto, já que ambos alteram `_run_external_linter`.
- Alteração no filtro do Checkstyle pode impactar diretamente o teste manual end-to-end definido no item 2, caso o cenário de teste utilize Checkstyle como linter de referência — validar compatibilidade entre as duas tarefas.
- Templates de linter gerados pelo `--init` (item 9) devem já refletir a nova opção de modo full-file, se aplicável.

### Fora de Escopo
- Suporte a outros formatos de saída de linter além do XML do Checkstyle já mencionado.
- Adição de novos linters externos ao conjunto suportado (esta tarefa corrige o mecanismo existente, não expande a lista de integrações).

---

## Item 13 — `LINTER_PRESETS_VERSION` como marcador de versão

### Título
Documentar `LINTER_PRESETS_VERSION` como Version Marker no `.env`

### Objetivo
Formalizar `LINTER_PRESETS_VERSION` como um marcador de versão dos presets de linter no arquivo `.env`, seguindo o padrão de Version Marker já adotado pelo projeto.

### Escopo
- Arquivo `.env` (e `.env.example`, se existente)
- Documentação relacionada a versionamento de presets (ex.: `ARCHITECTURE.md` ou documento específico de configuração)
- Templates de configuração gerados pelo `--init` (item 9), garantindo que já incluam o marcador desde a primeira geração

### Critérios de Aceite
- Variável `LINTER_PRESETS_VERSION` está presente e documentada no `.env` (ou `.env.example`), seguindo o mesmo padrão formal de Version Marker usado por outros marcadores de versão do projeto.
- Documentação explica o propósito do marcador (rastrear a versão dos presets de linter em uso) e como ele deve ser incrementado quando presets forem alterados.
- Templates de configuração de linter gerados pelo comando `--init` (item 9) já incluem `LINTER_PRESETS_VERSION` com valor inicial correto.
- Nenhum outro marcador de versão existente no projeto é alterado ou duplicado incorretamente por esta mudança.

### Casos de Teste
- Manual: inspeção do `.env`/`.env.example` confirmando presença e formatação correta de `LINTER_PRESETS_VERSION`.
- Unitário: geração de configuração via `--init` — validar que o arquivo de preset de linter gerado contém o marcador de versão correto.
- Manual: revisão da documentação confirmando clareza sobre o processo de incremento do marcador.

### Riscos/Dependências
- Depende do item 9 (`--init`) para garantir que novas instalações já nasçam com o marcador correto.
- Deve ser coordenado com o item 5 (atualização de `CLAUDE.md`) para não gerar confusão entre a versão geral do GitPR (`0.0.37`) e a versão específica dos presets de linter — os dois marcadores são independentes e devem ser documentados como tal.

### Fora de Escopo
- Criação de um sistema de migração automática entre versões de presets.
- Alteração do conteúdo dos presets de linter em si (apenas o marcador de versão é tratado nesta tarefa).
