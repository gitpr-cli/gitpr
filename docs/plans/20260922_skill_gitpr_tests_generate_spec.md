# SPEC — GitPR `tests generate` (evolução versionada do `/tests` do chat)

> Documento de especificação técnica para implementação via Claude Code skill.
> Escopo: generalizar o comando `/tests` hoje disponível apenas dentro do chat interativo em um comando de CLI de primeira classe (`gitpr tests generate`), capaz de produzir arquivos de teste versionados no repositório (não apenas texto exportável manualmente), seguindo o framework de teste já detectado/configurado no projeto do usuário.

## 0. Contexto obrigatório antes de codificar

Antes de gerar qualquer código, a skill DEVE:

1. Ler a implementação exata do comando `/tests` dentro do chat (handler do slash command) e extrair: (a) como o diff/contexto é hoje passado para a IA ao acionar `/tests`, (b) o formato de saída atual (bloco de código Markdown dentro da resposta do chat, texto livre, ou já algo estruturado), (c) como o usuário hoje aproveita essa saída — se é apenas leitura na tela, ou se já existe algum caminho de exportação (o atalho `Ctrl+Shift+E`/`Ctrl+E` de "Export Msg" já identificado no chat é candidato natural a ser reaproveitado ou substituído por esta feature).
2. Confirmar a arquitetura de mensagens do chat (`ChatMessage` widgets, `_ai_msg_widgets`, navegação por foco via F7/F8, conforme já implementado) apenas na medida necessária para entender se `/tests` deve continuar existindo como está no chat (gerando uma mensagem navegável, exportável via `Ctrl+Shift+E`) enquanto o comando novo de CLI oferece um caminho paralelo mais direto — ou se a intenção é que o chat passe a chamar a mesma camada de use case do comando novo, seguindo o mesmo princípio de não-duplicação já aplicado nas specs anteriores (`gitpr fix` generalizando o auto-patch do chat).
3. Confirmar qual(is) framework(s) de teste o projeto já detecta ou assume hoje em qualquer parte do código (ex.: menções a Pest/PHPUnit para PHP, Jest/Vitest para JS/Vue, pytest para Python) — se já existe alguma lógica de detecção de stack reaproveitável (mencionada em specs anteriores desta série, ex.: detecção de `composer.json`/`package.json`/`phpunit.xml`/`pest.php`), usar exatamente essa mesma lógica em vez de reimplementar detecção de framework.
4. Confirmar a interface real de `ai_providers.py` para reaproveitar o mesmo mecanismo de chamada de IA já usado pelo `/tests` do chat e pelo restante do produto.
5. Verificar se o projeto já tem alguma convenção de nomenclatura/localização de arquivo de teste por linguagem (ex.: `tests/Feature/`, `tests/Unit/` para Laravel/Pest; `__tests__/` ou arquivo `.test.js` ao lado do componente para Vue/Jest) documentada ou inferível a partir de exemplos no próprio código do GitPR ou em specs anteriores — não impor uma convenção própria divergente da convenção do framework detectado.
6. Confirmar se `apply_fix.py`/`patch_applier.py` (spec anterior "GitPR fix Command") já foram implementados — o fluxo de escrita de arquivo de teste novo pode reaproveitar o mesmo mecanismo de dry-run/confirmação/aplicação já construído ali, em vez de implementar um terceiro caminho de escrita de arquivo com confirmação.

Não prosseguir com a implementação sem completar os passos 1–3.

## 1. Escopo da feature

- **Objetivo:** permitir `gitpr tests generate` como comando de primeira classe que, a partir do diff atual (staged/unstaged) ou de um arquivo/finding específico, gera um arquivo de teste completo no framework correto do projeto, com opção de escrever diretamente no repositório (dry-run por padrão, seguindo o mesmo princípio de segurança já estabelecido nas specs anteriores desta série).
- **Comandos/flags novos:**
  - `gitpr tests generate` (dry-run por padrão) — mostra o conteúdo do arquivo de teste proposto, sem escrever nada.
  - `gitpr tests generate --file <caminho>` — gera teste para um arquivo específico, em vez de todo o diff.
  - `gitpr tests generate --finding <id>` — gera um teste direcionado a validar a correção de um finding específico do último review (integração natural com o modelo de finding já usado por `gitpr fix`), útil para comprovar que a correção resolve o problema apontado.
  - `gitpr tests generate --apply` — escreve o arquivo de teste no caminho convencional do framework detectado, exigindo confirmação explícita antes de criar/sobrescrever qualquer arquivo.
  - `gitpr tests generate --framework <nome>` — força um framework específico, sobrepondo a detecção automática (útil em projetos poliglota ou com configuração atípica).
