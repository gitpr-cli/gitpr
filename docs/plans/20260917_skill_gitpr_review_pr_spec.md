# SPEC — GitPR `--review-pr <n>` (review de PR remoto já aberto)

> Documento de especificação técnica para implementação via Claude Code skill.
> Escopo: permitir que o GitPR revise um Pull Request já aberto na forge (buscando o diff via API), em vez de exigir que o review seja feito apenas sobre o diff local do working tree/branch do autor. Isso estende o público do review de "quem está prestes a abrir o PR" para "quem foi convidado a revisar o PR de outra pessoa".

## 0. Contexto obrigatório antes de codificar

Antes de gerar qualquer código, a skill DEVE:

1. Ler o fluxo de review hoje existente em `core.py` (o mesmo que já usa `get_skill_context` e a skill `.gitpr.pr.md` ou equivalente) e extrair: (a) a função/método exato que hoje recebe um diff e executa o review via IA, (b) o formato de entrada esperado (diff bruto em texto, lista de arquivos+hunks estruturados, ou outro), (c) se essa função já é agnóstica à origem do diff (local vs remoto) ou se está acoplada a `git diff` local.
2. Confirmar se já existe qualquer código parcial relacionado a "revisar PR aberto" — a menção a esse conceito já aparece em discussões anteriores do projeto ("reviewing open PRs" foi citado como parte do fluxo de PR). Se houver uma implementação parcial ou planejada, ler o que já existe antes de propor uma nova função, para não duplicar ou conflitar com trabalho já iniciado.
3. Confirmar em `github_api.py` (ou `ScmProvider`, se a abstração multi-forge de spec anterior já tiver sido implementada) se já existe uma função de obtenção de diff de PR remoto (`get_pull_request_diff`) — essa função já foi especificada na spec multi-forge; confirmar se foi implementada e qual é sua assinatura real antes de assumir a interface.
4. Verificar como o projeto hoje identifica "o PR atual" nos comandos existentes (ex.: se `gitpr pr` já lê algum número de PR do contexto, de uma branch, ou de um arquivo de estado) para manter consistência de UX ao introduzir `--review-pr <n>` como uma nova forma de apontar o alvo do review.
5. Confirmar se o motor de map-reduce/smart excludes (usado para diffs grandes) opera sobre texto de diff genérico ou está acoplado a alguma particularidade do diff local — precisa funcionar igualmente bem com o diff vindo da API remota.
6. Verificar se existe algum mecanismo de cache de review (MD5 ou outro, mencionado em análises anteriores da arquitetura) e como ele gera a chave de cache hoje — a chave precisa ser estendida para incluir a origem do diff (local vs PR remoto + número do PR), evitando colisão entre cache de um review local e de um review de PR remoto sobre o mesmo conteúdo.

Não prosseguir com a implementação sem completar os passos 1–3.

## 1. Escopo da feature

- **Objetivo:** permitir `gitpr --review-pr <n>` (ou `gitpr review --pr <n>`, conforme convenção de flags já estabelecida no projeto — confirmar padrão exato usado por comandos similares antes de fixar a sintaxe final) para revisar um PR identificado pelo número, buscando o diff diretamente da API da forge, sem exigir que o usuário tenha aquela branch localmente ou até mesmo tenha aberto o PR.
- **Casos de uso cobertos:**
  - Revisor que recebeu um PR para avaliar, mas não é o autor e não necessariamente fez checkout da branch.
  - Autor que quer rodar o review de IA sobre o estado atual do PR já publicado (útil após pushes adicionais).
  - Uso em CI/pipeline dirigido por número de PR (ex.: acionado por webhook/Action) em vez de pelo diff do runner local.
- **Comportamento de saída:** deve reaproveitar o mesmo pipeline de review já usado para diff local — mesma classificação de achados, mesmo formato de saída (Markdown/TUI/JSON, conforme o que já existir), e mesma possibilidade de alimentar `gitpr fix` (spec anterior) sobre os findings resultantes.
- **Publicação de comentários:** nesta fase, o resultado do review de PR remoto deve poder ser publicado como comentário no PR (reaproveitando `add_comment` do `ScmProvider`/`github_api.py`, já especificado anteriormente), como uma opção explícita (`--post-comment`), não automática por padrão.
- **Fora de escopo nesta fase:** review incremental (revisar apenas o que mudou desde o último review automatizado do mesmo PR — isso é uma otimização futura), comentários inline por linha (a spec de comentários inline já foi mapeada separadamente em outra análise como feature própria), suporte a forges além das já cobertas pela abstração `ScmProvider`/`github_api.py` existente no momento desta implementação.
- **Compatibilidade:** o fluxo de review local (`gitpr -r` ou equivalente) não deve ter nenhuma alteração de comportamento. A nova função deve ser um caminho de entrada adicional para o mesmo motor de review, não uma reescrita dele.

