# SPEC — GitPR `fix` Command (generalização do auto-patch do chat)

> Documento de especificação técnica para implementação via Claude Code skill.
> Escopo: generalizar o mecanismo de auto-patch hoje disponível apenas dentro do chat interativo (atalhos F5 / `ctrl+shift+s`) em um comando de primeira classe (`gitpr fix`), capaz de aplicar sugestões de review como diff revisável, com dry-run como comportamento padrão e nunca aplicando alterações sem confirmação explícita.

## 0. Contexto obrigatório antes de codificar

Antes de gerar qualquer código, a skill DEVE:

1. Localizar e ler o código exato do chat TUI que implementa o atalho `F5` e o atalho `ctrl+shift+s` (podem ser o mesmo handler ou dois handlers distintos — confirmar isso primeiro, pois a memória do usuário indica ambos os atalhos associados a "auto-patch"/extração de patch). Documentar: (a) como o patch é extraído da resposta da IA hoje (regex de bloco de código, parsing de diff unificado, ou outro método), (b) como/se o patch é aplicado hoje (via `git apply`, escrita direta de arquivo, ou outro mecanismo), (c) se há alguma validação antes da aplicação atual.
2. Confirmar se existe hoje algum **modelo de finding estruturado** (severidade, categoria, arquivo, linha, sugestão) produzido pelo review de IA, ou se o review retorna apenas texto/Markdown livre. Isso define se `gitpr fix` pode operar por ID de finding (ex.: `gitpr fix SEC-001`) ou precisa operar sobre o review completo como um bloco único nesta primeira versão.
3. Verificar se o projeto já implementou alguma normalização de saída de IA em JSON estruturado (schema de finding) mencionada em análises anteriores — se sim, reaproveitar esse schema; se não, esta feature deve definir um schema mínimo próprio, documentado na seção 3 abaixo, sem tentar resolver a normalização completa do produto nesta entrega.
4. Confirmar a interface real de `ai_providers.py` para reaproveitar o mesmo mecanismo de chamada de IA já usado no chat, evitando duplicar lógica de prompt/parsing.
5. Verificar se o projeto já tem alguma abstração de execução de comandos Git (wrapper sobre `git apply`, `git stash`, criação de branch) — reaproveitar em vez de duplicar chamadas de subprocess espalhadas.
6. Confirmar convenção de nomes de branch já usada pelo projeto (ex.: prefixos de branch de feature/fix gerados automaticamente em outros comandos) para manter consistência na branch criada por `gitpr fix --create-branch`.

Não prosseguir com a implementação sem completar os passos 1–3. Se o chat hoje aplica patch de forma direta e não-revisável, isso é uma mudança de comportamento relevante que deve ser destacada ao usuário antes da implementação (ver seção 8, compatibilidade).

## 1. Escopo da feature

- **Objetivo:** transformar a extração/aplicação de patch — hoje restrita ao chat interativo via atalho — em um comando de CLI de primeira classe, com fluxo seguro e auditável: `dry-run` por padrão, aplicação explícita via `--apply`, e opção de aplicar tudo que for classificado como seguro via `--all-safe`.
- **Comandos/flags novos:**
  - `gitpr fix <finding-id> --dry-run` (ou sem flag — dry-run é o default) — mostra o diff que seria aplicado, sem tocar em arquivos.
  - `gitpr fix <finding-id> --apply` — aplica o patch no working tree, exigindo confirmação interativa salvo se `--yes`/`--force` for informado.
  - `gitpr fix --all-safe` — aplica todos os patches classificados como `safe` (ver critério na seção 4), pulando os classificados como `review-required` ou `experimental`.
  - `gitpr fix --all-safe --create-branch <nome>` — cria uma branch nova antes de aplicar, nunca commitando direto na branch atual.
  - `gitpr fix --list` — lista os findings do último review que têm patch sugerido disponível, com classificação de segurança e resumo, sem aplicar nada.
  - `gitpr fix <finding-id> --rollback` — desfaz um patch já aplicado por este comando (ver seção 6).