- **Diferença central em relação ao `/tests` do chat:** o comando novo produz um **artefato versionável e nomeado corretamente** segundo a convenção do framework (arquivo pronto para `git add`), não apenas texto exibido na tela que o usuário precisa copiar/colar e posicionar manualmente. Isso é a evolução explícita mencionada no backlog: "falta um artefato versionado".
- **Escopo de geração de conteúdo de teste:**
  - Cenários de caminho feliz (happy path) cobrindo a mudança principal do diff.
  - Cenários de borda/regressão quando identificáveis a partir do diff (validações, condições de erro introduzidas ou alteradas).
  - Para stacks conhecidas do produto (Laravel/PHP, Vue/JS), seguir convenções específicas já usadas nas análises anteriores como diferencial: testes de Feature/Unit/Policy/FormRequest para Laravel com Pest/PHPUnit; testes de componente para Vue com Jest/Vitest.
- **Fora de escopo nesta fase:** execução automática dos testes gerados (o comando gera o arquivo, não roda a suite) — isso pode ser um passo manual do usuário ou uma integração futura separada; geração de mocks/fixtures complexos de infraestrutura (ex.: containers de banco de dados de teste) — o teste gerado pode referenciar fixtures existentes do projeto, mas não cria infraestrutura de teste nova; cobertura de mutação ou métricas de qualidade do teste gerado (validação de que o teste gerado realmente falha antes da correção e passa depois é uma melhoria futura, não desta entrega).
- **Compatibilidade:** o comando `/tests` do chat deve continuar funcionando exatamente como hoje (mesma UX, mesmo atalho de exportação `Ctrl+Shift+E`/`Ctrl+E`), mas deve internamente passar a chamar a mesma camada de use case do comando novo, eliminando duplicação de lógica de prompt/geração — seguindo o mesmo princípio já aplicado na spec de `gitpr fix` em relação ao auto-patch.

## 2. Árvore de arquivos a criar/alterar

```
src/domain/tests_generation/
├── framework_detector.py         # NOVO (ou reaproveitado de detecção de stack já existente em outras specs)
├── test_scaffold_builder.py      # NOVO — monta a estrutura/convenção de nome e caminho de arquivo por framework
└── test_content_types.py          # NOVO — dataclasses de entrada/saída

src/application/use_cases/
└── generate_test_file.py          # NOVO — orquestra: resolver alvo (diff/arquivo/finding) -> detectar framework -> prompt IA -> montar arquivo -> dry-run ou escrever

src/ui/chat/                        # ALTERAR — handler de `/tests` passa a chamar generate_test_file.py internamente

core.py ou main.py                   # ALTERAR — registrar `gitpr tests generate` e subflags

tests/domain/tests_generation/
├── test_framework_detector.py
└── test_scaffold_builder.py
tests/application/use_cases/
└── test_generate_test_file.py
```

## 3. Contrato de dados (obrigatório)

```python
# src/domain/tests_generation/test_content_types.py
from dataclasses import dataclass
from enum import Enum


class TestFramework(str, Enum):
    PEST = "pest"
    PHPUNIT = "phpunit"
    JEST = "jest"
    VITEST = "vitest"
    PYTEST = "pytest"
    UNKNOWN = "unknown"


@dataclass
class TestGenerationTarget:
    """O que está sendo testado — origem única para diff completo, arquivo específico, ou finding."""
    source_type: str            # "diff" | "file" | "finding"
    file_path: str | None
    finding_id: str | None
    diff_content: str


@dataclass
class TestScaffold:
    framework: TestFramework
    target_test_path: str        # caminho final sugerido, seguindo convenção do framework detectado
    already_exists: bool          # True se um arquivo de teste já existe nesse caminho — decide entre criar vs. sugerir merge manual


@dataclass
class GeneratedTest:
    scaffold: TestScaffold
    content: str                  # código de teste completo, pronto para escrita
    covered_scenarios: list[str]   # lista curta descrevendo cada cenário coberto, para exibição no dry-run
    warnings: list[str]            # ex.: "framework não detectado com confiança, usando default X"
```

```python
# src/application/use_cases/generate_test_file.py
def generate_test_file(
    target: TestGenerationTarget,
    repo_path: str,
    ai_provider,
    framework_override: TestFramework | None = None,
    apply: bool = False,
) -> GeneratedTest:
    ...
```

## 4. Algoritmo — pipeline completo

