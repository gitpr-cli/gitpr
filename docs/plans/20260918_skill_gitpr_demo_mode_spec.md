# SPEC — GitPR `demo` Mode (tour guiado sem API key)

> Documento de especificação técnica para implementação via Claude Code skill.
> Escopo: criar um modo `gitpr demo` que executa um tour guiado usando um diff de exemplo embutido no próprio pacote, sem exigir PAT/API key de IA nem repositório Git real do usuário, com objetivo de reduzir o time-to-value do primeiro contato a segundos.

## 0. Contexto obrigatório antes de codificar

Antes de gerar qualquer código, a skill DEVE:

1. Confirmar que o projeto usa **Textual** como framework de TUI (já usado nas TUIs existentes: PR Publisher, Issue, Chat, Metrics Dashboard, Linter) e ler ao menos uma dessas TUIs existentes por completo para entender: (a) padrão de composição de widgets/screens já adotado, (b) convenção de navegação (teclas, footer de atalhos), (c) tema/CSS (Textual CSS) já usado, para que o modo demo seja visualmente consistente com o restante do produto, não uma tela isolada com estilo próprio.
2. Ler `main.py`/`core.py` para confirmar como os comandos hoje são registrados e roteados (parser de argumentos, subcomandos), de forma a inserir `gitpr demo` seguindo exatamente a mesma convenção — não criar um mecanismo de parsing paralelo.
3. Confirmar a interface real de `ai_providers.py` (Strategy Pattern) para identificar o ponto exato onde o provider de IA é resolvido/chamado no fluxo normal de commit/review/PR — o modo demo precisa **substituir** essa resolução por respostas pré-gravadas (fixtures), sem tocar em rede, então é necessário saber exatamente onde interceptar essa chamada sem duplicar o restante do pipeline (linter, skills, formatação de saída).
4. Verificar se o projeto já tem algum mecanismo de fixtures/mocks para testes (provavelmente sim, dado os 264 cenários de teste) — reaproveitar o mesmo estilo de fixture de diff/resposta de IA já usado em testes, em vez de criar um formato novo do zero.
5. Confirmar se existe hoje alguma flag global de "modo offline" ou "sem rede" mencionada em análises anteriores da arquitetura — se existir, o modo demo deve reaproveitar essa flag internamente (o demo é, por definição, 100% offline) em vez de reimplementar a lógica de bloqueio de rede.
6. Confirmar o mecanismo de detecção de primeira execução (se houver) ou se este é o primeiro ponto do produto que precisa dessa lógica — importante para decidir se `gitpr demo` deve ser sugerido automaticamente na primeira execução sem config (`gitpr` rodado pela primeira vez, sem PAT configurado).

Não prosseguir com a implementação sem completar os passos 1–3.

## 1. Escopo da feature

- **Objetivo:** permitir que qualquer pessoa rode `gitpr demo` imediatamente após instalar o pacote (via `pip install gitpr-cli` ou binário), sem configurar API key, sem estar dentro de um repositório Git, e sem acesso à internet, e em menos de um minuto entender o que o GitPR faz através de um percurso guiado com dados de exemplo.
- **Comando novo:** `gitpr demo` com subopções mínimas:
  - `gitpr demo` (sem flags) — inicia o tour guiado completo na TUI.
  - `gitpr demo --scenario <nome>` — permite escolher entre cenários de exemplo distintos (ex.: `laravel-bug-fix`, `vue-feature`, `security-issue`), caso mais de um cenário seja incluído.
  - `gitpr demo --no-tui` — roda a demonstração em modo texto simples no terminal (sem Textual), para ambientes sem suporte a TUI interativa (ex.: CI, terminais muito limitados, gravação de GIF/asciinema para o README).
- **Percurso do tour (mínimo obrigatório):**
  1. Tela de boas-vindas explicando em 2–3 linhas o que é o GitPR e o que o tour vai mostrar.
  2. Exibição de um diff de exemplo embutido (realista, de um cenário reconhecível — ex.: correção de bug em validação de formulário).
  3. Simulação do **commit semântico gerado**: mostrar como o GitPR transformaria aquele diff em uma mensagem de commit Conventional Commits, usando uma resposta de IA pré-gravada (fixture), não uma chamada real.
  4. Simulação do **review de qualidade**: exibir 1–2 findings de exemplo (ex.: um problema de segurança, um problema de teste faltante) no mesmo formato visual usado pelo review real.
  5. Simulação da **geração de descrição de PR**: mostrar o texto de PR que seria gerado a partir do diff de exemplo.
  6. Tela final com **próximos passos**: comando exato para instalar/configurar uma API key real (`gitpr --init`), link para documentação, e sugestão de rodar `gitpr demo --scenario <outro>` se houver mais de um cenário.
