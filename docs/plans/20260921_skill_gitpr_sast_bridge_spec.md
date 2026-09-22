# SPEC — GitPR SAST Bridge (Semgrep, Gitleaks, Bandit)

> Documento de especificação técnica para implementação via Claude Code skill.
> Escopo: estender o padrão de bridge para linter externo já implementado (Checkstyle/ESLint/PHPCS/Stylelint) para suportar ferramentas de SAST (Static Application Security Testing) dedicadas — Semgrep, Gitleaks e Bandit — normalizando a saída de cada uma no mesmo modelo de finding já usado pelo restante do produto.

## 0. Contexto obrigatório antes de codificar

Antes de gerar qualquer código, a skill DEVE:

1. Ler a implementação completa do bridge de linter externo já existente (Checkstyle e os demais bridges de ESLint/PHPCS/Stylelint, conforme mencionado nas análises de arquitetura) e extrair: (a) a interface/classe base que cada bridge implementa (se já existe uma abstração comum, ou se cada bridge é uma função isolada), (b) como o bridge invoca o processo externo (via `subprocess.run`, `subprocess.Popen`, com quais argumentos de segurança já aplicados — timeout, shell=False, captura de stdout/stderr), (c) como a saída de cada ferramenta externa (que tem formato próprio) é hoje convertida para o modelo de finding interno do GitPR.
2. Ler especificamente o trabalho já existente ou planejado de **"hardening de subprocesso"** e **"external_linters full-file"** (já identificados como itens de backlog relacionados entre si no projeto) antes de escrever qualquer chamada nova de subprocess — esta spec deve seguir exatamente as mesmas práticas de segurança já estabelecidas ou em desenvolvimento nesse hardening (timeout obrigatório, validação de binário antes da execução, `shell=False`, sanitização de paths passados como argumento), não introduzir um terceiro padrão de execução de processo externo divergente.
3. Confirmar se o bridge existente já lida com a ausência do binário externo instalado (ex.: ESLint não instalado no PATH) de forma graciosa (aviso não-fatal, não exceção) — o mesmo comportamento é obrigatório para Semgrep/Gitleaks/Bandit, já que nenhum deles deve ser uma dependência obrigatória do GitPR.
4. Confirmar o modelo de finding interno usado pelo restante do produto (severidade, categoria, arquivo, linha, mensagem, fonte) para que a normalização de saída de cada ferramenta SAST mapeie exatamente para esse mesmo contrato, sem introduzir um segundo formato de finding específico para SAST.
5. Verificar se o preset de segurança baseado em regex (spec anterior, "Secret Scanning") já foi implementado — se sim, definir claramente a divisão de responsabilidade entre o preset de regex (rápido, sem dependência externa, primeira linha de defesa) e o Gitleaks via bridge SAST (mais completo, detecção por entropia, mas dependente de binário externo instalado) para evitar sobreposição confusa de findings duplicados sobre o mesmo segredo.
6. Confirmar se o motor de linter já tem algum mecanismo de execução condicional por linguagem/stack detectada no repositório (ex.: só rodar PHPCS se houver `composer.json`) — reaproveitar essa mesma lógica de detecção para decidir quando rodar Bandit (projetos Python) vs. Semgrep (multi-linguagem) vs. Gitleaks (sempre aplicável, independe de linguagem).

Não prosseguir com a implementação sem completar os passos 1–4.

## 1. Escopo da feature

- **Objetivo:** adicionar três novos bridges de ferramenta externa ao mecanismo já existente, cada um focado em uma responsabilidade de segurança específica:
  - **Semgrep**: SAST multi-linguagem baseado em regras (padrões de vulnerabilidade conhecidos: SQL injection, XSS, uso inseguro de criptografia, etc.).
  - **Gitleaks**: detecção de segredos com suporte a entropia estatística (complementa o preset de regex já especificado, cobrindo o caso de segredos sem padrão de prefixo conhecido).
  - **Bandit**: SAST específico para Python (uso inseguro de `eval`, `pickle`, `subprocess` com shell=True, etc.) — relevante mesmo o GitPR sendo majoritariamente usado em projetos PHP/JS/Vue, pois o próprio GitPR e outros projetos Python do usuário podem se beneficiar.
