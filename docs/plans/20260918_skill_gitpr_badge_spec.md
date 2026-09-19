# SPEC — GitPR Badge/Selo "Reviewed by GitPR" (marketing viral)

> Documento de especificação técnica para implementação via Claude Code skill.
> Escopo: gerar automaticamente um badge/selo (Markdown + imagem via shields.io ou serviço equivalente) inserível na descrição do PR e/ou README, exibindo que aquele PR/repositório foi processado pelo GitPR, com métricas resumidas (ex.: "0 issues, 94% clean"). Objetivo é marketing viral de baixo custo — cada PR se torna uma vitrine pública do produto.

## 0. Contexto obrigatório antes de codificar

Antes de gerar qualquer código, a skill DEVE:

1. Ler como o trailer `Co-Authored-By` é hoje implementado (já confirmado existir, com opt-out via `GITPR_COAUTHOR=false`) — extrair: (a) onde no pipeline esse trailer é injetado (na geração da mensagem de commit, no momento do commit real, ou em ambos), (b) o padrão de nome de variável de ambiente/config usado para opt-out, para replicar exatamente a mesma convenção no badge (ex.: `GITPR_BADGE=false`), (c) se existe algum mecanismo central de "flags de branding opcionais" onde o badge deveria se registrar, em vez de criar um mecanismo de config isolado.
2. Ler o arquivo `.gitpr.pr.md` (ou equivalente) que já funciona como template/molde de instrução de sistema para geração de descrição de PR, e confirmar exatamente como esse arquivo é injetado no prompt e como a saída da IA é depois inserida no corpo do PR — o badge deve ser inserido nesse mesmo ponto de montagem final do corpo do PR, não via uma segunda chamada de edição do PR após criado.
3. Confirmar como `metrics.py` (telemetria local) registra eventos por comando, incluindo se já existe algum dado agregado por review (contagem de findings por severidade, "tempo de execução", tokens) que possa alimentar o texto do badge (ex.: "0 issues, 94% clean") sem precisar recalcular nada — reaproveitar o dado já coletado em vez de introduzir uma nova fonte de métrica paralela.
4. Confirmar se o projeto já tem alguma convenção de geração de URLs para serviços externos de imagem (shields.io ou similar) em qualquer parte do código (ex.: badges já usados no próprio README do projeto, mencionados em análises anteriores como melhoria sugerida) — se sim, seguir o mesmo padrão de construção de URL.
5. Verificar se a criação/atualização de corpo de PR já passa por uma função centralizada de "montagem final do corpo" (concatenando descrição gerada por IA + trailers + outros elementos) — o badge deve ser adicionado nessa função central, não espalhado em múltiplos pontos de código que montam corpo de PR de formas diferentes.

Não prosseguir com a implementação sem completar os passos 1–3.

## 1. Escopo da feature

- **Objetivo:** inserir automaticamente, ao final da descrição do PR gerado pelo GitPR (e opcionalmente no README do projeto via comando dedicado), um badge Markdown que renderiza uma imagem de status (via shields.io endpoint dinâmico ou geração de SVG estático) mostrando que o PR foi processado pelo GitPR, com um resumo curto de qualidade extraído do review real daquele PR.
- **Dois pontos de inserção distintos:**
  1. **Badge de PR** (automático, por padrão, no fluxo normal de `gitpr pr`): inserido ao final do corpo do PR gerado, refletindo o resultado do review daquele PR específico (ex.: "GitPR: 0 blockers · 2 warnings · reviewed in 4.2s").
  2. **Badge de README** (comando explícito, não automático): `gitpr badge --readme` gera o snippet Markdown para o usuário colar manualmente no README do repositório, indicando "este projeto usa GitPR" — este é estático (não muda a cada PR), serve como badge de adoção da ferramenta, não de resultado de review.
