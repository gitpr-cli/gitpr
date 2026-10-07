# SPEC — GitPR "Junior Mentor" Mode (review didático)

> Documento de especificação técnica para implementação via Claude Code skill.
> Escopo: nova skill fixa que transforma a saída do review de qualidade em feedback didático — não apenas apontando o problema, mas explicando o "porquê" com analogias e contexto pedagógico, voltado a desenvolvedores juniores/em formação.

## 0. Contexto obrigatório antes de codificar

Antes de gerar qualquer código, a skill DEVE:

1. Ler o mecanismo de skills fixas já confirmado no projeto: skills são registradas em `get_skill_context` (`core.py`), sem descoberta dinâmica por diretório, e cada skill (`.gitpr.pr.md`, potencialmente `.gitpr.explain.md` se já implementada) é injetada como *system instruction* junto ao `git diff` analisado. Esta feature deve seguir exatamente o mesmo mecanismo: uma nova skill fixa (`.gitpr.mentor.md`), registrada no mesmo ponto, sem introduzir um segundo sistema de carregamento de skill.
2. Ler a implementação do **motor de review de qualidade já existente** (o pipeline que hoje gera findings — linter regex, bridge externo, review semântico de IA) e confirmar: (a) o modelo de finding já usado internamente (severidade, categoria, arquivo, linha, mensagem, sugestão — já mapeado em specs anteriores desta série, ex. `gitpr fix`), (b) em que ponto exato do pipeline a mensagem de finding é formatada para exibição, para decidir se o modo mentor **reescreve** essa mensagem final ou **gera uma camada adicional** ao lado da mensagem técnica padrão (a segunda opção é preferível para não obrigar todo usuário a ler texto didático quando não quer — ver seção 1).
3. Confirmar se `gitpr fix`/`gitpr tests generate` (specs anteriores desta série) já foram implementados — se sim, o modo mentor pode reaproveitar a mesma referência de finding (`finding_id`) para oferecer, junto à explicação didática, um link direto para "aplicar a correção" ou "gerar um teste que comprova o problema", sem duplicar a lógica de resolução de finding já existente nesses comandos.
4. Confirmar a interface real de `ai_providers.py` para reaproveitar o mesmo mecanismo de chamada de IA já usado pelo review padrão — o modo mentor deve, preferencialmente, reaproveitar a mesma chamada de review (evitando o custo de uma segunda chamada de IA completa) e apenas mudar a **skill/prompt de formatação da saída**, não o motor de análise em si; confirmar se essa separação entre "análise" e "formatação da explicação" já existe no pipeline atual antes de assumir que é trivial.
5. Verificar se existe algum mecanismo de perfil de usuário/preferência persistente (ex.: um modo "estilo de review" configurável por pessoa, não apenas por repositório) — se não existir, esta feature precisa decidir se a ativação do modo mentor é por repositório (config `.gitpr/config.yml`) ou por execução individual (flag), já que o cenário de uso típico (um tech lead revisando código de um júnior específico) sugere que pode não fazer sentido ativar por repositório inteiro de forma permanente.

Não prosseguir com a implementação sem completar os passos 1–3.

## 1. Escopo da feature

- **Objetivo:** oferecer uma alternativa de formatação da saída do review de qualidade, voltada a quem está aprendendo — cada finding, em vez de (ou além de) uma mensagem técnica direta, recebe uma explicação didática do porquê aquele padrão é um problema, com analogia quando isso ajudar a fixar o conceito, e uma sugestão de leitura/próximo passo de aprendizado quando aplicável.
- **Modelo de ativação:** este modo deve ser **aditivo por padrão**, não substitutivo — a mensagem técnica original do finding continua existindo (é a fonte de verdade para quem já sabe o que aquilo significa); o modo mentor adiciona uma seção de explicação expandida, ativável via flag (`gitpr -r --mentor` ou `gitpr review --mentor`) ou config (`review.mentor_mode: true`), nunca ligada silenciosamente por padrão.
- **Estrutura da explicação didática por finding:**
  1. **O que está acontecendo** — reformulação simples do problema técnico, sem o jargão da mensagem original quando um termo mais acessível comunicar melhor a mesma ideia.
  2. **Por que isso importa** — a consequência prática caso o padrão não seja corrigido (não apenas "isso é uma boa prática", mas o cenário concreto de falha que a regra evita).
  3. **Analogia (opcional, apenas quando genuinamente esclarecedora)** — usada para fixar o conceito, nunca forçada quando o problema já é simples o suficiente para não precisar de analogia.
  4. **Para aprender mais** — um ponteiro textual curto (não um link externo verificado, já que a IA não deve inventar URLs) para o conceito geral a estudar (ex.: "isso está relacionado ao princípio de responsabilidade única" em vez de um link específico que pode não existir).