- **Fora de escopo nesta fase:** aplicação automática em CI sem qualquer intervenção humana (mesmo `--all-safe` deve ser um comando explícito rodado por alguém, não um hook automático de pipeline nesta entrega), geração de testes automáticos para validar o patch (é feature relacionada mas separada, já mapeada como "Testes como primeira classe" em outra análise), patch multi-arquivo com dependências cruzadas complexas (nesta fase, cada finding gera um patch isolado por arquivo/hunk).
- **Compatibilidade:** os atalhos `F5`/`ctrl+shift+s` do chat devem continuar funcionando exatamente como hoje. Internamente, porém, devem passar a chamar a mesma camada de use case (`apply_fix.py`) usada pelo comando novo, para eliminar duplicação de lógica — não é aceitável manter dois caminhos de código distintos fazendo a mesma extração/aplicação de patch.

## 2. Árvore de arquivos a criar/alterar

```
src/domain/fix/
├── patch_extractor.py         # NOVO (ou migrado da lógica hoje embutida no chat)
├── patch_safety_classifier.py # NOVO — classifica patch em safe / review-required / experimental
└── patch_provenance.py        # NOVO — registra qual finding/modelo/prompt gerou o patch

src/application/use_cases/
├── apply_fix.py                # NOVO — orquestra: localizar finding -> obter/gerar patch -> classificar -> validar -> aplicar ou dry-run
└── rollback_fix.py             # NOVO — desfaz aplicação anterior via registro de proveniência

src/infrastructure/git/
└── patch_applier.py            # NOVO (ou extraído de utilitário git já existente) — wrapper sobre git apply / git stash / git checkout -b

src/ui/chat/                    # ALTERAR — handlers de F5 e ctrl+shift+s passam a chamar apply_fix.py em vez de lógica própria
core.py ou main.py               # ALTERAR — registrar comando `gitpr fix` e subflags

.gitpr/fix_history.json          # NOVO (arquivo de estado local) — histórico de patches aplicados para suportar --rollback

tests/domain/fix/
├── test_patch_extractor.py
└── test_patch_safety_classifier.py
tests/application/use_cases/
├── test_apply_fix.py
└── test_rollback_fix.py
```

## 3. Contrato de dados (obrigatório)

```python
# src/domain/fix/patch_provenance.py
from dataclasses import dataclass
from enum import Enum


class PatchSafety(str, Enum):
    SAFE = "safe"                     # mudança mecânica, baixo risco (ex.: import faltante, formatação)
    REVIEW_REQUIRED = "review_required"  # mudança de lógica, requer olhar humano antes de aceitar
    EXPERIMENTAL = "experimental"      # baixa confiança do modelo, ou patch multi-hunk complexo


@dataclass
class FindingRef:
    id: str                    # ex.: "SEC-001" — deve casar com o schema de finding do produto, se existir
    file_path: str
    line_start: int
    line_end: int
    severity: str
    category: str
    message: str


@dataclass
class PatchCandidate:
    finding: FindingRef
    diff_unified: str          # patch em formato unified diff, pronto para git apply
    safety: PatchSafety
    safety_reason: str         # texto curto explicando a classificação
    suggested_test: str | None # descrição textual de teste sugerido, se o provider retornar
    provenance: "PatchProvenance"


@dataclass
class PatchProvenance:
    finding_id: str
    ai_provider: str           # "gemini" | "deepseek" | "ollama"
    ai_model: str
    prompt_version: str
    generated_at: str          # ISO 8601
    gitpr_version: str


@dataclass
class ApplyFixResult:
    applied: bool               # False em modo dry-run
    branch_created: str | None
    files_changed: list[str]
    patch_id: str                # identificador único, usado para --rollback
    dry_run_diff: str | None     # preenchido quando applied=False
    warnings: list[str]          # ex.: "hunk não aplicou limpo, conflito detectado"
```

## 4. Algoritmo — pipeline completo

