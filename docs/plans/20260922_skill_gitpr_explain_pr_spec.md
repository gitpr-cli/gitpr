# SPEC — GitPR "Explain my PR" (resumo para o revisor)

> Documento de especificação técnica para implementação via Claude Code skill.
> Escopo: gerar um resumo em linguagem simples do PR, com perspectiva invertida em relação à descrição de PR já existente — pensado para quem vai revisar (não para quem vai ler o histórico/changelog), respondendo diretamente "o que muda, por que, e quais riscos preciso avaliar".

## 0. Contexto obrigatório antes de codificar

Antes de gerar qualquer código, a skill DEVE:

1. Ler o arquivo `.gitpr.pr.md` (ou nome real confirmado no projeto) na íntegra e entender exatamente como ele funciona hoje: é injetado como *system instruction* para a IA, e o `git diff` é o conteúdo analisado — a IA devolve a descrição seguindo a estrutura de seções que esse arquivo define. Esta feature deve seguir **exatamente o mesmo mecanismo**: uma nova skill fixa (ex.: `.gitpr.explain.md`) com uma estrutura de seções própria, voltada à perspectiva do revisor.
2. Confirmar em `core.py`, no método `get_skill_context` (já confirmado como o ponto único de verdade sobre quais skills são suportadas — não há descoberta dinâmica por varredura de diretório), como uma skill existente é registrada, para adicionar a nova skill `explain` seguindo exatamente o mesmo padrão de registro, sem introduzir um mecanismo de carregamento paralelo.
3. Confirmar o ponto exato do pipeline onde `.gitpr.pr.md` é hoje carregado e injetado no prompt de geração de descrição de PR (provavelmente dentro do fluxo de `gitpr pr`), para decidir se "Explain my PR" é: (a) uma chamada de IA adicional e independente, disparada por um comando/flag própria, produzindo uma saída separada da descrição de PR; ou (b) uma seção adicional dentro do mesmo corpo do PR, gerada na mesma chamada. A resposta correta depende de como o restante do produto já trata múltiplas skills/seções — não assumir, confirmar contra o código real.
4. Confirmar se o projeto já tem algum mecanismo de múltiplas skills combinadas em uma única chamada de IA (ex.: parte do prompt vem de `.gitpr.pr.md`, outra parte de outra skill) ou se cada skill hoje corresponde a uma chamada de IA isolada e independente — isso define a estratégia de implementação de "Explain my PR" como uma segunda chamada versus uma extensão da mesma chamada.
5. Verificar se existe algum placeholder/convenção de "campo não preenchível sem evidência" já estabelecida em `.gitpr.pr.md` (mencionada em trabalho anterior do projeto: usar `[PREENCHER: pergunta objetiva]` em vez de suposição) — se essa convenção existir, a nova skill de "Explain my PR" deve seguir exatamente o mesmo princípio de honestidade epistêmica (nunca inventar risco ou impacto sem evidência no diff), mantendo consistência de qualidade entre as skills do produto.
6. Confirmar se o comando de publicação de PR (`gitpr pr`) já suporta múltiplas seções/blocos de conteúdo no corpo final (por exemplo, para acomodar o badge da spec anterior, trailers de coautoria, e agora potencialmente esta explicação) — identificar o ponto de montagem final do corpo do PR, já mapeado em specs anteriores desta série (badge, release notes), para reaproveitá-lo aqui também.

Não prosseguir com a implementação sem completar os passos 1–4.

## 1. Escopo da feature