- **Comandos/flags:**
  - `gitpr -r --mentor` (ou equivalente à convenção de flags do review existente) — roda o review normal, mas com a camada didática adicionada a cada finding.
  - `gitpr mentor --finding <id>` — gera a explicação didática para um finding específico do último review (útil quando um tech lead quer compartilhar a explicação de um problema específico com um desenvolvedor júnior, sem reprocessar todo o review).
- **Fora de escopo nesta fase:** perfil de aprendizado persistente por desenvolvedor (rastrear quais conceitos uma pessoa específica já recebeu explicação, para não repetir) — isso exigiria armazenamento de identidade por pessoa que hoje não existe no produto; geração de conteúdo de treinamento estruturado (trilha de aprendizado, quiz) — a feature produz explicação pontual por finding, não um curso; tradução do texto didático para múltiplos idiomas nesta entrega (mesma decisão já tomada na spec de "Explain my PR": o i18n cobre a interface, não o conteúdo gerado por IA).
- **Compatibilidade:** ativar o modo mentor não deve alterar a classificação de severidade nem a lógica de bloqueio de fluxo já existente (um finding `blocker` continua bloqueando o commit/PR independentemente do modo de explicação escolhido) — o modo mentor afeta exclusivamente a apresentação textual, nunca a lógica de negócio do review.

## 2. Árvore de arquivos a criar/alterar

```
skills/
└── .gitpr.mentor.md               # NOVO — arquivo de skill fixo, seguindo o mesmo formato de .gitpr.pr.md

src/domain/review/
└── mentor_explanation_builder.py  # NOVO — estrutura a resposta da IA em explicação didática por finding

src/application/use_cases/
└── generate_mentor_explanation.py # NOVO — orquestra: localizar finding(s) -> montar prompt com skill mentor -> chamar IA -> estruturar saída

core.py                            # ALTERAR — registrar a skill "mentor" em get_skill_context; integrar flag --mentor no fluxo de review
main.py (ou entrypoint CLI)         # ALTERAR — novo comando `gitpr mentor --finding <id>` e flag `--mentor` no review

tests/domain/review/
└── test_mentor_explanation_builder.py
tests/application/use_cases/
└── test_generate_mentor_explanation.py
```

## 3. Contrato de dados (obrigatório)

```python
# src/domain/review/mentor_explanation_builder.py
from dataclasses import dataclass


@dataclass
class MentorExplanation:
    finding_id: str              # referência ao finding original, mesmo modelo já usado por gitpr fix
    what_is_happening: str
    why_it_matters: str
    analogy: str | None           # None quando a IA decidir que não é necessária
    learn_more_pointer: str | None
    markdown: str                  # explicação já formatada, pronta para exibição junto ao finding original
```

```python
# src/application/use_cases/generate_mentor_explanation.py
def generate_mentor_explanation(
    finding,                      # reaproveita o modelo de finding já existente no produto
    ai_provider,
    skill_context: str,            # conteúdo de .gitpr.mentor.md via get_skill_context
) -> MentorExplanation:
    ...

def generate_mentor_explanations_for_review(
    findings: list,                # todos os findings do review atual
    ai_provider,
    skill_context: str,
) -> list[MentorExplanation]:
    ...
```

## 4. Conteúdo esperado da skill `.gitpr.mentor.md`