## 2. Árvore de arquivos a criar/alterar

```
src/application/use_cases/
└── review_remote_pr.py         # NOVO — orquestra: resolver PR -> obter diff remoto -> normalizar -> executar review existente -> (opcional) publicar comentário

src/infrastructure/scm/
└── (extensão de github_provider.py / demais providers)  # CONFIRMAR/COMPLETAR get_pull_request_diff já especificado

src/domain/review/
└── diff_source.py               # NOVO — abstrai a origem do diff (local vs remoto) para o motor de review existente consumir de forma agnóstica

core.py                          # ALTERAR — nova flag --review-pr <n>, roteamento para review_remote_pr.py
main.py (ou entrypoint CLI)       # ALTERAR — parsing da nova flag/comando

tests/application/use_cases/
└── test_review_remote_pr.py
tests/domain/review/
└── test_diff_source.py
```

## 3. Contrato de dados (obrigatório)

```python
# src/domain/review/diff_source.py
from dataclasses import dataclass
from enum import Enum


class DiffOrigin(str, Enum):
    LOCAL = "local"           # git diff do working tree/branch local
    REMOTE_PR = "remote_pr"   # diff obtido via API de um PR já aberto


@dataclass
class DiffSource:
    origin: DiffOrigin
    content: str                  # diff unificado, já normalizado, pronto para o motor de review consumir
    identifier: str               # ex.: hash do diff local, ou "pr-123" para remoto
    pr_number: int | None         # preenchido apenas quando origin == REMOTE_PR
    repo_ref: "RepoRef | None"    # reaproveitar RepoRef já definido na spec multi-forge, quando origin == REMOTE_PR
    base_branch: str | None
    head_branch: str | None
```

```python
# src/application/use_cases/review_remote_pr.py
from dataclasses import dataclass


@dataclass
class ReviewRemotePrResult:
    pr_number: int
    pr_url: str
    review_result: "ReviewResult"   # reaproveitar o mesmo tipo já usado pelo review local, se existir
    comment_posted: bool
    comment_url: str | None
    warnings: list[str]             # ex.: "PR grande, aplicado map-reduce", "diff obtido via fallback X"


def review_remote_pr(
    pr_number: int,
    scm_provider,           # instância já resolvida via factory de ScmProvider / github_api.py
    ai_provider,             # instância já resolvida via ai_providers.py
    repo_ref,                 # RepoRef do repositório atual (detectado do remote local)
    post_comment: bool = False,
    skill_context=None,       # mesmo get_skill_context() já usado no review local, para manter paridade de regras
) -> ReviewRemotePrResult:
    ...
```

## 4. Algoritmo — pipeline completo