- **Formato do badge de PR (dinâmico):** deve refletir dados reais do review daquele PR — não um número fixo genérico. Campos mínimos: contagem de blockers/críticos, contagem de warnings, e opcionalmente o tempo de execução do review. Se o review não encontrou nenhum problema, o badge deve comunicar isso de forma positiva (ex.: "0 issues found").
- **Mecanismo de geração de imagem:** usar shields.io como serviço de badge dinâmico via URL parametrizada (endpoint `https://img.shields.io/badge/...` ou o endpoint JSON dinâmico de shields.io), sem exigir infraestrutura própria de geração de imagem nesta fase — é uma decisão deliberada para não introduzir dependência de backend numa feature que deve ficar 100% no tier gratuito.
- **Fora de escopo nesta fase:** dashboard público agregando badges de múltiplos repositórios, geração de imagem própria hospedada em infraestrutura do GitPR (isso teria custo de hosting e abriria uma discussão de monetização que não é o objetivo desta feature viral gratuita), leaderboard de qualidade entre repositórios (já mapeado como feature separada em outra análise).
- **Compatibilidade:** deve ser **opt-out**, seguindo exatamente a mesma filosofia já estabelecida pelo trailer `Co-Authored-By` (`GITPR_COAUTHOR=false`) — nunca opt-in silencioso forçado. A ausência de badge não deve quebrar a geração normal do corpo do PR em nenhuma circunstância (se a chamada ao shields.io falhar ou estiver indisponível, a ausência do badge não deve impedir a publicação do PR).

## 2. Árvore de arquivos a criar/alterar

```
src/domain/branding/
├── badge_builder.py            # NOVO — monta a URL do badge e o snippet Markdown a partir de dados de review/config
└── badge_data.py                # NOVO — dataclasses de entrada (dados de review) e saída (snippet pronto)

src/application/use_cases/
└── generate_pr_badge.py         # NOVO — orquestra: ler resultado do review -> badge_builder -> inserir no corpo final do PR

core.py                          # ALTERAR — ponto de montagem final do corpo do PR passa a chamar generate_pr_badge
main.py (ou entrypoint CLI)       # ALTERAR — novo subcomando `gitpr badge --readme` (badge estático, geração avulsa)

tests/domain/branding/
├── test_badge_builder.py
└── test_badge_data.py
tests/application/use_cases/
└── test_generate_pr_badge.py
```

## 3. Contrato de dados (obrigatório)

```python
# src/domain/branding/badge_data.py
from dataclasses import dataclass


@dataclass
class ReviewSummaryForBadge:
    """Dados mínimos extraídos do resultado de review já existente — não recalcular nada aqui."""
    blockers: int
    criticals: int
    warnings: int
    total_findings: int
    duration_seconds: float | None
    provider: str | None          # "gemini" | "deepseek" | "ollama" — opcional, para badge mais detalhado


@dataclass
class BadgeSnippet:
    markdown: str        # ex.: "![Reviewed by GitPR](https://img.shields.io/badge/...)"
    image_url: str        # URL isolada, útil para quem quiser customizar o Markdown manualmente
    label_text: str        # texto puro exibido no badge, ex.: "0 issues · reviewed in 4.2s"
    style: str             # estilo shields.io usado (ex.: "flat", "flat-square") — configurável
```

```python
# src/domain/branding/badge_builder.py
def build_pr_badge(summary: ReviewSummaryForBadge, style: str = "flat") -> BadgeSnippet:
    """
    Lógica pura (sem I/O de rede) que monta a URL do shields.io e o Markdown final.
    Deve tratar summary com total_findings == 0 como caso de destaque positivo
    (cor verde/"brightgreen" no badge), blockers > 0 como alerta (cor vermelha/"red"),
    e warnings sem blockers como estado intermediário (cor amarela/"yellow").
    """
    ...

def build_readme_badge(style: str = "flat") -> BadgeSnippet:
    """
    Badge estático de adoção ("Uses GitPR"), sem dados de review — não depende
    de nenhum resultado de execução, pode ser gerado a qualquer momento via
    `gitpr badge --readme`.
    """
    ...
```

## 4. Algoritmo — pipeline completo (badge de PR, automático)

