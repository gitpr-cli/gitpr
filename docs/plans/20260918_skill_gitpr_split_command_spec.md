# SPEC — GitPR `split` Command (commits/PRs atômicos por hunk)

> Documento de especificação técnica para implementação via Claude Code skill.
> Escopo: analisar um diff com mudanças misturadas (múltiplas preocupações não relacionadas no mesmo working tree) e propor/executar sua separação em commits atômicos por hunk, usando IA para agrupar hunks por intenção lógica.

## 0. Contexto obrigatório antes de codificar

Antes de gerar qualquer código, a skill DEVE:

1. Ler a implementação do motor de **map-reduce e smart excludes** já existente (usado para diffs grandes no review) e extrair: (a) como o diff é hoje parseado em unidades (arquivo inteiro, hunk, linha), (b) se já existe algum parser de diff unificado para hunks individuais com metadados (arquivo, linha inicial/final, conteúdo do hunk) que possa ser reaproveitado diretamente, (c) qual biblioteca é usada para parsing de diff (regex própria, `unidiff`, `whatthepatch`, ou outra) — reaproveitar exatamente essa mesma biblioteca/parser, não introduzir uma segunda forma de interpretar diffs no projeto.
2. Confirmar a interface real de `ai_providers.py` para reaproveitar o mesmo mecanismo de chamada de IA já usado na geração de commit/PR — o agrupamento de hunks por intenção lógica é uma tarefa de classificação que precisa de IA, e deve usar o mesmo Strategy Pattern.
3. Confirmar se o `apply_fix.py`/`patch_applier.py` já foram implementados (spec anterior "GitPR fix Command") — se sim, reaproveitar o wrapper de `git apply`/manipulação de patches já construído ali, em vez de duplicar lógica de aplicação de hunks parciais.
4. Verificar como o projeto hoje gera mensagens de commit semânticas (fluxo padrão de `gitpr` sem flags, ou `gitpr --commit`) para reaproveitar exatamente essa mesma função na geração de mensagem de cada commit atômico resultante do split — cada grupo de hunks deve gerar sua mensagem de commit pelo mesmo pipeline já existente, não por um caminho novo.
5. Confirmar se existe alguma abstração de "staging seletivo" (equivalente a `git add -p`/`git apply --cached` por hunk) já usada em algum ponto do projeto — se não existir, esta feature precisa implementá-la do zero, e isso deve ser destacado como o componente de maior risco técnico da entrega (manipular o índice do Git por hunk é uma operação sensível a erros).
6. Confirmar se `core.py` já tem algum conceito de "modo interativo com preview antes de confirmar" (o PR Publisher TUI provavelmente já tem isso) para reaproveitar o mesmo padrão de confirmação explícita antes de aplicar qualquer split real.

Não prosseguir com a implementação sem completar os passos 1–4. O passo 5, em particular, deve ser reportado explicitamente ao usuário antes da implementação começar, já que define se a feature é uma extensão de algo existente ou uma capacidade nova de manipulação de índice Git construída do zero.

## 1. Escopo da feature

- **Objetivo:** dado um working tree com mudanças não commitadas cobrindo múltiplas preocupações (ex.: uma correção de bug + uma refatoração + uma mudança de configuração, tudo misturado), o GitPR analisa o diff, agrupa os hunks por intenção lógica usando IA, e propõe N commits atômicos — cada um com apenas os hunks relacionados e uma mensagem de commit gerada especificamente para aquele subconjunto.
- **Comando novo:** `gitpr split` com subopções:
  - `gitpr split --dry-run` (comportamento default, mesmo sem a flag) — mostra os grupos propostos e a mensagem de commit de cada um, sem tocar no índice/working tree.
  - `gitpr split --apply` — executa de fato os commits atômicos propostos, em sequência, exigindo confirmação explícita antes de iniciar.
  - `gitpr split --interactive` — permite ao usuário revisar/editar/mesclar os grupos propostos pela IA antes de aplicar (via TUI, reaproveitando componentes Textual já existentes no projeto).
  - `gitpr split --max-groups <n>` — limite superior de quantos commits atômicos a IA deve propor (evita over-splitting em diffs muito grandes; default sugerido: 5).