1. **Resolver o(s) finding(s) alvo.** Se `gitpr fix <finding-id>` for chamado com um ID específico, localizar esse finding no resultado do último review executado (ler do cache/output já persistido pelo review, conforme mecanismo existente no projeto). Se `--all-safe`, iterar todos os findings do último review que tenham patch sugerido.
2. **Obter ou gerar o patch.** Se o review já retornou um patch sugerido para o finding (extraído via `patch_extractor.py`, reaproveitando a lógica hoje usada por F5/`ctrl+shift+s`), usar diretamente. Se o review só descreveu o problema em texto sem patch, disparar uma chamada adicional ao provider de IA configurado, pedindo especificamente um patch em formato unified diff para aquele finding — reaproveitando `ai_providers.py`.
3. **Validar sintaticamente o patch** antes de qualquer classificação: tentar um `git apply --check` (dry-run nativo do Git) contra o working tree atual. Se falhar, marcar como `EXPERIMENTAL` automaticamente e adicionar warning — nunca prosseguir para aplicação real de um patch que falha na validação sintática.
4. **Classificar segurança do patch** (`patch_safety_classifier.py`) usando heurísticas determinísticas, não outra chamada de IA (para manter previsibilidade e custo zero nesta etapa):
   - `SAFE`: patch de um único hunk, altera menos de N linhas (configurável, default 5), não toca em arquivos de migration/schema/CI/CD/infra (lista de padrões de caminho sensível, reaproveitando conceito de "área crítica" já discutido nas análises de risk scoring), e não remove nenhuma linha que contenha uma chamada de função pré-existente (heurística simples para evitar quebra de assinatura).
   - `REVIEW_REQUIRED`: qualquer patch que não se qualifique como `SAFE` mas passou na validação sintática do passo 3.
   - `EXPERIMENTAL`: falhou na validação sintática, ou o provider de IA sinalizou baixa confiança (se o schema de resposta da IA incluir esse campo), ou o patch abrange múltiplos arquivos.
5. **Registrar proveniência** (`PatchProvenance`): qual finding, provider, modelo, versão de prompt e versão do GitPR geraram o patch — persistir isso junto ao resultado para auditoria futura e para suportar rollback preciso.
6. **Modo dry-run (default):** exibir o diff completo (via terminal com syntax highlight, se o projeto já tiver esse recurso em outro comando, ou texto simples) e a classificação de segurança, sem tocar em nenhum arquivo. Retornar `ApplyFixResult(applied=False, dry_run_diff=...)`.
7. **Modo `--apply`:**
   - Se `--create-branch` for informado (ou for o comportamento default ao usar `--all-safe`, a confirmar com o usuário na primeira revisão desta spec), criar a branch nova a partir do `HEAD` atual antes de aplicar qualquer patch.
   - Exigir confirmação interativa explícita (exibindo o diff) antes de aplicar, salvo `--yes` informado.
   - Aplicar via `git apply` (não escrever arquivo diretamente — preservar a granularidade de hunks e permitir que falhas de aplicação sejam reportadas pelo próprio Git).
   - Após aplicar, gravar entrada em `.gitpr/fix_history.json` com `patch_id`, arquivos alterados, hash do patch aplicado e timestamp — necessário para `--rollback` funcionar.
   - Rodar teste sugerido/existente relacionado ao arquivo, **se o projeto já tiver esse mecanismo implementado** (não bloquear esta feature esperando a feature de "Testes como primeira classe" — apenas verificar se já existe algo reaproveitável; se não existir, pular esta etapa e registrar warning informativo).
8. **Modo `--all-safe`:** repetir os passos 6–7 apenas para findings classificados como `SAFE`; findings `REVIEW_REQUIRED`/`EXPERIMENTAL` devem ser listados no resumo final como "não aplicados automaticamente — use `gitpr fix <id> --apply` individualmente".

```python
# src/application/use_cases/apply_fix.py
def apply_fix(
    finding_id: str | None,       # None quando --all-safe
    all_safe: bool,
    apply: bool,                  # False = dry-run
    create_branch: str | None,
    ai_provider,
    repo_path: str,
    require_confirmation: bool = True,
) -> list[ApplyFixResult]:
    ...
```

## 5. Integração com o chat existente (F5 / `ctrl+shift+s`)