1. **Obter o resultado do review já executado** para o PR atual dentro do fluxo de `gitpr pr` — reaproveitar exatamente a mesma estrutura de resultado (contagem de findings por severidade) já produzida pelo motor de review, sem rodar um segundo review nem recalcular métricas de forma paralela.
2. **Mapear para `ReviewSummaryForBadge`**, extraindo apenas os campos necessários (contagens agregadas por severidade, duração, provider usado).
3. **Verificar a flag de opt-out** (`GITPR_BADGE=false` ou chave equivalente em config, seguindo a mesma convenção do `GITPR_COAUTHOR`) antes de prosseguir — se desabilitado, pular todas as etapas seguintes silenciosamente, sem log de erro (comportamento esperado, não uma falha).
4. **Montar o badge** via `build_pr_badge`, decidindo a cor/tom com base na severidade mais alta encontrada (blockers presentes → vermelho; sem blockers mas com warnings → amarelo; nenhum finding → verde).
5. **Inserir o snippet Markdown** ao final do corpo do PR, no mesmo ponto de montagem final identificado no passo 0.2/0.5 — após a descrição gerada pela IA e após quaisquer outros trailers/seções já existentes, separado por uma linha em branco e, opcionalmente, um separador Markdown (`---`) para diferenciar visualmente o badge do conteúdo gerado.
6. **Tratar falha de rede/indisponibilidade do shields.io como não-fatal**: como shields.io é um serviço externo, se a validação de URL falhar (não é necessário fazer uma chamada de verificação síncrona antes de publicar — a URL do badge é resolvida pelo navegador de quem visualiza o PR, não pelo GitPR no momento da criação) isso não deve nunca bloquear a criação do PR. Não é necessário (e não é recomendado) fazer uma chamada HTTP de verificação ao shields.io durante a execução do `gitpr pr` — a URL é apenas montada como texto, a renderização da imagem acontece no lado do cliente (GitHub/GitLab renderizando o Markdown), não no GitPR.

## 5. Algoritmo — pipeline do badge de README (comando avulso)

1. `gitpr badge --readme` monta um badge estático (`build_readme_badge`) sem depender de nenhum resultado de execução prévia — apenas texto/URL fixos indicando "Quality-checked with GitPR" ou equivalente.
2. Imprimir o snippet Markdown no terminal para o usuário copiar manualmente — **não escrever automaticamente no `README.md` do usuário nesta fase** (evitar modificar arquivo do usuário sem confirmação explícita; se uma versão futura quiser inserir automaticamente, isso exigiria confirmação interativa explícita, análoga ao padrão de confirmação já estabelecido em outras specs deste produto para ações que alteram arquivos do usuário).
3. Opcionalmente, oferecer variações de estilo (`--style flat|flat-square|for-the-badge`, seguindo os estilos suportados nativamente pelo shields.io) e permitir customizar o texto do label.

## 6. Config

Adicionar ao schema de config existente, seguindo a mesma convenção do `GITPR_COAUTHOR`:

```yaml
branding:
  pr_badge: true                # equivalente a variável de ambiente GITPR_BADGE
  pr_badge_style: "flat"        # flat | flat-square | for-the-badge (estilos nativos do shields.io)
  pr_badge_show_duration: true  # incluir tempo de execução do review no texto do badge
```

Variável de ambiente equivalente, seguindo o padrão já estabelecido: `GITPR_BADGE=false` desabilita o badge automático de PR (config tem precedência menor que env var, ou o inverso — confirmar qual convenção de precedência o projeto já usa para `GITPR_COAUTHOR` e replicar exatamente).

## 7. Setup e transparência (consentimento explícito)

Seguindo a recomendação já identificada nas análises anteriores sobre o trailer `Co-Authored-By` — que mesmo tendo opt-out, pode gerar resistência se ativado silenciosamente por padrão — o badge deve ser apresentado ao usuário no momento do `gitpr --init` (ou primeira execução de `gitpr pr` após a feature ser lançada) com uma linha explicando o que é e como desabilitar, em vez de simplesmente aparecer no primeiro PR sem aviso prévio. Isso não é uma escolha de UX arbitrária: é consistente com o princípio de transparência já aplicado ao trailer de coautoria neste mesmo produto.

## 8. Testes obrigatórios (critério de aceite)