- **Fluxo alvo:**
  1. Capturar o diff completo do working tree (staged + unstaged, ou apenas um dos dois — confirmar com o usuário qual é o comportamento esperado antes de fixar; sugestão de default: todas as mudanças não commitadas, staged e unstaged juntas, tratadas de forma unificada).
  2. Parsear o diff em hunks individuais com metadados (arquivo, linhas, conteúdo).
  3. Enviar a lista de hunks (não o diff bruto inteiro de uma vez, para permitir que a IA raciocine sobre unidades discretas) para o provider de IA configurado, pedindo agrupamento por intenção lógica com justificativa curta por grupo.
  4. Para cada grupo proposto, gerar uma mensagem de commit semântica usando o pipeline de commit já existente, mas alimentado apenas pelos hunks daquele grupo (não pelo diff completo).
  5. Exibir o plano completo (grupos + mensagens) para confirmação.
  6. Se aprovado, aplicar cada grupo como um commit atômico e sequencial: stage seletivo dos hunks daquele grupo → commit com a mensagem gerada → repetir para o próximo grupo.
- **Fora de escopo nesta fase:** split automático de PRs já publicados na forge (ex.: fechar um PR grande e abrir N PRs menores automaticamente) — esta primeira versão opera apenas sobre commits locais ainda não publicados; divisão de um único hunk em partes menores (a unidade mínima de divisão nesta versão é o hunk inteiro, não sub-hunk); undo automático de um split já aplicado (usar os mecanismos padrão do Git — `git reset`/`reflog` — não é necessário construir um rollback dedicado como foi feito para `gitpr fix`, já que aqui o resultado são commits normais, reversíveis pelas ferramentas Git padrão).
- **Compatibilidade:** a feature não deve alterar nenhum arquivo do working tree além do índice Git (staging) durante o processo — o conteúdo final dos arquivos após todos os commits deve ser idêntico ao estado original antes do `gitpr split`, apenas distribuído em múltiplos commits em vez de um estado não commitado único.

## 2. Árvore de arquivos a criar/alterar

```
src/domain/split/
├── hunk_parser.py               # NOVO (ou reaproveitado do parser de diff já existente no map-reduce)
├── hunk_grouper.py                # NOVO — lógica de orquestração do agrupamento via IA
└── split_plan.py                  # NOVO — dataclasses do plano de split (grupos, mensagens, ordem)

src/infrastructure/git/
└── selective_stager.py            # NOVO — stage seletivo de hunks específicos (git apply --cached com patch parcial)

src/application/use_cases/
└── generate_split_plan.py         # NOVO — orquestra: diff -> hunks -> agrupamento IA -> mensagens de commit -> plano final
└── apply_split_plan.py            # NOVO — executa o plano: stage seletivo + commit, grupo a grupo

src/ui/split/                      # NOVO (se --interactive for implementado nesta fase) — TUI de revisão/edição dos grupos propostos

core.py ou main.py                  # ALTERAR — registrar comando `gitpr split` e subflags

tests/domain/split/
├── test_hunk_parser.py
├── test_hunk_grouper.py
└── test_split_plan.py
tests/infrastructure/git/
└── test_selective_stager.py
tests/application/use_cases/
├── test_generate_split_plan.py
└── test_apply_split_plan.py
```

## 3. Contrato de dados (obrigatório)

```python
# src/domain/split/split_plan.py
from dataclasses import dataclass, field


@dataclass
class Hunk:
    file_path: str
    hunk_header: str          # ex.: "@@ -10,6 +10,8 @@"
    content: str               # conteúdo bruto do hunk, incluindo header, pronto para aplicação parcial
    line_start_old: int
    line_start_new: int
    id: str                    # identificador estável dentro da execução (ex.: hash do conteúdo do hunk)


@dataclass
class HunkGroup:
    group_id: str
    intent_label: str          # ex.: "fix: validação de e-mail", curto, gerado pela IA
    justification: str          # explicação da IA de por que esses hunks formam um grupo coeso
    hunks: list[Hunk]
    generated_commit_message: str | None   # preenchido após a etapa de geração de mensagem


@dataclass
class SplitPlan:
    groups: list[HunkGroup]     # ordem em que os commits serão aplicados, se aprovado
    ungrouped_hunks: list[Hunk]  # hunks que a IA não conseguiu classificar com confiança — tratamento explícito, nunca descartados silenciosamente
    total_hunks: int
    warnings: list[str]          # ex.: "diff muito grande, truncado a N hunks para análise"
```