- **Modo de operação:** cada bridge deve poder ser habilitado/desabilitado independentemente, e a execução deve ser condicionada à presença do binário no PATH do sistema — se ausente, gerar um aviso não-fatal orientando a instalação, nunca falhar o fluxo principal do GitPR.
- **Escopo de análise:** assim como o bridge Checkstyle existente, a execução deve poder operar em modo "diff-only" (analisar apenas os arquivos/trechos alterados) quando a ferramenta suportar esse filtro nativamente, ou em modo "full-file" (analisar o arquivo inteiro, mesmo que só uma parte tenha mudado) quando a ferramenta exigir contexto completo do arquivo para funcionar corretamente — confirmar no passo 0.1 qual modo o bridge Checkstyle já usa e replicar a mesma decisão de design para consistência, a menos que a ferramenta específica exija o contrário (Semgrep e Bandit tipicamente precisam do arquivo completo para análise de fluxo de dados; Gitleaks pode operar sobre o diff).
- **Fora de escopo nesta fase:** instalação automática dos binários externos (Semgrep, Gitleaks, Bandit) pelo GitPR — a responsabilidade de ter a ferramenta instalada é do usuário/ambiente, documentada claramente; customização de regras próprias do Semgrep (regras `.semgrep.yml` customizadas) além do conjunto de regras padrão da ferramenta — usar o ruleset default/recomendado da ferramenta nesta primeira versão; execução distribuída/paralela dos três bridges simultaneamente (podem rodar sequencialmente nesta versão, otimização de paralelismo é melhoria futura).
- **Compatibilidade:** a introdução destes bridges não deve alterar o comportamento do bridge Checkstyle/ESLint/PHPCS/Stylelint já existente — devem compartilhar a mesma infraestrutura de execução segura de subprocess, mas cada bridge permanece independente e opcional.

## 2. Árvore de arquivos a criar/alterar

```
src/infrastructure/linter/external/
├── base_bridge.py                # CONFIRMAR/EXTRAIR — interface comum já existente ou a ser extraída do bridge Checkstyle atual
├── checkstyle_bridge.py          # EXISTENTE — não alterar comportamento, apenas confirmar que implementa base_bridge
├── semgrep_bridge.py              # NOVO
├── gitleaks_bridge.py             # NOVO
└── bandit_bridge.py               # NOVO

src/domain/linter/
└── sast_finding_mapper.py         # NOVO — normaliza a saída específica de cada ferramenta para o modelo de finding interno

core.py                            # ALTERAR — registrar os três novos bridges na lista de linters externos disponíveis, seguindo o mesmo padrão de ativação por flag/config já usado para os bridges existentes

tests/infrastructure/linter/external/
├── test_semgrep_bridge.py
├── test_gitleaks_bridge.py
└── test_bandit_bridge.py
tests/domain/linter/
└── test_sast_finding_mapper.py
```

## 3. Contrato — reaproveitar a interface já existente

```python
# src/infrastructure/linter/external/base_bridge.py
# Esta interface deve ser CONFIRMADA contra o bridge Checkstyle real (passo 0.1),
# não redefinida do zero. O código abaixo é a expectativa mínima, a ajustar
# conforme a assinatura real encontrada no projeto.

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ExternalLinterResult:
    tool_name: str
    available: bool             # False se o binário não foi encontrado no PATH
    findings: list["NormalizedFinding"]
    raw_output: str              # saída bruta da ferramenta, para debug
    exit_code: int | None
    warnings: list[str]          # ex.: "binário não encontrado", "timeout atingido"


@dataclass
class NormalizedFinding:
    """Deve corresponder EXATAMENTE ao modelo de finding interno já usado
    pelo restante do produto — confirmar campos reais no passo 0.4."""
    severity: str
    category: str
    file_path: str
    line_start: int
    line_end: int
    message: str
    source: str                  # "semgrep" | "gitleaks" | "bandit"
    rule_id: str | None           # id da regra da ferramenta externa, quando disponível


class ExternalLinterBridge(ABC):
    tool_name: str
    binary_name: str              # nome do executável esperado no PATH, ex.: "semgrep"

    @abstractmethod
    def is_available(self) -> bool:
        """Verifica presença do binário no PATH sem executá-lo com argumentos reais."""
        ...

    @abstractmethod
    def run(self, target_files: list[str], repo_path: str, diff_only: bool) -> ExternalLinterResult:
        ...

    @abstractmethod
    def parse_output(self, raw_output: str) -> list[NormalizedFinding]:
        ...
```