Requisito explícito de não-duplicação: os handlers desses atalhos devem ser refatorados para chamar `apply_fix.py` internamente. Diferença de UX a preservar: dentro do chat, o fluxo pode continuar sendo mais direto (menos telas de confirmação que o comando standalone, já que o usuário está em contexto interativo olhando a resposta da IA), mas a **extração e classificação do patch** deve vir do mesmo código, não de uma implementação paralela. Se hoje o chat aplica o patch diretamente sem passar por validação sintática (`git apply --check`) ou sem registrar proveniência, esta é uma melhoria de segurança que deve ser aplicada retroativamente ao fluxo do chat como parte desta entrega, não apenas ao comando novo.

## 6. Rollback

```python
# src/application/use_cases/rollback_fix.py
def rollback_fix(patch_id: str, repo_path: str) -> bool:
    """
    Lê .gitpr/fix_history.json, localiza o patch_id, e reverte
    usando `git apply --reverse` sobre o mesmo diff armazenado.
    Deve falhar com mensagem clara se o working tree já foi
    modificado de forma incompatível desde a aplicação original
    (ex.: hash do arquivo mudou e o reverse não aplica limpo).
    """
```

Persistir o diff completo (não apenas metadados) em `fix_history.json` é o que torna o rollback determinístico — não depender de `git revert` de commit, já que o usuário pode não ter commitado o patch ainda.

## 7. Config

```yaml
fix:
  safe_max_lines_changed: 5
  safe_excluded_paths:
    - "database/migrations/**"
    - "**/*.ci.yml"
    - "docker/**"
    - "terraform/**"
  require_confirmation: true      # false só deve ser possível via --yes explícito na linha de comando, nunca via config silenciosa para --apply isolado
  create_branch_on_all_safe: true
  branch_name_template: "fix/gitpr-{date}"
```

## 8. Compatibilidade e riscos a comunicar ao usuário

- Se a investigação do passo 0.1 revelar que o chat hoje aplica patches **sem** validação sintática prévia ou **sem** possibilidade de rollback, isso deve ser reportado como um gap de segurança encontrado durante a implementação, não silenciosamente corrigido sem menção — o comportamento do chat vai mudar (ainda que para melhor), e isso deve estar visível no changelog da versão que introduzir esta feature.
- Nunca aplicar patch `EXPERIMENTAL` mesmo com `--all-safe` ou `--yes` — a única forma de aplicar um patch experimental é via `gitpr fix <id> --apply` individual e explícito, exibindo um aviso adicional de baixa confiança antes da confirmação.
- `--force` (se implementado como alias de "pular confirmação e ignorar classificação de segurança") é uma flag de alto risco — se for adicionada, deve exigir digitação de confirmação textual (não apenas `y/n`) para evitar execução acidental em script.

## 9. Testes obrigatórios (critério de aceite)

1. **Teste de extração de patch** (`test_patch_extractor.py`): cobrir extração a partir do formato de resposta real da IA hoje usado pelo chat (bloco de código com diff, ou o formato que a investigação do passo 0.1 revelar), incluindo casos de resposta malformada (sem patch algum) retornando `None`/erro tratado, não exceção não tratada.
2. **Teste de classificação de segurança** (`test_patch_safety_classifier.py`): matriz cobrindo cada critério de `SAFE` isoladamente (linhas alteradas, caminho excluído, remoção de assinatura de função) e combinações; patch que falha `git apply --check` deve sempre cair em `EXPERIMENTAL`, independentemente de outros critérios.
3. **Teste de dry-run**: `apply_fix` com `apply=False` nunca deve escrever no working tree — validar isso com um `git status` limpo antes e depois da chamada em teste de integração.
4. **Teste de `--all-safe` seletivo**: dado um conjunto misto de findings com patches `SAFE`, `REVIEW_REQUIRED` e `EXPERIMENTAL`, apenas os `SAFE` devem ser aplicados; os demais devem aparecer no resumo como não aplicados.
5. **Teste de criação de branch**: `--create-branch` deve criar a branch a partir do `HEAD` correto e aplicar o patch nela, sem alterar a branch original.
6. **Teste de proveniência**: todo patch aplicado deve gerar uma entrada correspondente em `fix_history.json` com todos os campos de `PatchProvenance` preenchidos.
7. **Teste de rollback**: aplicar um patch, reverter via `rollback_fix`, e confirmar que o working tree retorna ao estado anterior (diff vazio contra o commit original). Testar também o caso de falha (arquivo modificado externamente após a aplicação) retornando erro claro em vez de corromper o arquivo.
8. **Teste de não-duplicação de lógica**: teste (pode ser de revisão de código/lint arquitetural, não necessariamente automatizado) confirmando que os handlers de `F5`/`ctrl+shift+s` chamam `apply_fix.py` e não contêm lógica própria de extração/aplicação de patch duplicada.
9. **Teste de regressão do chat**: os atalhos `F5` e `ctrl+shift+s` devem continuar funcionando com a mesma UX percebida (mesmas teclas, mesmo resultado visível ao usuário) após a refatoração para usar a camada compartilhada.