A skill deve instruir a IA, como *system instruction*, a produzir a explicação didática seguindo estes princípios (escritos como instruções diretas no arquivo, não como código):

- Escrever para alguém que está aprendendo, não para quem já domina o conceito — evitar assumir conhecimento prévio de padrões avançados sem explicá-los brevemente.
- Nunca ser condescendente ou infantilizar o problema — o tom é de mentoria técnica respeitosa, não de "aula para principiante" genérica.
- A analogia, quando usada, deve vir de domínios cotidianos ou de conceitos de programação mais básicos que o desenvolvedor já provavelmente conhece — nunca uma analogia mais complexa que o próprio conceito que está explicando.
- Nunca inventar um link específico ou nome de artigo/livro que possa não existir — usar apenas referência a conceito/princípio geral (nomes de padrões, princípios SOLID, categorias de vulnerabilidade OWASP quando aplicável) que o desenvolvedor possa buscar por si mesmo.
- Manter cada explicação curta o suficiente para ser lida em menos de 30 segundos — o objetivo é fixar um conceito por vez, não escrever um tutorial completo.
- Seguir a mesma convenção de honestidade epistêmica já estabelecida em outras skills do produto (`.gitpr.pr.md`, e `.gitpr.explain.md` se já implementada): se o "porquê" de uma regra não for claramente inferível a partir do finding e do contexto do diff, admitir isso explicitamente em vez de inventar uma justificativa genérica.

## 5. Algoritmo — pipeline completo

1. **Executar o review de qualidade normalmente** (linter, bridges externos, review semântico) — o modo mentor não substitui nem duplica essa etapa, apenas consome o resultado já produzido.
2. **Para cada finding do resultado** (ou apenas para o finding especificado via `--finding <id>`), montar o prompt injetando `.gitpr.mentor.md` como system instruction, junto ao contexto do finding (mensagem original, arquivo, trecho de código relevante, categoria, severidade).
3. **Chamar o provider de IA** configurado — avaliar, no passo 0.4, se é viável obter a explicação didática na mesma chamada que já gera o finding (economizando uma segunda chamada), ou se precisa ser uma chamada adicional por finding; se for uma chamada adicional, considerar processá-la apenas sob demanda (`--mentor` ativo) para não impor esse custo a quem não pediu.
4. **Estruturar a resposta** em `MentorExplanation`, vinculada ao `finding_id` original.
5. **Exibir a explicação didática junto (não em vez) da mensagem técnica original do finding**, no mesmo formato de saída já usado pelo review (Markdown/TUI/terminal) — a mensagem técnica aparece primeiro (fonte de verdade rápida), seguida da seção expandida do mentor quando o modo estiver ativo.
6. **`gitpr mentor --finding <id>`** (comando avulso): localizar o finding no resultado do último review persistido (mesmo mecanismo de leitura já usado por `gitpr fix --finding` e `gitpr tests generate --finding`), gerar apenas a explicação daquele finding específico, e exibir de forma isolada — útil para compartilhar com outra pessoa sem reprocessar todo o review.

## 6. Config

```yaml
review:
  mentor_mode: false                # equivalente à flag --mentor; nunca true por padrão
  mentor_include_analogy: true       # permite desabilitar analogias globalmente, se a equipe preferir tom mais direto
```

## 7. Testes obrigatórios (critério de aceite)