## 4. Requisitos de segurança de execução (obrigatórios, sem exceção)

Estes requisitos devem seguir exatamente o padrão já estabelecido (ou em desenvolvimento) pelo hardening de subprocesso do projeto — não são uma proposta nova, são a aplicação do padrão existente aos três bridges novos:

1. **Nunca usar `shell=True`** em nenhuma chamada de subprocess.
2. **Timeout obrigatório** em toda execução (valor configurável, default sugerido: 60 segundos por ferramenta — ferramentas SAST podem ser mais lentas que linters de estilo simples).
3. **Validar o binário antes de executar**: usar `shutil.which(binary_name)` (ou equivalente já usado no projeto) para confirmar existência antes de qualquer `subprocess.run`, evitando exceções não tratadas de "arquivo não encontrado".
4. **Sanitizar paths de arquivo** passados como argumento — nunca interpolar diretamente input do usuário/nome de arquivo em uma string de comando; usar sempre lista de argumentos (`subprocess.run([binary, "arg1", "arg2"], ...)`, nunca string concatenada).
5. **Capturar stdout/stderr separadamente**, nunca descartar stderr silenciosamente — erros de execução da ferramenta externa (ex.: Semgrep com ruleset inválido) devem aparecer como warning informativo, não desaparecer.
6. **Limitar working directory** da execução ao `repo_path` do projeto analisado — nunca permitir que a ferramenta externa opere fora do repositório sendo analisado.
7. **Nunca executar com privilégios elevados** nem propagar variáveis de ambiente sensíveis (chaves de API do GitPR) para o processo filho, a menos que estritamente necessário — passar apenas o ambiente mínimo necessário.

## 5. Especificação por ferramenta

### 5.1 Semgrep
| Campo | Valor |
|---|---|
| `binary_name` | `semgrep` |
| Comando de execução | `semgrep --config auto --json --timeout <N> <arquivo_ou_diretório>` |
| Modo de análise | full-file (Semgrep precisa do arquivo completo para análise de fluxo de dados corretamente) |
| Formato de saída | JSON — parsear campo `results[]`, cada item com `check_id`, `path`, `start.line`, `end.line`, `extra.message`, `extra.severity` |
| Mapeamento de severidade | Semgrep usa `ERROR`/`WARNING`/`INFO` — mapear para o esquema interno (`ERROR` → `critical` ou `blocker` conforme regra, `WARNING` → `warning`, `INFO` → `info`) |
| Detecção de disponibilidade | `is_available()` via `shutil.which("semgrep")` |

### 5.2 Gitleaks
| Campo | Valor |
|---|---|
| `binary_name` | `gitleaks` |
| Comando de execução | `gitleaks detect --source <repo_path> --report-format json --report-path <arquivo_temp> --no-git` (usar `--no-git` e apontar para os arquivos do diff quando se quiser escopo limitado, ou considerar `gitleaks protect --staged` para escopo de pre-commit, conforme o modo de invocação do GitPR — confirmar qual subcomando do Gitleaks se encaixa melhor no fluxo diff-only do produto) |
| Modo de análise | diff-only preferencialmente, usando o subcomando/flags do Gitleaks voltados a arquivos staged/diff, evitando escanear o histórico completo do repositório nesta integração (a varredura de histórico completo é fora de escopo, conforme seção 1) |
| Formato de saída | JSON — cada finding com `RuleID`, `File`, `StartLine`, `EndLine`, `Description`, `Secret` (nunca logar o valor de `Secret` em texto pleno nos logs do GitPR — mascarar antes de qualquer output/telemetria) |
| Mapeamento de severidade | Gitleaks não retorna severidade nativa — mapear todos os findings como `blocker` por padrão, já que qualquer segredo detectado é crítico por definição |
| Detecção de disponibilidade | `is_available()` via `shutil.which("gitleaks")` |
| Cuidado de segurança específico | O valor do segredo capturado (`Secret`) nunca deve ser persistido em cache, telemetria, ou log de forma não mascarada — truncar/mascarar (ex.: exibir apenas os 4 primeiros caracteres seguidos de `***`) em qualquer superfície de saída |