- **Fora de escopo nesta fase:** telemetria de uso do demo (pode ser adicionado depois, mas não é requisito desta entrega), personalização do diff de exemplo pelo usuário (o diff é fixo/embutido, não editável nesta versão), integração com o MCP server durante o demo.
- **Compatibilidade:** o modo demo não deve, sob nenhuma circunstância, fazer chamadas de rede (nem para provider de IA, nem para verificação de atualização, nem para qualquer telemetria) — deve funcionar 100% com o pacote instalado, sem internet. Não deve exigir `git init` nem estar dentro de um repositório Git válido.

## 2. Árvore de arquivos a criar/alterar

```
src/demo/
├── __init__.py
├── fixtures/
│   ├── scenario_laravel_bug_fix.json      # diff de exemplo + respostas de IA pré-gravadas
│   ├── scenario_vue_feature.json          # (opcional, se mais de 1 cenário for incluído nesta fase)
│   └── scenario_security_issue.json       # (opcional)
├── demo_runner.py                          # NOVO — orquestra o percurso do tour, independente de TUI ou texto simples
└── fake_ai_provider.py                     # NOVO — implementa a mesma interface de ai_providers.py, mas retorna respostas das fixtures sem rede

src/ui/demo/
├── demo_app.py                             # NOVO — Textual App/Screen do tour guiado
└── demo_screens.py                         # NOVO — telas individuais do percurso (boas-vindas, diff, commit, review, PR, final)

core.py ou main.py                           # ALTERAR — registrar subcomando `gitpr demo`

tests/demo/
├── test_demo_runner.py
└── test_fake_ai_provider.py
```

## 3. Contrato de dados (obrigatório)

```python
# src/demo/fake_ai_provider.py — deve implementar a MESMA interface de ai_providers.py
from dataclasses import dataclass


@dataclass
class DemoScenario:
    name: str                      # ex.: "laravel-bug-fix"
    title: str                     # título amigável exibido na seleção de cenário
    description: str               # 1 linha, exibida na tela de boas-vindas
    diff: str                      # diff unificado, realista, embutido como string/arquivo
    fixed_commit_message: str       # resposta pré-gravada, no formato Conventional Commits
    fixed_review_findings: list["FixedFinding"]
    fixed_pr_title: str
    fixed_pr_description: str


@dataclass
class FixedFinding:
    severity: str
    category: str
    file_path: str
    line_start: int
    line_end: int
    message: str
    suggestion: str
```

```python
# src/demo/demo_runner.py
from dataclasses import dataclass
from enum import Enum


class DemoStep(str, Enum):
    WELCOME = "welcome"
    SHOW_DIFF = "show_diff"
    COMMIT_GENERATION = "commit_generation"
    QUALITY_REVIEW = "quality_review"
    PR_GENERATION = "pr_generation"
    NEXT_STEPS = "next_steps"


@dataclass
class DemoState:
    scenario: DemoScenario
    current_step: DemoStep
    completed_steps: list[DemoStep]


def run_demo(scenario_name: str | None = None, tui: bool = True) -> None:
    """
    Ponto de entrada único chamado por `gitpr demo`.
    Carrega o cenário (default: o primeiro disponível se scenario_name for None),
    e delega para a Textual App (tui=True) ou para o percurso em texto simples (tui=False).
    NUNCA deve instanciar um provider de IA real nem abrir socket de rede.
    """
```

## 4. `FakeAIProvider` — ponto crítico de design

Este é o componente que garante o "zero configuração, zero rede":

```python
# src/demo/fake_ai_provider.py
class FakeAIProvider:
    """
    Implementa a MESMA interface abstrata usada por GeminiProvider/DeepSeekProvider/OllamaProvider
    em ai_providers.py (confirmar assinatura exata no passo 0.3 antes de implementar).
    Toda chamada de geração retorna instantaneamente uma resposta pré-gravada da fixture do
    cenário ativo, ignorando o conteúdo real do prompt recebido (o prompt é descartado,
    apenas o tipo de operação solicitada — commit, review, pr — importa para decidir
    qual campo da fixture retornar).
    """

    def __init__(self, scenario: DemoScenario):
        self.scenario = scenario

    def generate_commit_message(self, diff: str, **kwargs) -> str:
        return self.scenario.fixed_commit_message

    def generate_review(self, diff: str, **kwargs) -> list[FixedFinding]:
        return self.scenario.fixed_review_findings

    def generate_pr_description(self, diff: str, **kwargs) -> tuple[str, str]:
        return self.scenario.fixed_pr_title, self.scenario.fixed_pr_description
```