1. **Resolver o alvo da geração** (`TestGenerationTarget`): se `--file` for informado, obter o diff daquele arquivo específico; se `--finding <id>` for informado, localizar o finding no resultado do último review (mesmo mecanismo de leitura de finding já especificado em `gitpr fix`) e usar o contexto daquele finding (arquivo, linhas, descrição do problema) como foco da geração; caso nenhuma flag seja informada, usar o diff completo staged/unstaged.
2. **Detectar o framework de teste** (`framework_detector.py`), reaproveitando a lógica de detecção de stack já existente no projeto (confirmada no passo 0.3) — verificar presença de `pest.php`/`phpunit.xml` (PHP), `jest.config.*`/`vitest.config.*` (JS/Vue), `pytest.ini`/`pyproject.toml` com seção pytest (Python). Se `--framework` for explicitamente informado, pular a detecção e usar o valor forçado.
3. **Resolver o caminho de destino do arquivo de teste** (`test_scaffold_builder.py`) seguindo a convenção específica do framework detectado (ex.: Pest/Laravel → `tests/Feature/` ou `tests/Unit/` espelhando o namespace da classe original; Jest/Vue → arquivo `.test.js`/`.spec.js` ao lado do componente ou em `__tests__/`). Verificar se já existe um arquivo de teste nesse caminho — se existir, marcar `already_exists=True` e, no modo `--apply`, exigir uma confirmação adicional específica para sobrescrita (nunca sobrescrever silenciosamente um teste já existente).
4. **Montar o prompt de geração**, incluindo: o diff/contexto do alvo, o framework detectado, a convenção de nomenclatura esperada, e instrução explícita para gerar cenários de caminho feliz e de borda/regressão relevantes ao diff — reaproveitando o mesmo mecanismo de skill/system prompt já usado pelo `/tests` do chat (não escrever um prompt divergente do zero, apenas estruturá-lo para produzir um arquivo completo em vez de um trecho solto).
5. **Chamar o provider de IA** configurado (via `ai_providers.py`) e receber o conteúdo do arquivo de teste completo.
6. **Validar sintaticamente o conteúdo gerado** antes de qualquer escrita: para PHP, validar ao menos que o arquivo é sintaticamente válido (ex.: `php -l` se disponível, reaproveitando o mesmo padrão de segurança de subprocess já estabelecido na spec do bridge SAST); para JS/TS, validação equivalente se uma ferramenta já estiver disponível no ambiente (ex.: `node --check`); para Python, `python -m py_compile`. Se a validação falhar, tratar como `EXPERIMENTAL`/baixa confiança e destacar isso claramente no dry-run, nunca escrever um arquivo com erro de sintaxe sem aviso.
7. **Modo dry-run (default):** exibir o conteúdo completo do teste gerado, o caminho de destino sugerido, e a lista de cenários cobertos — sem escrever nada.
8. **Modo `--apply`:** exigir confirmação explícita (exibindo o conteúdo e o caminho); se `already_exists=True`, exigir confirmação adicional específica de sobrescrita; escrever o arquivo no caminho resolvido.
9. **Se `--finding <id>` foi usado**, o resultado deve deixar claro na saída que aquele teste foi gerado especificamente para validar a correção daquele finding, criando um vínculo rastreável entre finding → patch (`gitpr fix`) → teste (`gitpr tests generate --finding`).

## 5. Integração com o chat existente (`/tests`)

Seguindo o mesmo princípio de não-duplicação já estabelecido na spec de `gitpr fix`: o handler de `/tests` no chat deve ser refatorado para chamar `generate_test_file.py` internamente, usando `TestGenerationTarget(source_type="diff", diff_content=<diff atual do chat>)`. A diferença de UX a preservar: dentro do chat, o resultado continua aparecendo como uma mensagem de IA navegável (`ChatMessage`, participando de `_ai_msg_widgets` e navegação F7/F8), exportável via `Ctrl+Shift+E`/`Ctrl+E` como já funciona hoje — o comando novo de CLI é um caminho de entrada adicional para o mesmo motor de geração, não uma substituição da experiência de chat. Se o usuário, dentro do chat, quiser transformar o resultado de `/tests` em um arquivo escrito de fato (não apenas exportado como texto), avaliar como melhoria futura um atalho que invoque o modo `--apply` a partir da mensagem focada — fora do escopo obrigatório desta entrega, mas compatível com a arquitetura proposta.

## 6. Config

```yaml
tests_generation:
  default_framework: null          # null = detecção automática; caso contrário força um valor de TestFramework
  validate_syntax_before_write: true
  overwrite_requires_confirmation: true   # não deve ser desabilitável via config, apenas mencionado aqui por completude/documentação
```

## 7. Testes obrigatórios (critério de aceite)