### 5.3 Bandit
| Campo | Valor |
|---|---|
| `binary_name` | `bandit` |
| Comando de execução | `bandit -f json -r <diretório_ou_arquivo>` |
| Condição de execução | Só executar se o repositório analisado contiver arquivos `.py` no diff (reaproveitar a lógica de detecção de stack já existente no projeto, conforme passo 0.6) — não rodar Bandit em repositórios sem Python |
| Modo de análise | full-file |
| Formato de saída | JSON — parsear campo `results[]`, cada item com `test_id`, `filename`, `line_number`, `issue_text`, `issue_severity`, `issue_confidence` |
| Mapeamento de severidade | Bandit usa `HIGH`/`MEDIUM`/`LOW` combinado com `issue_confidence` — mapear `HIGH severity + HIGH confidence` para `blocker`, demais combinações para `warning`/`info` conforme matriz a definir na implementação |
| Detecção de disponibilidade | `is_available()` via `shutil.which("bandit")` |

## 6. Normalização e deduplicação com o preset de regex existente

Se o preset de regex de secret scanning (spec anterior) já estiver implementado, e Gitleaks estiver disponível no ambiente, ambos podem detectar o mesmo segredo (ex.: uma chave AWS). Implementar deduplicação simples por `(file_path, line_start, categoria_normalizada)`: se o preset de regex e o Gitleaks reportarem essencialmente o mesmo achado na mesma linha, exibir apenas uma vez, preferindo a fonte mais específica (Gitleaks, por ter contexto de entropia, é considerado mais confiável quando ambos concordam) mas mencionando na mensagem que múltiplas fontes confirmaram o achado (aumenta a confiança do finding para o usuário).

## 7. Config

```yaml
linter:
  external:
    semgrep:
      enabled: false             # opt-in explícito, requer binário instalado
      timeout_seconds: 60
    gitleaks:
      enabled: false
      timeout_seconds: 30
    bandit:
      enabled: false
      timeout_seconds: 45
      only_if_python_detected: true
```

Todos os três bridges devem ser **opt-in** (`enabled: false` por padrão), diferente do preset de regex de secret scanning (que pode ser ativado por padrão por não depender de binário externo) — a diferença de comportamento default é intencional: uma dependência de ferramenta externa não deve criar fricção de instalação para quem nunca configurou nada.

## 8. Testes obrigatórios (critério de aceite)

1. **Teste de disponibilidade**: `is_available()` de cada bridge deve retornar `False` de forma limpa (sem exceção) quando o binário não estiver no PATH, e o fluxo principal do linter deve continuar normalmente com um warning, não uma falha.
2. **Teste de parsing de saída** (`test_sast_finding_mapper.py` + testes por bridge): usando exemplos fixos de saída JSON real de cada ferramenta (capturados manualmente uma vez e salvos como fixture, não gerados executando a ferramenta em CI), validar que o parsing produz `NormalizedFinding`s corretos, incluindo o mapeamento de severidade.
3. **Teste de segurança de subprocess**: verificar, para cada bridge, que a chamada usa lista de argumentos (não string), `shell=False`, timeout definido, e que um path de arquivo malicioso simulado (ex.: contendo `; rm -rf` como parte do nome, em teste controlado) não resulta em execução de comando injetado — validar via mock de `subprocess.run` capturando os argumentos exatos passados.
4. **Teste de mascaramento de segredo (Gitleaks)**: o valor de `Secret` retornado pela ferramenta nunca deve aparecer em texto pleno em nenhuma saída do `NormalizedFinding.message` ou em qualquer log — validar isso explicitamente com um segredo sintético de teste.
5. **Teste de timeout**: simular uma execução que excede o timeout configurado e confirmar que o bridge retorna `ExternalLinterResult` com warning apropriado, sem travar o fluxo principal do GitPR indefinidamente.
6. **Teste de condição de execução do Bandit**: repositório sem arquivos `.py` no diff não deve acionar a execução do Bandit (validar via mock que `subprocess.run` não foi chamado nesse cenário).
7. **Teste de deduplicação** (se o preset de regex já existir): cenário com achado duplicado entre preset de regex e Gitleaks deve resultar em um único finding exibido, com indicação de múltiplas fontes.
8. **Teste de não-regressão dos bridges existentes**: toda a suíte de testes já existente para Checkstyle/ESLint/PHPCS/Stylelint deve continuar passando sem alteração após a extração/confirmação da interface `ExternalLinterBridge` comum.
9. **Teste de opt-in**: com a configuração default (todos os três bridges `enabled: false`), nenhum dos três deve ser executado durante um fluxo normal de linter — validar via mock que nenhuma chamada de subprocess para semgrep/gitleaks/bandit ocorre.