```python
# src/application/use_cases/generate_split_plan.py
def generate_split_plan(
    repo_path: str,
    ai_provider,
    max_groups: int = 5,
    include_staged: bool = True,
    include_unstaged: bool = True,
) -> SplitPlan:
    ...
```

```python
# src/application/use_cases/apply_split_plan.py
@dataclass
class ApplySplitResult:
    commits_created: list[str]     # hashes dos commits criados, em ordem
    groups_applied: int
    groups_skipped: int             # ex.: grupos que o usuário removeu no modo interativo antes de aplicar
    warnings: list[str]

def apply_split_plan(plan: SplitPlan, repo_path: str, require_confirmation: bool = True) -> ApplySplitResult:
    ...
```

## 4. Algoritmo — pipeline completo

1. **Capturar o diff bruto** (staged + unstaged conforme flags), reaproveitando exatamente a mesma função de obtenção de diff já usada pelo restante do produto — não reimplementar chamada a `git diff`.
2. **Parsear em `Hunk`s individuais** com metadados completos, reaproveitando o parser de diff já existente no motor de map-reduce (confirmado no passo 0.1). Cada hunk recebe um `id` estável (ex.: hash do `file_path + hunk_header + content`) usado para rastreabilidade ao longo do pipeline.
3. **Tratar diffs muito grandes**: se o número total de hunks exceder um limite configurável (ex.: 50), aplicar o mesmo princípio de smart excludes já usado no review (excluir lockfiles, arquivos gerados, binários) antes de enviar à IA, e registrar warning se ainda assim o volume for grande demais para uma única chamada — neste caso, considerar dividir a classificação em lotes (reaproveitando a lógica de map-reduce já existente), mantendo a coerência do agrupamento final.
4. **Montar o prompt de agrupamento**: enviar a lista de hunks (arquivo + header + um trecho do conteúdo, não necessariamente o hunk completo se isso estourar limite de contexto) pedindo à IA que retorne uma estrutura JSON com grupos, cada um contendo os `id`s dos hunks pertencentes, um `intent_label` curto, e uma `justification`. Exigir que a IA retorne também uma lista de hunks que não conseguiu classificar com confiança (`ungrouped_hunks`) em vez de forçar todo hunk a pertencer a algum grupo.
5. **Validar a resposta da IA contra os `id`s reais dos hunks enviados**: todo `id` retornado pela IA deve corresponder a um hunk de fato existente no diff original — descartar/reportar como warning qualquer `id` inventado pela IA, nunca aplicar um grupo com referência a hunk inexistente.
6. **Gerar mensagem de commit por grupo**: para cada `HunkGroup`, montar um diff sintético contendo apenas os hunks daquele grupo, e passar esse diff reduzido pelo mesmo pipeline de geração de mensagem de commit já usado no fluxo padrão do GitPR (reaproveitar 100% dessa lógica, apenas trocando a entrada).
7. **Exibir o plano completo** (grupos, intenção, justificativa, mensagem de commit gerada, e a lista de `ungrouped_hunks` se houver) para o usuário — em modo `--dry-run` (default), parar aqui.
8. **Modo `--interactive`**: permitir reordenar grupos, mesclar dois grupos em um, mover um hunk de um grupo para outro, ou remover um grupo da aplicação (mantendo seus hunks como não commitados ao final) — via TUI Textual reaproveitando componentes já existentes no projeto.
9. **Modo `--apply`**: para cada grupo, na ordem definida no plano:
   - **Stage seletivo dos hunks daquele grupo** via `selective_stager.py` (ver seção 5) — nenhum outro hunk deve ser incluído no stage durante esta operação.
   - Commitar com a mensagem gerada para aquele grupo.
   - Confirmar que o índice está limpo dos hunks daquele grupo antes de prosseguir para o próximo (evitar vazamento de hunks entre grupos por erro de staging).