- **Objetivo:** produzir, a partir do mesmo diff já analisado pelo GitPR, um texto complementar à descrição de PR padrão — não uma redundância dela — estruturado para responder às perguntas que um revisor faz antes de aprovar: o que muda, por que essa abordagem foi escolhida, e quais riscos merecem atenção específica na revisão.
- **Diferença de perspectiva em relação à descrição de PR já existente:** a descrição de PR gerada por `.gitpr.pr.md` é tipicamente voltada a documentar a mudança (para o autor comunicar, para histórico, para changelog). "Explain my PR" inverte a audiência: é escrita assumindo que quem lê **não escreveu o código** e precisa decidir se aprova, com foco em risco e impacto, não em exaustividade técnica.
- **Estrutura mínima de seções da nova skill (`.gitpr.explain.md`):**
  1. **O que muda** — resumo de 2–4 frases em linguagem simples, evitando jargão de implementação quando um termo de negócio/domínio comunica melhor.
  2. **Por que muda** — a motivação/problema que a mudança resolve, inferida do diff e da mensagem de commit/contexto disponível (nunca inventada; se não houver evidência suficiente no diff para inferir motivação, seguir a mesma convenção de placeholder já usada em `.gitpr.pr.md`).
  3. **Onde focar a revisão** — lista objetiva de 2–5 pontos específicos que merecem atenção do revisor (ex.: "a validação de permissão foi movida do controller para o middleware — confirme que todos os caminhos de acesso passam por ele agora"), não uma lista genérica de boas práticas.
  4. **Risco de regressão** — avaliação textual curta do que pode quebrar em produção se a mudança tiver um problema não detectado na revisão, baseada em sinais objetivos do diff (arquivos críticos tocados, ausência de teste correspondente, migrations, mudanças em autenticação/autorização) — reaproveitando o mesmo tipo de sinal já mapeado como "risk scoring" em análises anteriores, se essa lógica já existir; caso não exista, produzir a avaliação apenas com base no julgamento da IA sobre o diff, sem inventar uma pontuação numérica formal (isso é escopo da feature de risk scoring, não desta).
- **Comando/flag novo:** `gitpr pr --explain` (adiciona a seção ao corpo do PR publicado) e/ou `gitpr explain` como comando standalone que apenas exibe o texto no terminal/TUI sem publicar nada — ambos devem existir, cobrindo o caso de quem só quer ler antes de decidir incluir no PR.
- **Fora de escopo nesta fase:** publicação como comentário separado do PR (distinto do corpo principal) — nesta versão, o texto entra como seção dentro do corpo do PR ou é exibido localmente, não como um segundo comentário automático (isso pode ser considerado como opção futura, análoga ao `--post-comment` já especificado para `--review-pr`); geração de diagrama visual do fluxo alterado; tradução automática para múltiplos idiomas do texto gerado (o i18n do produto cobre a interface, não o conteúdo gerado por IA nesta entrega).
- **Compatibilidade:** a introdução desta skill não deve alterar o comportamento de `.gitpr.pr.md` — são skills independentes, ativáveis separadamente, mesmo que ambas contribuam para o mesmo corpo final de PR quando usadas juntas.

## 2. Árvore de arquivos a criar/alterar

```
skills/
└── .gitpr.explain.md              # NOVO — arquivo de skill fixo, seguindo o mesmo formato de .gitpr.pr.md

src/domain/pr/
└── explain_section_builder.py     # NOVO — monta a seção final a partir da resposta estruturada da IA

src/application/use_cases/
└── generate_pr_explanation.py     # NOVO — orquestra: carregar skill -> montar prompt com diff -> chamar IA -> estruturar saída

core.py                            # ALTERAR — registrar a skill "explain" em get_skill_context, seguindo o padrão já existente de "pr"
main.py (ou entrypoint CLI)         # ALTERAR — novo comando/flag `gitpr explain` e `gitpr pr --explain`

tests/domain/pr/
└── test_explain_section_builder.py
tests/application/use_cases/
└── test_generate_pr_explanation.py
```

## 3. Contrato de dados (obrigatório)

```python
# src/domain/pr/explain_section_builder.py
from dataclasses import dataclass


@dataclass
class ReviewerFocusPoint:
    description: str            # ex.: "validação de permissão movida para middleware — confirme cobertura"
    file_path: str | None        # quando identificável a partir do diff
    related_line: int | None


@dataclass
class PrExplanation:
    what_changes: str            # 2-4 frases
    why_it_changes: str           # motivação inferida, ou placeholder explícito se não houver evidência
    reviewer_focus_points: list[ReviewerFocusPoint]
    regression_risk: str          # avaliação textual curta
    has_sufficient_evidence: bool  # False quando a IA precisou usar placeholder em algum campo
    markdown: str                  # seção já formatada, pronta para inserir no corpo do PR ou exibir standalone
```

