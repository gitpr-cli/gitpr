# ADR-0021 — Semântica de Avaliação Estrita do Switch de Verificação de Atualização (`GITPR_SKIP_UPDATE_CHECK`)

- **Status:** Aceito
- **Data:** 2026-11-11
- **Decisores:** Natan Fiuza, Antigravity
- **Contexto:** Transição da avaliação de `GITPR_SKIP_UPDATE_CHECK` de teste simples de presença de string para um parser booleano estrito (`_SKIP_TRUTHY_VALUES`).
- **Relacionados:** [ADR-0014 (Canonical Package Version SSOT)](0014-canonical-package-version-ssot.md), [Auto-Updater Documentation (`docs/auto-update.md`)](../auto-update.md), [Tutorial: Installing from Source (`docs/tutorial/install-from-source.md`)](../tutorial/install-from-source.md)
- **Glossário:** [CONTEXT.md](../../CONTEXT.md) (`Update check switch`)

---

## 1. Contexto

O GitPR é distribuído exclusivamente via PyPI (`pip install gitpr-cli`). Para proteger os usuários de comportamentos inconsistentes ou bugs já corrigidos upstream, o `src/updater.py` executa o **portão de atualização obrigatório** (*mandatory update gate*): quando uma versão publicada no PyPI é estritamente superior à versão local informada em `src/updater.py::__version__`, o GitPR bloqueia a execução interativa até que o pacote seja atualizado.

Para cenários legítimos de desenvolvimento local a partir de checkouts clonados do repositório (`pip install -e .`) e automações de testes offline, o GitPR disponibiliza a variável de ambiente `GITPR_SKIP_UPDATE_CHECK`.

### O Comportamento Legado (< v1.4.3)
Nas versões anteriores à 1.4.3, o código verificava apenas a presença ou falsidade simples da variável no ambiente:
```python
# Comportamento antigo (pseudo-código conceitual)
if os.environ.get("GITPR_SKIP_UPDATE_CHECK"):
    # Qualquer string não vazia silenciava o portão
    return True
```
Sob essa semântica ingênua baseada em presença, qualquer string não vazia — incluindo strings como `"false"`, `"0"`, `"off"`, `"no"`, `"n"` ou espaços — era avaliada pelo Python como truthy, desativando o portão de atualização.

### A Quebra de Contrato e o Problema com Automações
Muitos mantenedores de automações, contêineres e scripts de CI configuravam explicitamente flags no shell ou arquivos `.env` como:
```bash
GITPR_SKIP_UPDATE_CHECK=false
# ou
GITPR_SKIP_UPDATE_CHECK=0
```
com a intenção semântica expressa em inglês ("não pular a checagem" ou "manter a checagem ativa"). No entanto, quando esses mesmos scripts eram executados em ambientes onde a intenção do autor do script era silenciar a verificação (ou onde o script tratava `false` como "desligar o mecanismo de aviso"), o comportamento gerava inconsistências gritantes com as convenções modernas de CLI e POSIX para flags booleanas.

A partir da v1.4.3, o `src/updater.py` introduziu um **parser booleano estrito**:
```python
SKIP_UPDATE_CHECK_ENV = "GITPR_SKIP_UPDATE_CHECK"
_SKIP_TRUTHY_VALUES = ("1", "true", "yes", "on", "y")

def is_update_check_disabled():
    """Returns True when the update check must be muted for this execution."""
    value = os.environ.get(SKIP_UPDATE_CHECK_ENV, "")
    return value.strip().lower() in _SKIP_TRUTHY_VALUES
```

Essa correção necessária criou uma **quebra semântica para automações legadas**:
- Scripts que setavam `GITPR_SKIP_UPDATE_CHECK=false` ou `0` esperando silenciar a checagem com base no comportamento antigo agora têm o valor avaliado como falso.
- Consequentemente, a checagem **permanece ativa** e o portão bloqueia comandos interativos se a working tree local estiver desatualizada em relação ao PyPI.

---

## 2. Decisão

Formaliza-se a avaliação estrita de `GITPR_SKIP_UPDATE_CHECK`:

1. **Parser Booleano Estrito Mandatório**:
   Apenas valores normalizados (`strip().lower()`) presentes em `_SKIP_TRUTHY_VALUES` (`"1"`, `"true"`, `"yes"`, `"on"`, `"y"`) desativam a checagem de atualização.
2. **Tratamento de Valores Falsos e Inválidos**:
   Valores como `"0"`, `"false"`, `"no"`, `"off"`, `"n"`, strings vazias ou palavras não reconhecidas são categoricamente avaliados como falsos, mantendo a checagem de atualização ativada.
3. **Sem Shims Silenciosos**:
   Não reverter nem criar exceções para strings como `"false"` desativarem o portão.
4. **Governança Documental e Notas de Migração**:
   - Manter notas de migração com destaque visual (`> [!WARNING]`) tanto na documentação técnica (`docs/auto-update.*.md`) quanto no tutorial prático (`docs/tutorial/install-from-source.*.md`) em todos os 5 idiomas suportados (`en_us`, `pt_br`, `pt_pt`, `es_es`, `fr_fr`).
   - Assegurar paridade contínua e imutabilidade dos alertas através de testes unitários automatizados (`tests/unit/test_auto_update_docs_parity.py`).
   - Manter o termo canônico `Update check switch` documentado no `CONTEXT.md`.

---

## 3. Consequências

### Positivas
- Elimina comportamentos ambíguos e acidentais onde scripts que tentavam desativar o bypass acabavam ativando-o por engano.
- Alinha o GitPR às boas práticas de interpretação de variáveis de ambiente do ecossistema UNIX e Python.
- Previne falsos negativos na suíte de testes e em esteiras de validação.

### Negativas / Riscos e Remediação
- Scripts de automação ou receitas Docker/devcontainer legadas que definiam `GITPR_SKIP_UPDATE_CHECK=false` esperando silenciar a verificação agora veem o comando falhar ao encontrar uma versão mais nova no PyPI.
- **Remediação Obrigatória**: Atualizar os scripts de automação e pipelines para definir explicitamente `GITPR_SKIP_UPDATE_CHECK=1` ou `GITPR_SKIP_UPDATE_CHECK=true`.