Critério de "feature completa": todos os testes acima passam; em um ambiente com os três binários instalados, ativar os três bridges via config detecta corretamente exemplos sintéticos de vulnerabilidade (Semgrep), segredo (Gitleaks) e uso inseguro de API Python (Bandit) em um repositório de teste, sem qualquer risco de execução de comando não sanitizado.

## 9. Ordem de execução recomendada

1. Confirmar/extrair a interface `ExternalLinterBridge` comum a partir do bridge Checkstyle real (passo 0.1) — se o bridge existente não tiver uma interface abstrata formal, esta extração deve ser feita com cuidado para não alterar o comportamento observável do Checkstyle/ESLint/PHPCS/Stylelint já em produção, validado por sua suíte de testes existente antes de prosseguir.
2. Implementar `gitleaks_bridge.py` primeiro (ferramenta mais simples de invocar e já parcialmente coberta conceitualmente pelo preset de regex anterior) com testes de parsing usando fixture de saída real.
3. Implementar `semgrep_bridge.py` com testes de parsing usando fixture de saída real.
4. Implementar `bandit_bridge.py`, incluindo a lógica de execução condicional por detecção de arquivos Python.
5. Implementar `sast_finding_mapper.py` centralizando qualquer lógica de normalização compartilhada entre os três (se houver), evitando duplicação de código de mapeamento de severidade.
6. Implementar a deduplicação com o preset de regex de secret scanning, se já existente.
7. Registrar os três bridges em `core.py`, com as flags/config de ativação (`enabled: false` por padrão).
8. Validar manualmente, com os binários reais instalados em ambiente de desenvolvimento, que cada bridge detecta corretamente um exemplo conhecido de vulnerabilidade/segredo/uso inseguro.
9. Atualizar `config.schema.yml` e documentação (README/CLI help), deixando claro que os binários externos são pré-requisitos opcionais não instalados automaticamente pelo GitPR.
10. Rodar suite completa de testes do projeto, com atenção especial a não haver regressão nos bridges de linter já existentes (Checkstyle/ESLint/PHPCS/Stylelint).

Cada etapa deve ser um commit/PR isolado e revisável. A etapa 1 (extração/confirmação da interface comum) é a mais sensível por tocar em código já em produção — deve ser validada isoladamente antes de qualquer bridge novo ser implementado sobre ela.

## 10. Encaixe estratégico (contexto de monetização)

Classificada como Tier 2 (diferenciação e retenção, médio esforço) por estender um padrão de integração já existente (bridge de linter externo) para uma categoria de maior valor percebido — segurança —, mas com esforço não trivial de engenharia devido aos requisitos de hardening de subprocess e à necessidade de normalizar três formatos de saída distintos. O suporte a "40+ linters e SAST" é hoje uma feature paga do CodeRabbit, conforme já identificado nas análises de monetização anteriores. Nesta primeira versão, recomenda-se manter o bridge disponível no tier **Free/Community** (o usuário instala os binários e usa livremente, sem custo de infraestrutura do lado do GitPR), reservando para o tier **Pro/Team** futuro a curadoria de rulesets customizados por stack (ex.: ruleset Semgrep específico para Laravel/PHP mantido e atualizado pelo GitPR), a agregação de resultados SAST em dashboard de time, e o suporte/SLA para configuração em ambientes corporativos — a mesma lógica já aplicada ao preset de secret scanning por regex.
