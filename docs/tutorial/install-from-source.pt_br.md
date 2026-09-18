# Instalando o GitPR do código-fonte (e desbloqueando o portão de versão)

Este guia é para quem roda o GitPR a partir de um **checkout local** em vez do
pacote publicado no PyPI, e que esbarra no bloqueio de atualização obrigatória
por causa disso.

> Se o seu objetivo é apenas testar uma alteração antes de publicar uma nova
> versão no PyPI, a receita mais curta em
> [testar_sem_usar_pypi.md](testar_sem_usar_pypi.md) pode bastar. Este guia vai
> além: explica **por que** o bloqueio de atualização continua disparando numa
> instalação do fonte e o que fazer a respeito.

---

## 1. O sintoma

Você instalou o GitPR a partir do repositório, com a flag de modo editável:

```bash
pip install -e .
```

E, mesmo assim, toda vez que executa, o GitPR se recusa a funcionar:

```text
⚠️ A new version of GitPR is available: 1.1.0 -> 1.2.0
GitPR must be updated before it can run: pip install --upgrade gitpr-cli
```

O processo sai com status diferente de zero e não faz trabalho nenhum. Rodar
`pip install --upgrade gitpr-cli` é o movimento óbvio, mas é exatamente o que
você **não** quer: ele substitui o seu checkout pelo pacote publicado.

---

## 2. Instalando do código-fonte (modo editável)

O comando é `pip install -e .` — o `-e` vem de *editable* e o ponto é o
diretório atual.

```bash
git clone https://github.com/gitpr-cli/gitpr.git
cd gitpr
pip install -e .
```

> Atenção ao **espaço e ao ponto** no final de `-e .`. O ponto significa
> "instale o pacote deste diretório"; sem ele, o pip procura no PyPI um pacote
> com esse nome literal e falha.

Confirme que o ponto de entrada foi criado:

```bash
gitpr --version
```

No modo editável o Python não copia os arquivos — ele liga a distribuição
instalada diretamente ao seu diretório de trabalho. Salvar um arquivo no editor
já basta para a alteração valer na próxima execução do `gitpr`, sem reinstalar.

---

## 3. Por que o bloqueio de atualização ainda dispara

Esta é a parte que surpreende: **não é uma instalação quebrada**. É o portão de
atualização funcionando como projetado, sobre um checkout que está atrás da
release publicada.

O portão fica em `enforce_update_required()` ([src/updater.py](../../src/updater.py))
e compara duas versões:

| Versão | De onde vem |
| --- | --- |
| Remota | `https://pypi.org/pypi/gitpr-cli/json`, com cache de 24h em `~/.gitpr/update_cache.json` |
| Local | `__version__`, no topo de `src/updater.py` |

A execução é bloqueada quando a versão remota é **maior** que a local. A
pegadinha está no lado *local*: numa instalação editável, o `src/updater.py` é
lido da **sua árvore de trabalho**, não de uma cópia congelada no momento da
instalação. O que `__version__` disser no checkout que você tem aberto é a
versão que o GitPR reporta — e, portanto, a versão que o portão compara.

O cenário da falha fica assim:

| | Valor |
| --- | --- |
| Publicado no PyPI | `1.2.0` |
| `__version__` no seu checkout | `1.1.0` |
| Resultado | bloqueado em todos os comandos |

Um segundo sintoma, mais sutil, do mesmo mecanismo: `git stash`,
`git checkout` ou `git switch` para um branch anterior ao último corte de
release volta a bloquear o GitPR na hora, porque o arquivo em disco mudou mesmo
sem nada ter sido reinstalado.

---

## 4. Desbloqueando — opção A (recomendada): alinhe-se à release

A correção direta é fazer a árvore em que você trabalha reportar uma versão
**maior ou igual** à que o PyPI publica. Na prática:

```bash
git switch main
git pull
pip install -e .
gitpr -u
```

O `gitpr -u` (`--update`) nunca é bloqueado, então é a forma mais segura de
confirmar a situação antes de rodar algo mais pesado. Ele imprime a comparação e
o comando de atualização, e não instala nada.

Rode `pip install -e .` de novo também após um `git pull` ou uma troca de branch
que adicione ou renomeie módulos. O link editável cobre a árvore de código, mas
um ponto de entrada ou dependência novos no `pyproject.toml` só chegam à
distribuição instalada com um `pip install -e .` novo.

> **Não edite `__version__` à mão para forjar uma versão.** Aumentar a string
> sem cortar uma release corrompe o que o `gitpr -u` reporta e esconde uma
> necessidade real de atualização. O marcador de versão é definido pelo processo
> de release, não pela conveniência do desenvolvedor.

---

## 5. Desbloqueando — opção B: `GITPR_SKIP_UPDATE_CHECK` (uso local)