Requisito arquitetural: `FakeAIProvider` deve satisfazer o mesmo contrato/interface abstrata que os providers reais implementam em `ai_providers.py` (o mesmo Strategy Pattern usado no restante do produto e já reaproveitado nas specs anteriores de multi-forge e release notes). Isso permite que o restante do pipeline de renderização (formatação de commit, exibição de findings, montagem de PR) seja **exatamente o mesmo código usado em produção** — o demo não deve duplicar lógica de apresentação, apenas trocar a fonte dos dados.

## 5. Integração com a TUI existente (Textual)

Requisitos de reuso:

- As telas do demo (`demo_screens.py`) devem herdar/compor os mesmos widgets Textual já usados nas TUIs existentes (ex.: o widget que já exibe diff com syntax highlight no Linter TUI ou no PR Publisher, o widget que já exibe findings de review) — não recriar componentes visuais que já existem.
- O footer de atalhos (navegação entre telas do tour: avançar, voltar, sair) deve seguir a mesma convenção de teclas já usada nas outras TUIs do projeto (confirmar convenção exata no passo 0.1).
- Se o projeto já tiver um tema/CSS Textual centralizado, o demo deve importá-lo, não definir cores/estilos próprios.

```python
# src/ui/demo/demo_app.py
from textual.app import App
from textual.screen import Screen
# reaproveitar widgets já existentes de outras TUIs, ex.:
# from src.ui.pr_publisher.widgets import DiffViewer, FindingsList

class DemoApp(App):
    """
    App Textual dedicada ao tour guiado. Navegação linear (avançar/voltar)
    entre as telas definidas em DemoStep, usando os componentes visuais
    já existentes no restante do produto.
    """
    def __init__(self, scenario: DemoScenario):
        super().__init__()
        self.scenario = scenario
        self.state = DemoState(scenario=scenario, current_step=DemoStep.WELCOME, completed_steps=[])
```

## 6. Modo `--no-tui` (texto simples)

Requisito: mesmo percurso e mesmo conteúdo do tour, mas impresso sequencialmente no terminal (sem Textual), pensado para:
- Ambientes sem suporte a TUI interativa.
- Gravação determinística de GIFs/asciinema para README (citado como ação de marketing de baixo custo nas análises de monetização) — a saída em texto simples é mais fácil de gravar de forma reprodutível que uma TUI interativa.
- CI/smoke test do próprio demo (ver seção de testes).

```python
def run_demo_text_mode(scenario: DemoScenario) -> None:
    """Imprime cada etapa do tour sequencialmente, com pausas/prompts 'pressione Enter para continuar'
    quando rodando em terminal interativo, ou sem pausas quando stdin não é um TTY (uso em CI/gravação)."""
```

## 7. Empacotamento das fixtures

- As fixtures (`scenario_*.json` ou `.py`) devem ser embutidas no pacote distribuído (incluídas no `MANIFEST.in`/`pyproject.toml` como `package_data`, conforme mecanismo já usado pelo projeto para outros assets, se houver) — confirmar que o build PyInstaller e o pacote PyPI já existentes incluem corretamente arquivos de dados não-`.py`, testando isso explicitamente (é um erro comum de empacotamento).
- O diff de exemplo deve ser realista mas curto o suficiente para caber em uma tela sem scroll excessivo — sugestão: um cenário de correção de bug de validação (ex.: Laravel `FormRequest` sem regra de validação, já que é um nicho de autoridade do produto segundo as análises anteriores), entre 15–40 linhas de diff.

## 8. Detecção de primeiro uso (opcional, mas recomendado)

Se o passo 0.6 confirmar que não existe ainda nenhuma lógica de "primeira execução", avaliar (não implementar sem confirmar com o usuário) uma sugestão simples: se `gitpr` for executado sem nenhuma configuração de API key/PAT presente, exibir uma linha sugerindo `gitpr demo` como próximo passo, em vez de apenas retornar erro de configuração ausente. Esta é uma melhoria de UX de baixo risco, mas deve ser tratada como item separado do escopo principal desta spec — implementar apenas se o tempo permitir, sem bloquear a entrega do comando `gitpr demo` em si.

## 9. Testes obrigatórios (critério de aceite)

