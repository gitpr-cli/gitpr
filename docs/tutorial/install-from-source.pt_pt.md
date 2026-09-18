# Instalar o GitPR a partir do código-fonte (e desbloquear o portão de versão)

Este guia é para quem executa o GitPR a partir de um **checkout local** em vez do
pacote publicado no PyPI, e que por isso esbarra no bloqueio de atualização
obrigatória.

> Se o seu objetivo é apenas testar uma alteração antes de publicar uma nova
> versão no PyPI, a receita mais curta em
> [testar_sem_usar_pypi.md](testar_sem_usar_pypi.md) pode ser suficiente. Este
> guia vai mais longe: explica **porque** é que o bloqueio de atualização
> continua a disparar numa instalação do código-fonte e o que fazer quanto a
> isso.

---

## 1. O sintoma

Instalou o GitPR a partir do repositório, com a flag de modo editável:

```bash
pip install -e .
```

E, mesmo assim, de cada vez que o executa, o GitPR recusa-se a funcionar:

```text
⚠️ A new version of GitPR is available: 1.1.0 -> 1.2.0
GitPR must be updated before it can run: pip install --upgrade gitpr-cli
```

O processo termina com um estado diferente de zero e não faz trabalho nenhum.
Executar `pip install --upgrade gitpr-cli` é o movimento óbvio, mas é
exatamente o que **não** quer: substitui o seu checkout pelo pacote publicado.

---

## 2. Instalar a partir do código-fonte (modo editável)

O comando é `pip install -e .` — o `-e` vem de *editable* e o ponto é o
diretório atual.

```bash
git clone https://github.com/gitpr-cli/gitpr.git
cd gitpr
pip install -e .
```

> Atenção ao **espaço e ao ponto** no final de `-e .`. O ponto significa
> "instala o pacote deste diretório"; sem ele, o pip procura no PyPI um pacote
> com esse nome literal e falha.

Confirme que o ponto de entrada foi criado:

```bash
gitpr --version
```

No modo editável o Python não copia os ficheiros — liga a distribuição
instalada directamente ao seu diretório de trabalho. Gravar um ficheiro no
editor basta para a alteração valer na execução seguinte do `gitpr`, sem
reinstalar.

---

## 3. Porque é que o bloqueio de atualização continua a disparar

Esta é a parte que surpreende: **não é uma instalação avariada**. É o portão de
atualização a funcionar como foi concebido, sobre um checkout que está atrás da
release publicada.

O portão está em `enforce_update_required()` ([src/updater.py](../../src/updater.py))
e compara duas versões:

| Versão | De onde vem |
| --- | --- |
| Remota | `https://pypi.org/pypi/gitpr-cli/json`, com cache de 24h em `~/.gitpr/update_cache.json` |
| Local | `__version__`, no topo de `src/updater.py` |

A execução é bloqueada quando a versão remota é **maior** que a local. O
pormenor está no lado *local*: numa instalação editável, o `src/updater.py` é
lido da **sua árvore de trabalho**, não de uma cópia congelada no momento da
instalação. O que `__version__` disser no checkout que tem aberto é a versão que
o GitPR reporta — e, portanto, a versão que o portão compara.

O cenário da falha fica assim:

| | Valor |
| --- | --- |
| Publicado no PyPI | `1.2.0` |
| `__version__` no seu checkout | `1.1.0` |
| Resultado | bloqueado em todos os comandos |

Um segundo sintoma, mais subtil, do mesmo mecanismo: `git stash`,
`git checkout` ou `git switch` para um branch anterior ao último corte de
release volta a bloquear o GitPR de imediato, porque o ficheiro em disco mudou
mesmo sem nada ter sido reinstalado.

---

## 4. Desbloquear — opção A (recomendada): alinhe-se com a release

A correcção directa é fazer com que a árvore em que trabalha reporte uma versão
**maior ou igual** à que o PyPI publica. Na prática:

```bash
git switch main
git pull
pip install -e .
gitpr -u
```

O `gitpr -u` (`--update`) nunca é bloqueado, por isso é a forma mais segura de
confirmar a situação antes de executar algo mais pesado. Imprime a comparação e
o comando de atualização, e não instala nada.

Execute `pip install -e .` novamente também após um `git pull` ou uma troca de
branch que adicione ou renomeie módulos. A ligação editável cobre a árvore de
código, mas um ponto de entrada ou dependência novos no `pyproject.toml` só
chegam à distribuição instalada com um `pip install -e .` novo.

> **Não edite `__version__` à mão para forjar uma versão.** Aumentar a string sem
> cortar uma release corrompe o que o `gitpr -u` reporta e esconde uma
> necessidade real de atualização. O marcador de versão é definido pelo processo
> de release, não pela conveniência do programador.

---

## 5. Desbloquear — opção B: `GITPR_SKIP_UPDATE_CHECK` (uso local)