```python
# src/application/use_cases/generate_pr_explanation.py
def generate_pr_explanation(
    diff_content: str,
    ai_provider,
    skill_context: str,           # conteúdo de .gitpr.explain.md, obtido via get_skill_context já existente
) -> PrExplanation:
    ...
```

## 4. Conteúdo esperado da skill `.gitpr.explain.md`

A skill deve instruir a IA, como *system instruction*, a produzir a saída estruturada acima seguindo estes princípios (a serem escritos como instruções diretas no arquivo, não como código):

- Escrever para um leitor que não viu o código antes e vai decidir se aprova — evitar jargão de implementação sempre que um termo de domínio/negócio for suficiente.
- Nunca inventar motivação ou risco sem evidência textual no diff, na mensagem de commit, ou no contexto disponível — usar a mesma convenção de placeholder explícito já estabelecida em `.gitpr.pr.md` (`[PREENCHER: pergunta objetiva]` ou equivalente confirmado no passo 0.1) quando a motivação não puder ser inferida com confiança.
- Pontos de foco de revisão devem ser específicos e ligados a um arquivo/trecho real do diff, nunca genéricos ("revise a lógica com cuidado" não é um ponto de foco válido; "a query em `UserRepository::findActive()` não filtra por tenant_id, confirme se isso é intencional" é um ponto de foco válido).
- Avaliação de risco de regressão deve citar o sinal objetivo que a sustenta (arquivo crítico, ausência de teste, migration sem rollback) — nunca uma afirmação de risco sem justificativa rastreável ao diff.
- Limitar a saída a um tamanho que caiba em uma leitura de 30-60 segundos — este é um resumo para acelerar a revisão, não uma segunda descrição exaustiva.

## 5. Algoritmo — pipeline completo

1. **Carregar a skill `explain`** via `get_skill_context` (mesmo mecanismo já usado para `pr`), confirmando que ela está registrada na lista fixa de skills suportadas.
2. **Obter o diff** do PR/branch atual, reaproveitando a mesma função de obtenção de diff já usada pelo restante do produto (mesmo diff que alimenta a geração de descrição de PR e o review, não uma segunda extração divergente).
3. **Montar o prompt** injetando o conteúdo de `.gitpr.explain.md` como system instruction e o diff como conteúdo a analisar — mesmo padrão estrutural de `.gitpr.pr.md`, apenas com a skill diferente.
4. **Chamar o provider de IA** configurado (via `ai_providers.py`), esperando uma resposta estruturada (JSON ou Markdown com seções previsíveis, conforme o padrão de saída que `.gitpr.pr.md` já usa — reaproveitar o mesmo formato de contrato de resposta, não inventar um novo).
5. **Estruturar em `PrExplanation`**, marcando `has_sufficient_evidence=False` se qualquer campo tiver caído no placeholder de evidência insuficiente.
6. **Se `gitpr explain` (standalone)**: exibir o resultado no terminal/TUI, sem tocar em nenhum PR.
7. **Se `gitpr pr --explain`**: inserir a seção formatada (`PrExplanation.markdown`) no corpo final do PR, no mesmo ponto de montagem final já identificado nas specs anteriores (após a descrição principal gerada por `.gitpr.pr.md`, antes ou depois do badge conforme ordem de leitura mais sensata a definir — sugestão: descrição principal → seção "Explain my PR" → badge, já que o badge é o elemento mais curto e decorativo, ficando bem ao final).

## 6. Config

```yaml
pr:
  explain_enabled_by_default: false   # gitpr pr --explain sempre disponível via flag; este campo controla se entra automaticamente sem a flag
```

## 7. Testes obrigatórios (critério de aceite)