Critério de "feature completa": todos os testes acima passam; nenhum patch é aplicado ao working tree sem passar por dry-run prévio (seja explícito via comando, seja implícito via validação sintática antes de qualquer `--apply`); rollback funciona de forma determinística para os casos cobertos em teste.

## 10. Ordem de execução recomendada

1. Investigar e documentar o comportamento atual exato de F5/`ctrl+shift+s` (passo 0.1) antes de escrever qualquer código novo — esta etapa não gera código de produção, apenas um relatório curto de achados para confirmar com o usuário se algo além do previsto nesta spec precisa mudar.
2. Extrair `patch_extractor.py` a partir da lógica hoje embutida no chat, sem alterar comportamento observável do chat ainda — apenas mover o código para o novo módulo e fazer o chat chamá-lo.
3. Implementar `patch_safety_classifier.py` (lógica pura, sem I/O) com testes de matriz completa.
4. Implementar `patch_applier.py` (wrapper sobre `git apply --check` / `git apply` / `git apply --reverse` / criação de branch) com testes de integração usando repositório git de fixture.
5. Implementar `apply_fix.py` conectando extração + validação + classificação + aplicação/dry-run, com teste de integração ponta a ponta.
6. Implementar `patch_provenance.py` e a escrita/leitura de `.gitpr/fix_history.json`.
7. Implementar `rollback_fix.py` com testes cobrindo sucesso e falha por incompatibilidade.
8. Registrar o comando `gitpr fix` em `core.py`/CLI com todas as subflags.
9. Refatorar os handlers de `F5`/`ctrl+shift+s` para chamar a camada compartilhada, validando que a UX do chat não regride (teste manual + teste automatizado de regressão).
10. Atualizar `config.schema.yml` e documentação (README/CLI help), incluindo a nota de changelog sobre a melhoria de segurança no fluxo do chat, se aplicável (ver seção 8).
11. Rodar suite completa de testes do projeto antes de considerar a feature concluída.

Cada etapa deve ser um commit/PR isolado e revisável. Não implementar extração, classificação, aplicação e refatoração do chat em um único commit grande — a refatoração do chat (etapa 9) em particular deve vir depois que toda a lógica compartilhada já estiver testada isoladamente, para minimizar risco de regressão em uma feature que os usuários já usam hoje.

## 11. Encaixe estratégico (contexto de monetização)

Classificada como Tier 1 (alto impacto, baixo esforço) por generalizar um mecanismo que já existe e funciona no chat, sem exigir nova infraestrutura de rede ou backend. Fica no tier **Free/Community**: é uma feature de produtividade individual que reduz a distância entre "a IA encontrou um problema" e "o problema está corrigido", que é exatamente a objeção de compra mais comum contra ferramentas de review que "só apontam problemas". Ao mesmo tempo, a infraestrutura de proveniência (`PatchProvenance`) e classificação de segurança construída aqui é o que permite, no futuro tier **Team/Enterprise**, oferecer auditoria de quem aplicou qual correção sugerida por IA, e políticas organizacionais restringindo `--all-safe` a determinados tipos de finding — sem precisar refazer esta base.