O GitPR lê uma chave de ambiente que silencia a verificação por completo.
Acrescente uma linha ao ficheiro de configuração global `~/.gitpr/.env`:

```bash
# ~/.gitpr/.env
GITPR_SKIP_UPDATE_CHECK=1
```

Grave o ficheiro e execute o GitPR novamente — o bloqueio desapareceu.

**Use isto apenas para desenvolvimento local e offline.** Não é substituto de
atualizar uma instalação de release: enquanto a chave estiver ligada, um GitPR
genuinamente desatualizado corre em silêncio, sem aviso e sem protecção contra
comportamento que já foi corrigido upstream.

Quatro pormenores que vale a pena conhecer antes de contar com ela:

- **Qualquer valor não vazio desliga a verificação** — incluindo `0`, `false` e
  `no`. A chave é lida como flag simples (`bool(os.environ.get(..., "").strip())`),
  não é interpretada como booleano. Só um valor vazio ou com apenas espaços
  mantém a verificação ligada. Definir `GITPR_SKIP_UPDATE_CHECK=` portanto **não
  faz nada**.
- **Não é uma chave de `DEFAULT_CONFIG`.** Não aparece na TUI de configuração e
  não é criada pelo assistente de instalação — tem de acrescentar a linha ao
  `~/.gitpr/.env` à mão.
- **Funciona através do carregamento do dotenv.** O `~/.gitpr/.env` é carregado
  em tempo de import, antes de o portão correr, e é por isso que escrevê-la no
  ficheiro funciona tal como exportá-la na shell. Exportá-la para um único
  comando também funciona:

  ```bash
  GITPR_SKIP_UPDATE_CHECK=1 gitpr -c
  ```

- **Para voltar a ligar a verificação**, apague a linha do `~/.gitpr/.env` (ou
  sobrescreva com um valor vazio) e reinicie o GitPR.

---

## 6. O que nunca é bloqueado

Não é qualquer invocação que passa pelo portão. A verificação é dispensada para:

| Contexto | Motivo |
| --- | --- |
| `--quiet` | Scripts e automação que descartam a saída |
| `--hook` | Hooks de git — nunca podem quebrar um commit |
| `--mcp` / `gitpr-mcp` | Servidor MCP consumido por IDEs e agentes |
| `-u` / `--update` | É justamente o comando que explica como atualizar |
| `-h --<flag>` | Ajuda contextual |
| `--help` / `--version` | O Click resolve ambos antes de o corpo do comando correr |
| **Qualquer subcomando** | `gitpr fix`, `gitpr review-pr`, `gitpr release`, `gitpr init` despacham antes do portão |
| Offline | Quando a versão remota é desconhecida, a execução prossegue — um utilizador offline nunca pode ficar trancado fora de um comando que não consegue corrigir |

Num checkout bloqueado, portanto, `gitpr -u` e os subcomandos continuam
utilizáveis para diagnóstico, mesmo sem a chave de ambiente.

---

## 7. Verificar a instalação

Confirme qual modo está activo:

```bash
pip list --editable
```

O `gitpr-cli` deve aparecer na lista. Num pip mais antigo, procure um diretório
`gitpr_cli.egg-info/` na raiz do repositório — a presença dele é a assinatura de
uma instalação editável.

> Apareceu `WARNING: Ignoring invalid distribution ~itpr-cli`? São directórios
> `~itpr_cli-*.dist-info` deixados em `site-packages` por uma operação do `pip`
> interrompida — o pip renomeia uma distribuição para `~<nome>` antes de a
> apagar, e uma execução abortada deixa a renomeação para trás. São restos
> inertes que o pip ignora; apague-os à mão se o aviso incomodar.

Depois confirme a versão reportada:

```bash
gitpr -u
```

Compare a versão local impressa aí com a linha `__version__` do
`src/updater.py` do checkout que tem aberto. Se forem diferentes, a instalação
está a apontar para outro sítio que não a árvore que pensa estar a editar.

---

## 8. Voltar à instalação do PyPI

Quando terminar de desenvolver localmente:

```bash
pip uninstall gitpr-cli
pip install --upgrade gitpr-cli
```

Depois limpe o que o modo editável deixou para trás:

- remova a linha `GITPR_SKIP_UPDATE_CHECK` do `~/.gitpr/.env`;
- apague o diretório `gitpr_cli.egg-info/` na raiz do repositório (é metadados
  de build descartáveis);
- confirme com `pip list --editable`, que não deve voltar a listar `gitpr-cli`.

---

## Ver também

- [auto-update.md](../auto-update.pt_pt.md) — o atualizador automático e o bloqueio de atualização obrigatória
- [testar_sem_usar_pypi.md](../testar_sem_usar_pypi.md) — como testar sem gastar versão no PyPI
- [ARCHITECTURE.md](../ARCHITECTURE.md) — mapa de módulos e fluxo de comandos
