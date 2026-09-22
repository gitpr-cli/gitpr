# SPEC — GitPR Secret Scanning (preset de segurança no linter regex)

> Documento de especificação técnica para implementação via Claude Code skill.
> Escopo: estender o linter regex já existente do GitPR com um preset de segurança dedicado, capaz de detectar segredos hardcoded (chaves AWS, tokens de API de provedores comuns, senhas/credenciais em texto plano) no diff analisado, elevando o produto de "linter de estilo" para "quality + security gate".

## 0. Contexto obrigatório antes de codificar

Antes de gerar qualquer código, a skill DEVE:

1. Ler o linter regex existente na íntegra e extrair: (a) o formato exato do arquivo de configuração de regras (provavelmente `.gitpr.linter.yml` ou nome equivalente — confirmar o nome real), (b) a estrutura de uma regra individual (campos: padrão regex, severidade, mensagem, categoria, extensões/glob de arquivo aplicável), (c) como o motor decide quais arquivos processar (todo o diff, ou apenas extensões configuradas), (d) como a saída de uma violação de regra é hoje estruturada (para reaproveitar o mesmo formato de finding usado no restante do produto).
2. Confirmar que as **skills são fixas** e carregadas em `core.py` via `get_skill_context` (já confirmado nesta conversa) — isso significa que qualquer novo preset de linter deve ser registrado como um arquivo de regras adicional referenciado explicitamente no código/config, não descoberto dinamicamente por varredura de diretório. Localizar onde a lista de presets/skills fixos é declarada em `core.py` para adicionar o novo preset de segurança no mesmo padrão.
3. Verificar se o bridge para linters externos (Checkstyle/ESLint/PHPCS/Stylelint, conforme mencionado nas análises de arquitetura) já lida com algum tipo de severidade "bloqueante" que impede o fluxo de commit/PR — confirmar como esse bloqueio é hoje acionado, para que o preset de segredos possa usar exatamente o mesmo mecanismo de bloqueio quando configurado como crítico.
4. Confirmar se o motor de review de IA (semântico) já tenta identificar segredos como parte de sua análise geral — se sim, definir claramente a divisão de responsabilidade: o preset de regex deve ser a primeira linha de defesa determinística e rápida (sem custo de IA, sem chamada de rede), e não deve duplicar nem depender do review de IA para funcionar.
5. Confirmar o mecanismo de exclusão de arquivos (smart excludes) já usado no projeto, para reaproveitá-lo e garantir que arquivos de teste/fixture com segredos de exemplo propositais (comum em testes automatizados) possam ser excluídos via padrão de caminho, evitando falsos positivos constantes em código de teste legítimo.
6. Confirmar se existe algum mecanismo de supressão de regra por linha/arquivo (comentário inline tipo `# gitpr-ignore` ou equivalente) já suportado pelo linter — se existir, reaproveitar exatamente esse mecanismo para supressão de falsos positivos de segredo; se não existir, esta pode ser uma lacuna a resolver como parte desta entrega ou reportar como limitação conhecida.

Não prosseguir com a implementação sem completar os passos 1–4.

## 1. Escopo da feature

- **Objetivo:** adicionar um preset de regras (`security` ou `secrets`) ao linter regex existente, capaz de detectar categorias comuns de segredo hardcoded no diff analisado, com severidade configurável e mensagens específicas por tipo de segredo detectado.
- **Categorias mínimas de detecção nesta primeira versão:**
  - Chaves de acesso AWS (Access Key ID no padrão `AKIA[0-9A-Z]{16}` e correspondente Secret Access Key em contexto próximo).
  - Tokens de API de provedores comuns reconhecíveis por prefixo/formato (ex.: tokens GitHub `ghp_`/`gho_`/`ghs_`, tokens Slack `xox[baprs]-`, chaves de API genéricas do Google `AIza[0-9A-Za-z\-_]{35}`).
  - Padrões genéricos de credencial em atribuição de variável (ex.: `password\s*=\s*['"][^'"]{6,}['"]`, `secret\s*=\s*['"]...`, `api_key\s*=\s*['"]...`) — com filtro para reduzir falso positivo óbvio (ex.: ignorar valores que sejam claramente placeholder como `changeme`, `xxx`, `your_key_here`, `${...}`, `<...>`).
  - Blocos de chave privada (`-----BEGIN PRIVATE KEY-----`, `-----BEGIN RSA PRIVATE KEY-----` e variantes).
  - Connection strings com credenciais embutidas (ex.: `mysql://user:senha@host`, `postgres://user:senha@host`).