1. **Resolver o repositório alvo.** Detectar `RepoRef` a partir do remote local (`git remote get-url origin`), reaproveitando `parse_repo_ref` do `ScmProvider` já existente/especificado — o usuário roda `gitpr --review-pr <n>` de dentro do repositório clonado, mesmo que não tenha feito checkout da branch do PR.
2. **Obter o diff do PR remoto.** Chamar `scm_provider.get_pull_request_diff(repo_ref, pr_number)`. Se essa função ainda não tiver sido implementada para o provider ativo (conforme confirmado no passo 0.3), a skill deve implementá-la seguindo exatamente a especificação já definida na spec multi-forge anterior, sem redefinir o contrato.
3. **Obter metadados do PR** (branches de origem/destino, título, descrição) via `list_open_pull_requests` filtrando pelo número, ou via uma chamada de detalhe de PR único — usar o que já estiver disponível na interface; se `ScmProvider` ainda não tiver um método de "get PR por número" (distinto de "listar todos abertos"), avaliar se vale adicionar `get_pull_request(repo, pr_number)` ao contrato como extensão mínima, documentando a mudança de interface.
4. **Normalizar em `DiffSource`** com `origin=REMOTE_PR`, preenchendo `pr_number`, `repo_ref`, `base_branch`, `head_branch`.
5. **Aplicar o mesmo pipeline de pré-processamento já usado no review local**: map-reduce para diffs grandes, smart excludes (arquivos gerados/vendorizados/lockfiles), cache — reaproveitando os módulos existentes, agora alimentados por `DiffSource` em vez de diff local direto. A chave de cache deve incorporar `identifier` (que para remoto inclui o número do PR e, idealmente, o hash do diff obtido) para não colidir com cache de reviews locais.
6. **Executar o motor de review de IA existente** passando o conteúdo normalizado — sem duplicar lógica de prompt/skill: usar exatamente `get_skill_context()` e o restante do pipeline hoje usado por `gitpr -r`/review local, garantindo que as mesmas regras/skills configuradas pelo time (`.gitpr.pr.md` ou equivalente) se apliquem igualmente a um review de PR remoto.
7. **Renderizar o resultado** no mesmo formato já suportado (Markdown/TUI/JSON) — não introduzir um formato de saída paralelo.
8. **Se `--post-comment` for informado**, montar um corpo de comentário a partir do `ReviewResult` (resumo + achados) e publicar via `scm_provider.add_comment(repo_ref, pr_number, body)`, já especificado na interface `ScmProvider`. Sem essa flag, o resultado fica apenas local (terminal/TUI/arquivo), sem qualquer efeito colateral na forge.
9. **Tratar diffs indisponíveis/PR inexistente/fechado** com mensagem de erro clara antes de qualquer chamada de IA — falhar rápido, sem gastar tokens/chamadas de provider em um número de PR inválido.

## 5. Integração com `core.py` e CLI

```python
# core.py — nova flag
def cmd_review(args):
    if args.review_pr is not None:
        repo_ref = scm_provider.parse_repo_ref(get_git_remote_url())
        result = review_remote_pr(
            pr_number=args.review_pr,
            scm_provider=resolve_scm_provider(config["scm"]),
            ai_provider=resolve_ai_provider(config),
            repo_ref=repo_ref,
            post_comment=args.post_comment,
            skill_context=get_skill_context(config),
        )
        render_review_result(result.review_result)   # mesma função de renderização já usada no review local
        if args.post_comment:
            log.info(f"Comentário publicado: {result.comment_url}")
    else:
        # fluxo de review local já existente, inalterado
        ...
```

Manter a mesma função de renderização (`render_review_result` ou equivalente já existente) para os dois fluxos garante que a saída visual seja idêntica entre review local e review de PR remoto — o usuário não deve perceber uma ferramenta diferente, apenas uma origem de diff diferente.

## 6. Config

Não é esperado que esta feature precise de novas chaves de configuração além do que já existe para `scm:` (token, provider, base_url) especificado na spec multi-forge — reaproveitar integralmente. Único ponto a confirmar: se `post_comment` deve ter um default configurável (`review.remote_pr_auto_comment: false`) para times que queiram sempre comentar automaticamente sem precisar da flag em cada chamada.

```yaml
review:
  remote_pr_auto_comment: false   # se true, --review-pr sempre publica comentário, sem precisar de --post-comment explícito
```

## 7. Testes obrigatórios (critério de aceite)