10. **Ao final**, hunks em `ungrouped_hunks` (se existirem) permanecem não commitados no working tree — o usuário decide manualmente o que fazer com eles (incluindo rodar `gitpr split` novamente sobre o restante, ou commitá-los manualmente).

## 5. `selective_stager.py` — componente de maior risco técnico

Esta é a peça mais delicada da feature: aplicar apenas um subconjunto de hunks ao índice do Git, preservando os demais como não commitados.

```python
# src/infrastructure/git/selective_stager.py
def stage_hunks(hunks: list[Hunk], repo_path: str) -> None:
    """
    Monta um patch unificado contendo apenas os hunks informados (com headers
    de arquivo corretos reconstruídos a partir de Hunk.file_path) e aplica
    via `git apply --cached <patch>`.

    Requisitos de segurança:
    - Validar com `git apply --cached --check <patch>` antes de aplicar de fato.
    - Se a validação falhar (hunks com dependência de contexto entre si que
      não podem ser aplicados isoladamente — cenário real e esperado quando
      hunks do mesmo arquivo estão próximos ou se sobrepõem), levantar uma
      exceção específica (`HunkConflictError`) capturada pelo use case, que
      deve then tratar esses hunks conflitantes como um grupo único forçado
      (mesclar os grupos automaticamente) em vez de falhar silenciosamente.
    - Nunca fazer stage de hunks fora da lista informada — validar o estado
      do índice antes e depois da operação.
    """

def unstage_all(repo_path: str) -> None:
    """Reverte qualquer stage parcial em caso de erro no meio do processo, restaurando o estado original."""
```

**Risco explícito a documentar**: hunks do mesmo arquivo que estão próximos um do outro no diff original podem ter dependência de contexto (o `git apply` de um hunk isolado pode falhar se as linhas de contexto ao redor dependem de outro hunk não aplicado ainda). A skill deve implementar a validação via `--check` antes de qualquer aplicação real, e ter uma estratégia explícita de fallback (mesclar hunks conflitantes no mesmo grupo) em vez de assumir que hunks são sempre independentes entre si.

## 6. Config

```yaml
split:
  max_groups: 5
  min_confidence_to_group: 0.6      # se o schema de resposta da IA incluir confiança por grupo; caso não inclua, remover este campo
  include_staged_by_default: true
  include_unstaged_by_default: true
```

## 7. Testes obrigatórios (critério de aceite)

1. **Teste de parsing de hunks**: dado um diff multi-arquivo conhecido, `hunk_parser` deve extrair exatamente os hunks esperados com metadados corretos (arquivo, headers, conteúdo, ids estáveis e determinísticos entre execuções para o mesmo diff).
2. **Teste de validação de resposta da IA**: se a IA retornar um `id` de hunk inexistente no diff original, o pipeline deve descartar essa referência e registrar warning, sem lançar exceção não tratada e sem incluir um hunk fantasma em nenhum grupo.
3. **Teste de preservação de conteúdo**: aplicar um `SplitPlan` completo (todos os grupos, incluindo hunks não agrupados permanecendo no working tree) deve resultar em um estado final de arquivos idêntico byte-a-byte ao estado antes do split — validar via diff do estado final contra uma cópia do estado original salva antes do teste.
4. **Teste de stage seletivo isolado**: `stage_hunks` com um subconjunto de hunks de um diff multi-hunk deve deixar no índice exatamente aqueles hunks, e nenhum outro — validar via `git diff --cached` após a chamada.
5. **Teste de conflito de hunks dependentes**: simular dois hunks do mesmo arquivo com sobreposição de contexto e confirmar que `HunkConflictError` é levantado e tratado (mesclagem automática de grupo), não propagado como falha genérica.
6. **Teste de dry-run**: `generate_split_plan` nunca deve tocar no índice ou working tree — apenas leitura. Validar com `git status` limpo antes/depois.
7. **Teste de reuso do pipeline de mensagem de commit**: a mensagem gerada para cada grupo deve vir da mesma função usada pelo fluxo padrão de commit do GitPR — teste de contrato garantindo que nenhuma lógica de geração de mensagem foi duplicada.
8. **Teste de aplicação sequencial e ordem**: `apply_split_plan` deve criar os commits na ordem definida no plano, e cada commit deve conter exatamente os hunks do seu grupo (validar via `git show <hash>` de cada commit criado contra o conteúdo esperado do grupo).
9. **Teste de rollback em caso de erro no meio da sequência**: se o commit do grupo N falhar por qualquer motivo, os grupos 1 a N-1 já commitados devem permanecer intactos (comportamento esperado documentado — não há rollback automático dos commits já criados, apenas garantia de que o processo para de forma limpa e informa claramente quais grupos foram aplicados e quais não).
10. **Teste de modo interativo** (se implementado nesta fase): mesclar dois grupos via TUI deve produzir um `SplitPlan` atualizado com um grupo a menos e todos os hunks originais preservados na união.