- **Formato do preset:** deve seguir exatamente o mesmo formato de arquivo de regras já usado pelo linter existente (YAML de regex + severidade + mensagem), como um arquivo de preset adicional, não como um motor de detecção paralelo com lógica própria de execução.
- **Ativação:** o preset de segurança deve poder ser ativado/desativado independentemente dos demais presets (estilo, convenção), via flag ou config — sugestão: `gitpr --linter security` ou uma chave em config habilitando presets múltiplos simultaneamente, seguindo a convenção já existente da flag `-l`/`--linter` confirmada no projeto.
- **Fora de escopo nesta fase:** detecção de segredos via entropia estatística (Shannon entropy) para strings aleatórias sem padrão conhecido — isso é uma técnica mais sofisticada usada por ferramentas dedicadas (Gitleaks, TruffleHog) e fica fora do escopo de um preset de regex simples nesta entrega; verificação de segredos já commitados no histórico completo do repositório (esta feature cobre apenas o diff analisado no fluxo normal do GitPR, não uma varredura retroativa de todo o histórico Git); revogação/notificação automática de segredo vazado a provedores externos.
- **Compatibilidade:** o preset de segurança deve coexistir com os presets de linter já existentes sem alterar o comportamento deles — ativá-lo é aditivo, nunca substitui ou desativa outras regras já configuradas pelo usuário.

## 2. Árvore de arquivos a criar/alterar

```
presets/linter/
└── security.yml                  # NOVO — arquivo de preset seguindo o formato já existente do linter

src/domain/linter/
└── secret_patterns.py            # NOVO (se o projeto preferir padrões centralizados em código em vez de apenas YAML) — ver decisão na seção 3

core.py                           # ALTERAR — registrar o preset "security" na lista fixa de presets/skills carregados via get_skill_context (ou mecanismo equivalente de registro de linter presets)

tests/domain/linter/
└── test_secret_patterns.py       # NOVO — testes de detecção positiva e negativa por categoria
tests/presets/
└── test_security_preset.py       # NOVO — teste de carregamento e execução do preset via motor de linter real
```

## 3. Decisão de design: regras em YAML puro vs. módulo Python auxiliar

Como o motor de linter já existente provavelmente executa regex diretamente a partir do YAML de configuração (confirmar no passo 0.1), a primeira opção é escrever `security.yml` inteiramente com os padrões regex embutidos, sem nenhum código Python novo além do registro do preset. Isso é preferível por consistência com o mecanismo existente. Um módulo Python auxiliar (`secret_patterns.py`) só deve ser criado se a lógica de filtro de falso positivo (ex.: ignorar valores placeholder) não puder ser expressa apenas com regex dentro do formato de regra já suportado pelo motor — a skill deve tentar a solução mais simples (YAML puro) primeiro e só introduzir código Python se o formato de regra existente não suportar negação/exclusão condicional.