O GitPR lê uma chave de ambiente que silencia a verificação por completo.
Acrescente uma linha ao arquivo de configuração global `~/.gitpr/.env`:

```bash
# ~/.gitpr/.env
GITPR_SKIP_UPDATE_CHECK=1
```

Salve o arquivo e rode o GitPR de novo — o bloqueio sumiu.

**Use isto apenas para desenvolvimento local e offline.** Não é substituto para
atualizar uma instalação de release: enquanto a chave estiver ligada, um GitPR
genuinamente desatualizado roda em silêncio, sem aviso e sem proteção contra
comportamento que já foi corrigido upstream.

Quatro detalhes que vale conhecer antes de contar com ela:

- **Qualquer valor não-vazio desliga a verificação** — incluindo `0`, `false` e
  `no`. A chave é lida como flag simples (`bool(os.environ.get(..., "").strip())`),
  não é interpretada como booleano. Só um valor vazio ou com apenas espaços
  mantém a verificação ligada. Definir `GITPR_SKIP_UPDATE_CHECK=` portanto **não
  faz nada**.
- **Não é uma chave de `DEFAULT_CONFIG`.** Ela não aparece na TUI de
  configuração e não é criada pelo assistente de instalação — você precisa
  adicionar a linha ao `~/.gitpr/.env` à mão.
- **Ela funciona através do carregamento do dotenv.** O `~/.gitpr/.env` é
  carregado em tempo de import, antes de o portão rodar, e é por isso que
  escrevê-la no arquivo funciona igual a exportá-la no shell. Exportá-la para um
  único comando também funciona:

  ```bash
  GITPR_SKIP_UPDATE_CHECK=1 gitpr -c
  ```

- **Para religar a verificação**, apague a linha do `~/.gitpr/.env` (ou
  sobrescreva com um valor vazio) e reinicie o GitPR.

---

## 6. O que nunca é bloqueado

Não é toda invocação que passa pelo portão. A verificação é dispensada para:

| Contexto | Motivo |
| --- | --- |
| `--quiet` | Scripts e automação que descartam a saída |
| `--hook` | Hooks de git — nunca podem quebrar um commit |
| `--mcp` / `gitpr-mcp` | Servidor MCP consumido por IDEs e agentes |
| `-u` / `--update` | É justamente o comando que explica como atualizar |
| `-h --<flag>` | Ajuda contextual |
| `--help` / `--version` | O Click resolve ambos antes de o corpo do comando rodar |
| **Qualquer subcomando** | `gitpr fix`, `gitpr review-pr`, `gitpr release`, `gitpr init` despacham antes do portão |
| Offline | Quando a versão remota é desconhecida, a execução prossegue — um usuário offline nunca pode ficar trancado fora de um comando que não consegue consertar |

Num checkout bloqueado, portanto, `gitpr -u` e os subcomandos continuam
utilizáveis para diagnóstico, mesmo sem a chave de ambiente.

---

## 7. Verificando a instalação

Confirme qual modo está ativo:

```bash
pip list --editable
```

O `gitpr-cli` deve aparecer na lista. Num pip mais antigo, procure um diretório
`gitpr_cli.egg-info/` na raiz do repositório — a presença dele é a assinatura de
uma instalação editável.

> Apareceu `WARNING: Ignoring invalid distribution ~itpr-cli`? São diretórios
> `~itpr_cli-*.dist-info` deixados em `site-packages` por uma operação do `pip`
> interrompida — o pip renomeia uma distribuição para `~<nome>` antes de
> apagá-la, e uma execução abortada deixa a renomeação para trás. São restos
> inertes que o pip ignora; apague-os à mão se o aviso incomodar.

Depois confirme a versão reportada:

```bash
gitpr -u
```

Compare a versão local impressa ali com a linha `__version__` do
`src/updater.py` do checkout que você tem aberto. Se forem diferentes, a
instalação está apontando para outro lugar que não a árvore que você pensa estar
editando.

---

## 8. Voltando para a instalação do PyPI

Quando terminar de desenvolver localmente:

```bash
pip uninstall gitpr-cli
pip install --upgrade gitpr-cli
```

Depois limpe o que o modo editável deixou para trás:

- remova a linha `GITPR_SKIP_UPDATE_CHECK` do `~/.gitpr/.env`;
- apague o diretório `gitpr_cli.egg-info/` na raiz do repositório (é metadado de
  build descartável);
- confirme com `pip list --editable`, que não deve mais listar `gitpr-cli`.

---

## Veja também

- [auto-update.md](../auto-update.pt_br.md) — o atualizador automático e o bloqueio de atualização obrigatória
- [testar_sem_usar_pypi.md](../testar_sem_usar_pypi.md) — como testar sem gastar versão no PyPI
- [ARCHITECTURE.md](../ARCHITECTURE.md) — mapa de módulos e fluxo de comandos