1. **Teste de isolamento de rede**: rodar `run_demo()` (ambos os modos, TUI e texto) em um ambiente com rede completamente bloqueada (mock/monkeypatch de `requests`/`socket` lançando exceção se qualquer chamada de rede for tentada) deve completar sem erro — qualquer chamada de rede detectada deve falhar o teste.
2. **Teste de independência de repositório Git**: rodar `gitpr demo` em um diretório que não é um repositório Git (sem `.git`) deve funcionar normalmente, sem tentar `git status`/`git diff` reais.
3. **Teste de independência de configuração**: rodar `gitpr demo` sem nenhuma API key configurada (nenhuma variável de ambiente, nenhum arquivo de config) deve funcionar normalmente.
4. **Teste de contrato do `FakeAIProvider`**: verificar que `FakeAIProvider` implementa a mesma interface abstrata que os providers reais de `ai_providers.py` (reaproveitar o teste de contrato já especificado para providers reais, se existir, parametrizando para incluir o fake).
5. **Teste de cada etapa do tour** (`test_demo_runner.py`): validar que o `DemoState` avança corretamente pela sequência de `DemoStep`, que cada etapa expõe o conteúdo esperado da fixture correspondente, e que navegar "voltar" retorna à etapa anterior sem perder o estado do cenário.
6. **Teste do modo `--no-tui`**: capturar stdout do modo texto simples e validar que todas as seções obrigatórias do percurso (boas-vindas, diff, commit, review, PR, próximos passos) aparecem na saída, em ordem.
7. **Teste de múltiplos cenários** (se mais de um for incluído): `--scenario <nome>` inválido deve listar os cenários disponíveis com mensagem clara, não lançar exceção genérica.
8. **Teste de empacotamento**: validar (idealmente via teste de build/CI, não apenas unitário) que as fixtures embutidas são de fato incluídas no pacote instalável (rodar `pip install` do pacote buildado em ambiente limpo e confirmar que `gitpr demo` funciona sem os arquivos-fonte do repositório presentes).

Critério de "feature completa": todos os testes acima passam; `gitpr demo` funciona em uma máquina limpa, recém-instalada, sem qualquer configuração prévia, sem repositório Git, e sem conexão de rede, do início ao fim do tour, em menos de um minuto de interação.

## 10. Ordem de execução recomendada

1. Definir e escrever a fixture do primeiro cenário (`scenario_laravel_bug_fix.json` ou equivalente) — conteúdo estático, sem código ainda. Validar manualmente que o diff e as respostas pré-gravadas são realistas e representam bem o produto.
2. Implementar `FakeAIProvider` confirmando que satisfaz a interface real de `ai_providers.py` (teste de contrato deve passar antes de seguir).
3. Implementar `demo_runner.py` com a lógica de estados (`DemoState`/`DemoStep`), sem UI ainda — testável isoladamente.
4. Implementar `run_demo_text_mode` (modo `--no-tui`) — é o caminho mais simples e serve como validação end-to-end rápida do conteúdo antes de investir na TUI.
5. Implementar `demo_app.py`/`demo_screens.py` reaproveitando widgets Textual já existentes no projeto.
6. Registrar o comando `gitpr demo` em `core.py`/CLI com as subflags (`--scenario`, `--no-tui`).
7. Validar empacotamento (fixtures incluídas no build PyPI/PyInstaller) — testar instalação limpa em ambiente isolado.
8. (Opcional) Implementar a sugestão de `gitpr demo` na primeira execução sem config, se o tempo permitir.
9. Gravar o GIF/asciinema do modo `--no-tui` ou da TUI para uso no README (ação de marketing recomendada nas análises anteriores, mas execução manual, fora do escopo de código desta spec).
10. Rodar suite completa de testes do projeto antes de considerar a feature concluída.

Cada etapa deve ser um commit/PR isolado e revisável. O modo texto simples (etapa 4) deve vir antes da TUI (etapa 5) porque valida o conteúdo e a lógica de estado com muito menos esforço de implementação, reduzindo retrabalho na camada visual.

## 11. Encaixe estratégico (contexto de monetização)

Classificada como Tier 1 (alto impacto, baixo esforço) porque não depende de nenhuma infraestrutura nova além de fixtures estáticas e reuso de componentes visuais já existentes — é puramente sobre reduzir fricção de adoção. Fica no tier **Free/Community**, sem ambiguidade: é a porta de entrada do produto, o primeiro contato de qualquer novo usuário, e sua função é exclusivamente de aquisição, não de retenção paga. O impacto comercial é indireto mas relevante: todas as análises de monetização anteriores identificaram a fricção de "precisar de API key no primeiro uso" como o principal filtro que afasta usuários casuais antes mesmo de eles verem o valor do produto — `gitpr demo` remove esse filtro completamente, aumentando o topo do funil que eventualmente converte para os tiers pagos (Pro/Team) mapeados nas specs anteriores.

## 12. Documentação

1. Crie a sua documentação própria em docs/
2. Adicione em README.md e em suas versões em outros idiomas
3. Se alguma variável ambiente foi criada e utilizada nesta feature adicionar na interface de Configuração na seção nova Demo 