```yaml
# presets/linter/security.yml — estrutura ilustrativa, ajustar ao formato real confirmado no passo 0.1
name: security
version: "1.0.0"
description: "Detecção de segredos hardcoded: chaves de nuvem, tokens de API, senhas e chaves privadas."
rules:
  - id: SEC-AWS-ACCESS-KEY
    pattern: "AKIA[0-9A-Z]{16}"
    severity: blocker
    category: security
    message: "Possível AWS Access Key ID hardcoded. Remova e rotacione a chave imediatamente."

  - id: SEC-GITHUB-TOKEN
    pattern: "gh[pousr]_[A-Za-z0-9]{36,}"
    severity: blocker
    category: security
    message: "Possível token do GitHub hardcoded."

  - id: SEC-SLACK-TOKEN
    pattern: "xox[baprs]-[A-Za-z0-9-]{10,}"
    severity: blocker
    category: security
    message: "Possível token do Slack hardcoded."

  - id: SEC-GOOGLE-API-KEY
    pattern: "AIza[0-9A-Za-z\\-_]{35}"
    severity: blocker
    category: security
    message: "Possível chave de API do Google hardcoded."

  - id: SEC-PRIVATE-KEY-BLOCK
    pattern: "-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"
    severity: blocker
    category: security
    message: "Bloco de chave privada detectado no diff. Nunca deve ser commitado."

  - id: SEC-DB-CONNECTION-STRING
    pattern: "(mysql|postgres|postgresql|mongodb)://[^:\\s]+:[^@\\s]+@"
    severity: critical
    category: security
    message: "Connection string com credenciais embutidas detectada."

  - id: SEC-GENERIC-CREDENTIAL-ASSIGNMENT
    pattern: "(?i)(password|senha|secret|api[_-]?key)\\s*[:=]\\s*['\"][^'\"]{6,}['\"]"
    severity: warning
    category: security
    message: "Possível credencial hardcoded em atribuição de variável. Verifique se não é um segredo real."
    exclude_values:
      - "changeme"
      - "your_key_here"
      - "xxx"
      - "placeholder"
      - "example"
```

Nota: a chave `exclude_values` só deve ser incluída se o motor de linter já existente suportar esse conceito de exclusão condicional de valor capturado; caso não suporte, documentar essa lacuna e tratar `SEC-GENERIC-CREDENTIAL-ASSIGNMENT` como `warning` (não `blocker`) justamente para compensar a maior taxa de falso positivo esperada sem esse filtro.

## 4. Integração com smart excludes e supressão

1. **Smart excludes para arquivos de teste**: confirmar (passo 0.5) o mecanismo já existente de exclusão de arquivos por padrão de caminho, e documentar explicitamente no README/config do preset que arquivos de teste/fixture (`tests/**`, `**/*fixture*`, `**/*mock*`) são candidatos naturais a exclusão configurável — mas não excluir automaticamente por padrão sem confirmação do usuário, já que segredos reais podem acidentalmente parar em arquivos de teste também.
2. **Supressão por linha**: se o motor já suporta comentário de supressão inline, documentar seu uso para o preset de segurança (ex.: `// gitpr-ignore: SEC-GENERIC-CREDENTIAL-ASSIGNMENT` ao lado de uma linha que é comprovadamente um valor de exemplo, não um segredo real). Se não existir, reportar como limitação conhecida desta entrega, sem tentar resolver a feature de supressão genérica dentro do escopo desta spec (é uma capacidade transversal ao linter, não específica do preset de segurança).

## 5. Severidade e bloqueio de fluxo

- Categorias de alta confiança e baixo risco de falso positivo (AWS, GitHub, Slack, Google API keys, blocos de chave privada) devem ser `blocker` por padrão — reaproveitando o mecanismo já existente de severidade bloqueante do linter (confirmado no passo 0.3), impedindo commit/PR até resolução ou supressão explícita.
- Connection strings com credenciais devem ser `critical` (impacto alto, mas formato menos padronizado que uma chave de API reconhecível, logo leve chance maior de captura de contexto não intencional).
- Padrão genérico de atribuição de credencial deve ser `warning` por padrão, dado o risco de falso positivo mais alto — o usuário pode elevar a severidade via config se preferir postura mais estrita.
- Toda essa configuração de severidade deve ser sobrescrevível pelo usuário no arquivo de config do projeto, seguindo o mesmo mecanismo de override já existente para as demais regras do linter (não introduzir um mecanismo de override paralelo específico para este preset).

## 6. Testes obrigatórios (critério de aceite)