1. **Teste de resolução de repositório remoto**: `parse_repo_ref` a partir do remote local deve produzir o mesmo `RepoRef` usado pelo restante do fluxo, sem exigir configuração adicional além do já existente para `scm:`.
2. **Teste de obtenção de diff remoto** (mock de API): `get_pull_request_diff` retornando um diff válido deve alimentar corretamente o `DiffSource`; resposta de erro HTTP (404 PR não encontrado, 403 sem permissão) deve propagar como erro claro para o usuário, não como exceção genérica não tratada.
3. **Teste de paridade de pipeline**: dado o mesmo conteúdo de diff, o resultado do review via `DiffSource(origin=LOCAL)` e via `DiffSource(origin=REMOTE_PR)` deve ser idêntico (mesmas skills aplicadas, mesma classificação de achados) — validando que não há lógica de review duplicada ou divergente entre os dois caminhos.
4. **Teste de map-reduce em diff remoto grande**: PR remoto com diff acima do limite de chunking deve acionar o mesmo mecanismo de map-reduce já testado para diffs locais grandes.
5. **Teste de cache sem colisão**: rodar review local e review remoto sobre conteúdo de diff idêntico não deve reaproveitar a mesma entrada de cache indevidamente (a menos que isso seja uma decisão intencional documentada) — validar que a chave de cache distingue a origem.
6. **Teste de publicação de comentário**: com `--post-comment`, `add_comment` deve ser chamado com o `repo_ref` e `pr_number` corretos e um corpo de comentário não vazio; sem a flag, `add_comment` nunca deve ser invocado.
7. **Teste de PR inexistente/fechado**: número de PR inválido ou já mesclado/fechado deve retornar erro claro antes de qualquer chamada ao provider de IA (nenhuma chamada de IA deve ocorrer nesse caso — validar via mock que o provider de IA não foi invocado).
8. **Teste de não-regressão do review local**: toda a suíte de testes já existente para o fluxo `gitpr -r`/review local deve continuar passando sem alteração após a introdução de `DiffSource` como camada intermediária.

Critério de "feature completa": todos os testes acima passam; `gitpr --review-pr <n>` funciona de ponta a ponta contra um repositório de teste com PR mockado; a saída é visualmente indistinguível (mesmo formato) da saída do review local, exceto pelos metadados de origem (número do PR, branches).

## 8. Ordem de execução recomendada

1. Confirmar (ou implementar, se ainda não existir) `get_pull_request_diff` no `ScmProvider`/`github_api.py` ativo, conforme já especificado na spec multi-forge — não prosseguir sem essa função disponível e testada.
2. Implementar `diff_source.py` (dataclass + enum, sem lógica de I/O) — camada puramente estrutural.
3. Refatorar o ponto de entrada do motor de review existente para aceitar `DiffSource` como parâmetro em vez de (ou além de) diff local bruto, garantindo que o fluxo local continue funcionando idêntico (passo crítico de não-regressão — validar com a suíte de testes existente antes de seguir).
4. Implementar `review_remote_pr.py` conectando resolução de repo + obtenção de diff remoto + `DiffSource` + motor de review já refatorado.
5. Adicionar a extensão de cache (chave incluindo origem/identificador) e validar ausência de colisão com testes dedicados.
6. Registrar a flag `--review-pr <n>` em `core.py`/CLI, incluindo `--post-comment`.
7. Implementar a publicação de comentário via `add_comment`, atrás da flag.
8. Atualizar `config.schema.yml` (chave opcional `remote_pr_auto_comment`) e documentação (README/CLI help).
9. Rodar a suíte completa de testes do projeto, com atenção especial aos testes já existentes de review local, antes de considerar a feature concluída.

Cada etapa deve ser um commit/PR isolado e revisável. A etapa 3 (refatoração do motor de review existente para aceitar `DiffSource`) é a mais sensível — deve ser validada isoladamente, com a suíte de testes de review local passando 100% antes de prosseguir para as etapas seguintes.

## 9. Encaixe estratégico (contexto de monetização)

Classificada como Tier 1 (alto impacto, baixo esforço) porque reaproveita majoritariamente infraestrutura já especificada (obtenção de diff remoto via `ScmProvider`, motor de review, cache, skills) — o trabalho novo real é a camada de orquestração (`review_remote_pr.py`) e a normalização (`DiffSource`). Fica no tier **Free/Community**: expande o público de usuário de "quem abre PRs" para "quem revisa PRs", o que é estrategicamente relevante porque multiplica o número de pessoas em uma equipe que interagem com o GitPR sem custo adicional de infraestrutura — cada revisor que usa `--review-pr` é um usuário a mais tocando o produto e potencial promotor interno da adoção em equipe, que é exatamente o gargalo identificado nas análises de monetização como pré-requisito para conversão ao tier Team (mais pessoas usando o GitPR na mesma organização torna a venda de Policy Sync/Dashboard agregado mais natural).

## 10. Documentação

1. Crie a sua documentação própria em docs/
2. Adicione em README.md e em suas versões em outros idiomas
3. Se alguma variável ambiente foi criada e utilizada nesta feature adicionar na interface de Configuração na seção nova Review PR 