1. **Teste de registro da skill**: `get_skill_context` deve reconhecer `explain` como skill suportada, seguindo o mesmo padrão de teste já existente para a skill `pr` (teste de contrato/paridade entre skills registradas).
2. **Teste de estruturação de resposta** (`test_explain_section_builder.py`): dada uma resposta de IA simulada (fixture) contendo os quatro campos esperados, `PrExplanation` deve ser montado corretamente, incluindo o Markdown final formatado.
3. **Teste de placeholder de evidência insuficiente**: resposta de IA contendo o placeholder de "sem evidência suficiente" em `why_it_changes` deve resultar em `has_sufficient_evidence=False`, sem que o pipeline trate isso como erro — é um resultado válido e esperado, não uma falha.
4. **Teste de não-interferência com `.gitpr.pr.md`**: gerar a descrição de PR padrão e a explicação para revisor no mesmo fluxo (`gitpr pr --explain`) não deve alterar o conteúdo da descrição padrão — validar que as duas skills produzem saídas independentes corretamente combinadas no corpo final.
5. **Teste de comando standalone**: `gitpr explain` deve funcionar sem exigir nenhuma configuração de SCM/token de forge — apenas a IA é necessária, já que não há publicação envolvida nesse modo.
6. **Teste de posicionamento no corpo do PR**: com `--explain` e o badge (spec anterior) ambos ativos, validar que a ordem final das seções no corpo do PR segue a sequência esperada (descrição → explicação → badge), reaproveitando o ponto de montagem final já usado por essas specs anteriores.
7. **Teste de reuso do diff**: confirmar, via mock/spy, que `generate_pr_explanation` consome exatamente o mesmo diff já obtido para a descrição de PR no mesmo fluxo, sem uma segunda chamada divergente de `git diff`.

Critério de "feature completa": todos os testes acima passam; `gitpr explain` produz um resumo legível e específico ao diff analisado em um repositório de teste real; `gitpr pr --explain` insere a seção corretamente no corpo do PR publicado, coexistindo sem conflito com a descrição padrão e com o badge, quando ambos estiverem ativos.

## 8. Ordem de execução recomendada

1. Escrever o conteúdo de `.gitpr.explain.md` como texto puro (sem código), seguindo os princípios da seção 4, e validar manualmente contra 2-3 diffs de exemplo reais que a saída é de fato útil e específica antes de integrar ao pipeline.
2. Registrar a skill `explain` em `get_skill_context` (`core.py`), confirmando que o mecanismo fixo de skills reconhece a nova entrada sem exigir descoberta dinâmica.
3. Implementar `explain_section_builder.py` (estruturação pura da resposta da IA em `PrExplanation`, sem I/O) com testes usando fixtures de resposta.
4. Implementar `generate_pr_explanation.py` conectando obtenção de diff real + skill + chamada de IA real + estruturação — validar contra pelo menos um provider real antes de finalizar.
5. Registrar o comando standalone `gitpr explain` em `core.py`/CLI.
6. Integrar a flag `--explain` em `gitpr pr`, inserindo a seção no ponto de montagem final do corpo do PR já identificado.
7. Validar a ordem de composição do corpo do PR quando múltiplas seções opcionais estiverem ativas simultaneamente (descrição + explicação + badge).
8. Atualizar `config.schema.yml` e documentação (README/CLI help), incluindo exemplo de saída no README como demonstração (reaproveitando a mesma lógica de "prova social de baixo custo" já usada em specs anteriores desta série).
9. Rodar suite completa de testes do projeto antes de considerar a feature concluída.

Cada etapa deve ser um commit/PR isolado e revisável.

## 9. Encaixe estratégico (contexto de monetização)

Classificada como Tier 2 (diferenciação e retenção, médio esforço) por exigir a criação de uma nova skill fixa com estrutura de saída própria e um novo ponto de composição no corpo do PR, mesmo reaproveitando integralmente a infraestrutura de IA e diff já existente — o esforço real está em desenhar bem o prompt/skill para produzir um resumo genuinamente útil ao revisor, não em nova infraestrutura técnica. Fica no tier **Free/Community**: é uma feature de produtividade que beneficia diretamente quem revisa PRs de outras pessoas (o mesmo público expandido pela feature `--review-pr` já especificada), reforçando a mesma lógica estratégica — mais pessoas de uma equipe interagindo com o GitPR sem custo adicional de infraestrutura, o que torna a conversão futura ao tier Team (dashboards agregados, políticas compartilhadas) mais natural quanto mais ampla for a adoção dentro da mesma organização.