1. **Teste de detecção positiva por categoria** (`test_secret_patterns.py`): para cada regra do preset, um exemplo de string que deve ser capturada (ex.: uma AWS Access Key ID sintética válida no formato, não uma chave real) deve gerar um finding com o `id` de regra correto.
2. **Teste de não-detecção (falso negativo controlado)**: strings semelhantes mas que não devem casar (ex.: uma sequência de 16 caracteres maiúsculos que não começa com `AKIA`) não devem gerar finding.
3. **Teste de filtro de placeholder**: valores na lista de exclusão (`changeme`, `xxx`, etc., se o mecanismo de exclusão for suportado) não devem gerar finding para `SEC-GENERIC-CREDENTIAL-ASSIGNMENT`; se o mecanismo não for suportado pelo motor existente, este teste deve validar que a regra está de fato configurada como `warning` (não `blocker`), documentando a limitação.
4. **Teste de carregamento do preset via motor real** (`test_security_preset.py`): o preset `security.yml` deve carregar sem erro de parsing pelo motor de linter existente, e cada regra deve ser executável contra um diff de exemplo sem exceção.
5. **Teste de coexistência com outros presets**: ativar o preset de segurança junto com um preset de estilo já existente não deve alterar o comportamento do preset de estilo, nem vice-versa — validar que os findings de cada preset aparecem de forma independente e completa.
6. **Teste de bloqueio de fluxo**: um diff contendo um finding `blocker` do preset de segurança deve acionar o mesmo mecanismo de bloqueio de commit/PR já usado por outras regras `blocker` do linter — reaproveitar o teste de bloqueio já existente, parametrizando para incluir uma regra de segurança.
7. **Teste de performance/custo**: confirmar que a execução do preset de segurança é puramente baseada em regex local, sem qualquer chamada de rede ou de IA — validar via mock que nenhum provider de IA é invocado durante a execução do linter de segurança isoladamente.
8. **Teste de mensagens específicas**: cada categoria de segredo detectada deve produzir uma mensagem de finding distinta e informativa (não uma mensagem genérica "segredo encontrado" para todas as categorias), permitindo ao desenvolvedor entender rapidamente que tipo de credencial foi exposta.

Critério de "feature completa": todos os testes acima passam; rodar o linter com o preset de segurança ativo sobre um diff de teste contendo exemplos sintéticos de cada categoria detecta corretamente todos eles com a severidade e mensagem esperadas, sem nenhuma chamada de rede/IA envolvida.

## 7. Ordem de execução recomendada

1. Confirmar o formato exato de regra do linter existente (passo 0.1) e validar, com um teste manual rápido, que uma regra simples nova carrega e executa corretamente antes de escrever o preset completo.
2. Escrever `security.yml` com as categorias mínimas listadas na seção 1, uma categoria por vez, validando cada uma isoladamente contra exemplos sintéticos antes de adicionar a próxima.
3. Implementar os testes de detecção positiva/negativa por categoria (`test_secret_patterns.py`).
4. Registrar o preset `security` no ponto de carregamento fixo de presets em `core.py` (mesmo padrão de `get_skill_context`, confirmado no passo 0.2), com a flag/config de ativação correspondente.
5. Validar coexistência com presets existentes e o mecanismo de bloqueio de severidade `blocker`.
6. Documentar a limitação de supressão/exclusão (se aplicável, conforme apurado no passo 0.6) na documentação do preset e no README.
7. Atualizar `config.schema.yml` (ou equivalente) com a chave de ativação do preset de segurança.
8. Rodar suite completa de testes do projeto antes de considerar a feature concluída, com atenção a não haver regressão nos presets de linter já existentes.

Cada etapa deve ser um commit/PR isolado e revisável. Não escrever todas as categorias de detecção em um único commit — cada categoria validada isoladamente reduz o risco de uma regex mal calibrada gerar ruído excessivo de falso positivo em produção.

## 8. Encaixe estratégico (contexto de monetização)

Classificada como Tier 2 (diferenciação e retenção, médio esforço) porque, embora seja uma extensão direta do linter regex já existente (baixo esforço de engenharia), sua importância estratégica é maior que a maioria dos itens do Tier 1: eleva a percepção do produto de "linter de estilo" para "quality + security gate", categoria em que ferramentas como Semgrep e GitGuardian cobram premium, conforme já identificado nas análises de monetização anteriores. Nesta primeira versão baseada em regex, o preset deve permanecer no tier **Free/Community** — é a prova de conceito e a porta de entrada para a categoria de segurança. A evolução natural para o tier pago é a extensão futura já mapeada separadamente: bridge SAST completo (Semgrep, Gitleaks, Bandit) com detecção por entropia e análise mais sofisticada, reservada para Pro/Team, enquanto este preset de regex simples continua gratuito como demonstração de capacidade e gerador de confiança.