1. **Teste de detecção de framework** (`test_framework_detector.py`): cada combinação de arquivos indicadores (`pest.php`, `phpunit.xml`, `jest.config.js`, `vitest.config.ts`, `pytest.ini`) deve resolver para o `TestFramework` correto; ausência de qualquer indicador deve resolver para `UNKNOWN` sem lançar exceção, e o pipeline deve reportar isso como warning pedindo `--framework` explícito.
2. **Teste de resolução de caminho de destino** (`test_scaffold_builder.py`): para cada framework suportado, validar que o caminho de teste sugerido segue a convenção esperada (ex.: `app/Services/UserService.php` → `tests/Feature/Services/UserServiceTest.php` para Pest/Laravel, ajustando ao padrão real do projeto de referência do usuário).
3. **Teste de detecção de arquivo já existente**: se já existir um arquivo no caminho de destino resolvido, `already_exists` deve ser `True`; o modo `--apply` não deve sobrescrever sem uma segunda confirmação explícita simulada no teste.
4. **Teste de resolução por finding**: `--finding <id>` deve localizar corretamente o finding no resultado do último review e usar seu contexto (arquivo, linha, descrição) como entrada do prompt, não o diff completo.
5. **Teste de validação sintática**: um conteúdo de teste gerado sintaticamente inválido (simulado via mock da resposta de IA) deve ser marcado com warning de baixa confiança e nunca escrito automaticamente mesmo em modo `--apply`, exigindo confirmação adicional explícita reconhecendo o risco.
6. **Teste de dry-run**: `generate_test_file` com `apply=False` nunca deve escrever nenhum arquivo no working tree — validar com `git status` limpo antes/depois em teste de integração.
7. **Teste de não-duplicação de lógica**: confirmar que o handler de `/tests` no chat chama `generate_test_file.py` e não contém lógica própria de prompt/geração duplicada.
8. **Teste de regressão do chat**: o comando `/tests` deve continuar funcionando com a mesma UX (mensagem navegável, exportável via `Ctrl+Shift+E`/`Ctrl+E`) após a refatoração para usar a camada compartilhada.
9. **Teste de reuso do pipeline de IA**: validar que `generate_test_file` usa a mesma instância/factory de `ai_providers.py` já usada pelo restante do produto, sem introduzir um segundo caminho de configuração de provider.

Critério de "feature completa": todos os testes acima passam; rodar `gitpr tests generate --apply` sobre um diff de teste conhecido cria um arquivo de teste sintaticamente válido no caminho correto da convenção do framework detectado; o comando `/tests` do chat continua funcionando sem alteração perceptível de UX.

## 8. Ordem de execução recomendada

1. Implementar `framework_detector.py` reaproveitando (ou extraindo para reuso comum) a lógica de detecção de stack já existente em outras partes do produto — testável isoladamente contra fixtures de estrutura de projeto.
2. Implementar `test_scaffold_builder.py` (lógica pura de convenção de nome/caminho por framework) com testes cobrindo cada framework suportado.
3. Investigar e documentar o comportamento atual exato do `/tests` no chat (prompt usado, formato de saída) antes de escrever o novo pipeline de geração — para garantir que o novo prompt estruturado produza qualidade equivalente ou superior à experiência já validada no chat.
4. Implementar `generate_test_file.py` conectando resolução de alvo + detecção de framework + scaffold + chamada de IA + validação sintática, em modo dry-run apenas nesta etapa.
5. Implementar a escrita real (`--apply`) com as confirmações exigidas (arquivo novo vs. sobrescrita).
6. Implementar a resolução por `--finding <id>`, integrando com o modelo de finding já usado por `gitpr fix`.
7. Registrar `gitpr tests generate` e subflags em `core.py`/CLI.
8. Refatorar o handler de `/tests` no chat para chamar a camada compartilhada, validando que a UX do chat não regride (teste manual + teste automatizado de regressão).
9. Atualizar `config.schema.yml` e documentação (README/CLI help).
10. Rodar suite completa de testes do projeto antes de considerar a feature concluída.

Cada etapa deve ser um commit/PR isolado e revisável. A refatoração do `/tests` no chat (etapa 8) deve vir por último, depois que toda a lógica compartilhada já estiver testada isoladamente, seguindo o mesmo cuidado de minimização de risco já aplicado na spec de `gitpr fix` para uma feature que os usuários já usam hoje.

## 9. Encaixe estratégico (contexto de monetização)

Classificada como Tier 2 (diferenciação e retenção, médio esforço) porque, embora reaproveite o motor de IA e o `/tests` já existentes, exige trabalho novo real de detecção de framework, resolução de convenção de caminho por stack, e validação sintática — mais esforço que uma simples generalização de comando já mapeado no Tier 1. Fica no tier **Free/Community** como recurso de produtividade individual: reduz a segunda objeção de compra mais comum contra ferramentas de review de IA (depois de "só aponta problemas, não corrige", vem "não gera evidência de que a correção realmente funciona"). A integração com `--finding <id>` cria uma cadeia de valor rastreável (finding → fix → teste) que reforça a narrativa de "quality gate completo" já usada nas análises de monetização anteriores, e serve de base para a feature futura de "test impact analysis" (Tier 2/3 em análises anteriores) sem exigir retrabalho desta camada.