Critério de "feature completa": todos os testes acima passam; rodar `gitpr split --apply` sobre um diff real de teste com 3 preocupações misturadas conhecidas produz 3 commits atômicos corretos e o estado final do repositório é idêntico ao estado antes da operação, apenas distribuído em commits.

## 8. Ordem de execução recomendada

1. Implementar/confirmar `hunk_parser.py` reaproveitando (ou extraindo para reuso) o parser de diff já existente no motor de map-reduce — validar com testes contra diffs reais multi-hunk antes de seguir.
2. Implementar `selective_stager.py` isoladamente, com testes extensivos de stage seletivo e detecção de conflito — este é o componente de maior risco, deve ser validado exaustivamente antes de ser consumido por qualquer camada superior.
3. Implementar `split_plan.py` (dataclasses, sem lógica).
4. Implementar `hunk_grouper.py` conectando o parser de hunks à chamada de IA (via `ai_providers.py`), incluindo a validação de `id`s retornados contra os hunks reais.
5. Implementar `generate_split_plan.py` conectando parsing + agrupamento + geração de mensagem de commit reaproveitada — testável em modo dry-run completo antes de tocar em `apply_split_plan`.
6. Implementar `apply_split_plan.py` conectando `selective_stager` + commit sequencial, com testes de preservação de conteúdo e ordem.
7. Registrar `gitpr split` (com `--dry-run`, `--apply`, `--max-groups`) em `core.py`/CLI.
8. (Opcional, se priorizado) Implementar o modo `--interactive` na TUI, reaproveitando componentes Textual existentes.
9. Atualizar `config.schema.yml` e documentação (README/CLI help).
10. Rodar suite completa de testes do projeto antes de considerar a feature concluída.

Cada etapa deve ser um commit/PR isolado e revisável. As etapas 1 e 2 (parsing e stage seletivo) são pré-requisitos de segurança que devem estar 100% testados antes de qualquer código que dependa deles ser escrito — erros nessas camadas corrompem o histórico Git do usuário, o que é um risco de dado real, não apenas um bug de UX.

## 9. Encaixe estratégico (contexto de monetização)

Classificada como Tier 2 (diferenciação e retenção, médio esforço) porque, ao contrário das features do Tier 1, exige construção de uma capacidade nova de manipulação de índice Git (stage seletivo por hunk) que não é uma simples extensão de código já existente — é a peça de maior risco técnico entre as specs já produzidas nesta série. Fica no tier **Free/Community** como recurso de produtividade individual: é a feature "uau" citada nas análises originais porque é visualmente impressionante em demonstrações (transformar um working tree bagunçado em commits limpos automaticamente) e reforça a narrativa de "GitPR entende a estrutura real do seu código", reforçando indiretamente a credibilidade do produto para a conversão futura aos tiers pagos, sem ela mesma ser uma feature paga.

## 10. Documentação

1. Crie a sua documentação própria em docs/
2. Adicione em README.md e em suas versões em outros idiomas
3. Se alguma variável ambiente foi criada e utilizada nesta feature adicionar na interface de Configuração na seção nova Demo 