1. **Teste de construção de URL/Markdown** (`test_badge_builder.py`): dado um `ReviewSummaryForBadge` com valores variados (zero findings, apenas warnings, com blockers), validar que a cor do badge e o texto do label correspondem à regra definida na seção 4.4; validar que a URL gerada é bem formada (encoding correto de caracteres especiais no texto do label, já que shields.io exige escaping específico no formato do path).
2. **Teste de opt-out**: com `GITPR_BADGE=false` (ou config equivalente), `generate_pr_badge` não deve inserir nenhum conteúdo no corpo do PR — corpo final deve ser idêntico ao que seria gerado sem a feature.
3. **Teste de não-bloqueio**: simular qualquer exceção dentro da construção do badge (ex.: dados de resumo malformados) e confirmar que a criação do PR prossegue normalmente, sem o badge, e sem propagar a exceção para o fluxo principal — badge é estritamente aditivo, nunca pode quebrar a publicação do PR.
4. **Teste de badge de README avulso** (`test_generate_pr_badge.py` ou arquivo próprio): `gitpr badge --readme` deve produzir um snippet válido sem exigir nenhum resultado de review prévio, nenhuma configuração de API key, e sem tocar em nenhum arquivo do usuário automaticamente.
5. **Teste de posicionamento no corpo do PR**: validar que o badge é inserido exatamente após a descrição gerada e após trailers existentes (não no meio do conteúdo gerado pela IA), reaproveitando o mesmo ponto de montagem final identificado no contexto obrigatório.
6. **Teste de não-regressão do trailer `Co-Authored-By`**: a introdução do badge não deve alterar o comportamento existente do trailer — ambos devem poder coexistir no corpo final do PR, cada um controlável de forma independente pela sua própria flag de opt-out.
7. **Teste de estilos**: cada valor válido de `--style`/`pr_badge_style` deve gerar uma URL shields.io correta para aquele estilo; valor inválido deve cair em um default seguro com aviso, não lançar exceção.

Critério de "feature completa": todos os testes acima passam; um PR real gerado com a feature ativa exibe o badge corretamente renderizado ao ser visualizado no GitHub/GitLab (validação manual final, já que a renderização de imagem shields.io não é testável via unit test); desabilitar a feature via flag produz corpo de PR idêntico ao comportamento anterior à introdução da feature.

## 9. Ordem de execução recomendada

1. Implementar `badge_data.py` (dataclasses, sem lógica) e `badge_builder.py` (lógica pura de construção de URL/Markdown, sem I/O) com testes cobrindo toda a matriz de cores/textos.
2. Confirmar o ponto exato de montagem final do corpo do PR (identificado no contexto obrigatório) e implementar `generate_pr_badge.py` conectando resultado de review real → `ReviewSummaryForBadge` → `badge_builder` → inserção no corpo.
3. Adicionar a flag de opt-out (`GITPR_BADGE` / config `branding.pr_badge`), replicando exatamente a convenção já usada por `GITPR_COAUTHOR`.
4. Integrar no fluxo de `gitpr pr` em `core.py`, validando manualmente contra um PR real (ou mock de API) que o badge aparece corretamente no corpo publicado.
5. Implementar o comando avulso `gitpr badge --readme` com as opções de estilo.
6. Adicionar a mensagem de transparência no `gitpr --init` (ou ponto equivalente de primeira execução) explicando a feature e como desabilitar.
7. Atualizar `config.schema.yml` e documentação (README/CLI help), incluindo o próprio badge de README como exemplo vivo no README do projeto (dogfooding — o GitPR usando seu próprio badge é a melhor demonstração pública da feature).
8. Rodar suite completa de testes do projeto antes de considerar a feature concluída.

Cada etapa deve ser um commit/PR isolado e revisável.

## 10. Encaixe estratégico (contexto de monetização)

Classificada como Tier 1 (alto impacto, baixo esforço) por depender apenas de um serviço de imagem externo gratuito (shields.io) e de dados que o motor de review já produz — nenhuma infraestrutura nova. Fica inteiramente no tier **Free/Community**, com função exclusiva de marketing: cada PR público gerado com o GitPR ativo se torna uma peça de exposição orgânica gratuita, visível para qualquer pessoa que revise aquele PR, incluindo em repositórios open source de terceiros. Isso é o mesmo princípio já usado (e validado) pelo trailer `Co-Authored-By`, estendido de um trailer de texto discreto para um elemento visual mais chamativo. O cuidado central, já reforçado por esta mesma linha de produto, é que nada disso pode ser silencioso ou forçado — a mesma resistência que análises anteriores identificaram como risco para o trailer de coautoria se aplica, com mais intensidade ainda, a um badge visualmente mais visível.