1. **Teste de registro da skill**: `get_skill_context` deve reconhecer `mentor` como skill suportada, seguindo o mesmo padrão de teste já existente/estabelecido para outras skills fixas do produto.
2. **Teste de estruturação de resposta** (`test_mentor_explanation_builder.py`): dada uma resposta de IA simulada (fixture) contendo os campos esperados, `MentorExplanation` deve ser montada corretamente, incluindo o caso em que `analogy` é `None`.
3. **Teste de vínculo com finding original**: `MentorExplanation.finding_id` deve corresponder exatamente ao finding que originou a chamada — nenhuma explicação deve ficar desvinculada de sua origem.
4. **Teste de não-alteração de severidade/bloqueio**: ativar o modo mentor não deve alterar a severidade de nenhum finding nem o comportamento de bloqueio de commit/PR já existente — teste de regressão comparando o resultado do review com e sem `--mentor` ativo, exceto pela presença da explicação adicional.
5. **Teste de modo aditivo**: com `--mentor` ativo, a mensagem técnica original de cada finding deve continuar presente na saída, ao lado da explicação didática — nunca substituída ou removida.
6. **Teste de comando avulso por finding**: `gitpr mentor --finding <id>` deve localizar corretamente o finding no resultado do último review persistido e gerar a explicação isolada, sem reprocessar o review completo.
7. **Teste de opt-in explícito**: sem a flag `--mentor` ou a config equivalente ativada, nenhuma chamada adicional de IA para explicação didática deve ocorrer — validar via mock que o provider de IA não é invocado para esse propósito quando o modo está desativado.
8. **Teste de honestidade epistêmica**: resposta de IA simulada sem evidência suficiente para o "por que isso importa" deve resultar em uma explicação que admite a limitação, seguindo a mesma convenção de placeholder já usada nas outras skills, e não uma justificativa genérica fabricada.

Critério de "feature completa": todos os testes acima passam; rodar `gitpr -r --mentor` sobre um diff de teste com findings conhecidos produz, para cada finding, a mensagem técnica original mais a explicação didática correspondente; `gitpr mentor --finding <id>` funciona isoladamente sem reprocessar o review inteiro.

## 8. Ordem de execução recomendada

1. Escrever o conteúdo de `.gitpr.mentor.md` como texto puro, seguindo os princípios da seção 4, e validar manualmente contra 3-4 findings reais de categorias diferentes (segurança, estilo, teste faltante) para confirmar que o tom e a profundidade da explicação são adequados antes de integrar ao pipeline.
2. Registrar a skill `mentor` em `get_skill_context` (`core.py`).
3. Implementar `mentor_explanation_builder.py` (estruturação pura da resposta da IA, sem I/O) com testes usando fixtures de resposta.
4. Implementar `generate_mentor_explanation.py` conectando finding real + skill + chamada de IA real + estruturação — validar contra pelo menos um provider real antes de finalizar.
5. Decidir e implementar a estratégia de custo de chamada (uma chamada por finding vs. reaproveitar a chamada de review original), conforme apurado no passo 0.4.
6. Integrar a flag `--mentor` no fluxo padrão de `gitpr -r`/review, garantindo que o modo é opt-in e não altera severidade/bloqueio.
7. Registrar o comando avulso `gitpr mentor --finding <id>` em `core.py`/CLI.
8. Atualizar `config.schema.yml` e documentação (README/CLI help) — este é um bom candidato para exemplo vivo no README, dado o apelo de branding forte da feature (mesma lógica de "prova social de baixo custo" já usada em specs anteriores desta série).
9. Rodar suite completa de testes do projeto antes de considerar a feature concluída.

Cada etapa deve ser um commit/PR isolado e revisável.

## 9. Encaixe estratégico (contexto de monetização)

Classificada como Tier 2 (diferenciação e retenção, médio esforço) por exigir uma nova skill fixa com estrutura de saída própria e uma decisão de arquitetura sobre custo de chamada de IA adicional — mas o esforço de engenharia é comparável ao de "Explain my PR", reaproveitando quase toda a infraestrutura já existente. Fica no tier **Free/Community**: nenhum concorrente do mercado (CodeRabbit, Qodo, Greptile) foca em mentoria didática como recurso central, o que torna esta uma feature de branding genuinamente diferenciada, não apenas mais uma capacidade técnica. O alinhamento com o perfil do próprio criador do produto — que dedica parte relevante do seu tempo a orientar uma equipe de 7 programadores — é o que torna esta feature mais que um exercício de marketing: é a formalização de um trabalho de mentoria que já é feito manualmente, distribuído pela ferramenta sem custo adicional de infraestrutura, com potencial de gerar conteúdo de demonstração autêntico (capturas reais de explicações geradas) para o README e para comunicação de posicionamento do produto.
