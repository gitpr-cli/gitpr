# Documentação Técnica: Ecrã de Configuração Interativo (`gitpr config`)

O GitPR é configurado pelo `~/.gitpr/.env`, um ficheiro dotenv com cerca de cinquenta variáveis. Até agora, alterar uma delas exigia saber o nome exato, abrir o ficheiro à mão e adivinhar se o valor é `true`, `1` ou `yes` — e um valor que o leitor não compreende é engolido em silêncio, pelo que um erro de escrita nunca aparece como erro.

O `gitpr config` abre um ecrã master-detail sobre esse mesmo ficheiro: categorias à esquerda, as definições da selecionada à direita, editadas no local. É uma camada fina sobre o ficheiro que já tem — não uma segunda fonte de configuração.

```bash
gitpr config
```

---

## 1. O Ecrã

```text
┌ Header ──────────────────────────────────────────────┐
│ Configurações      [/ procurar…]  ● 2 não guardadas  │
├──────────────┬───────────────────────────────────────┤
│ Geral        │  Idioma da interface                  │
│ Fornecedores │  [ pt_pt            ▾ ]               │
│ Pull Request │                                       │
│ …            │  Co-autor                             │
│              │  [ ●] habilitado                      │
├──────────────┴───────────────────────────────────────┤
│ F1 Ajuda · F2 Guardar · ^R Restaurar · / Procurar ·  │
└──────────────────────────────────────────────────────┘
```

| Tecla | Ação |
| --- | --- |
| `F1` | Ajuda — a lista de atalhos e como os valores são lidos |
| `F2` | Valida e guarda as alterações pendentes |
| `Ctrl+R` | Restaura o padrão do campo em foco (remove a linha) |
| `/` | Procura um nome de variável ou um rótulo em todas as categorias |
| `Esc` | Sai — ou limpa a procura primeiro; pergunta antes de descartar |

### 1.1 Categorias

O menu lateral espelha os comandos e flags da CLI, pelo que a definição que quer está onde está a funcionalidade que usa. A primeira entrada é sempre **Geral**:

| Categoria | Contém |
| --- | --- |
| **Geral** | Idioma da interface, trailer de co-autor, log geral |
| **Fornecedores de IA** | Motor predefinido, tempo limite da IA, as duas chaves de API, e os modelos de cada fornecedor — numa sub-secção por fornecedor, mostrada uma de cada vez |
| **Pull Request** | `OUTPUT_FILE_NAME`, branch base, auto commit/stage/merge, ignorar linter, log de publicação, sugestão de revisores |
| **Revisão de Código** | `OUTPUT_FILE_NAME_REVIEW`, `_FULLREVIEW`, `_FILEREVIEW` |
| **Issue** | `OUTPUT_FILE_NAME_ISSUE` |
| **Blame** | `OUTPUT_FILE_NAME_BLAME` |
| **Linter** | `OUTPUT_FILE_NAME_LINTER`, `GITPR_LINTER_TIMEOUT` |
| **Release** | Caminho do changelog, resumo por IA, bump automático, rascunho por omissão, `OUTPUT_FILE_NAME_RELEASE` |
| **SCM / Forge** | Fornecedor, token de CI/CD, token da forge, URL base; sub-secções **GitHub**, **Bitbucket** e **Azure DevOps** com o que cada forge precisa |
| **Filtros de Diff** | Chave dos smart excludes e os dois caminhos de lista de filtros |
| **Skills** | Os sete ficheiros de skill deste projeto — uma entrada por skill, editados ali mesmo (§1.7) |
| **Avançado** | Três sub-secções — **Spinner**, **Git Hooks**, **Descarregamentos** — ocultas até ligar **Mostrar avançadas** |
| **Desconhecidas** | Chaves no ficheiro que o schema não declara — aparece só quando existem |

Cada uma das doze categorias liga à sua própria documentação técnica (§1.5).

### 1.2 Controlos

Cada campo recebe o controlo que o seu tipo merece, para que um valor inválido seja difícil de produzir desde o início:

| Tipo | Controlo |
| --- | --- |
| Booleano | Switch |
| Enum | Select |
| Inteiro | Campo de texto, validado |
| Template de nome de ficheiro | Campo de texto, validado contra os placeholders |
| Caminho, texto livre | Campo de texto |
| Segredo | Campo mascarado |
| Lista de palavras | Caixa apenas de leitura que rola sozinha, com a contagem de entradas por cima e um botão de descarregamento (§1.4) |

### 1.3 Filtrado pelo Valor Selecionado

Duas definições decidem que outras definições estão no ecrã, e o painel segue a seleção **imediatamente** — antes de qualquer gravação:

| Quando seleciona | Vê |
| --- | --- |
| Um **Fornecedor Predefinido** | Apenas os modelos desse fornecedor. Sem nada selecionado, não é mostrada nenhuma secção de fornecedor |
| Um **Fornecedor de Forge** | Apenas a sub-secção dessa forge, mais os campos que todas as forges partilham |

A procura ignora o filtro de propósito: procurar `deepseek` com o Gemini selecionado continua a encontrar os modelos DeepSeek, para poder pré-preencher um fornecedor para o qual está prestes a mudar. Um campo oculto com uma edição pendente continua a ser guardado — a visibilidade é uma vista, não uma permissão.

### 1.4 Botões de Descarregamento

Quatro listas são servidas do repositório do GitPR e atualizadas quando o seu marcador de versão muda. **📥 Forçar descarregamento** ao lado de um marcador de versão descarrega-o novamente a pedido, e **📥 Descarregar a lista de palavras** faz o mesmo para as palavras do spinner. Esta é a saída manual para o caso que a verificação automática não consegue ver: a lista está presente, atualizada, e ainda assim não é a que quer.

O botão relata o resultado com honestidade, porque um descarregamento pode falhar e recuar para a cópia que já está em disco sem qualquer forma de distinguir as duas de fora:

| Feedback | Significado |
| --- | --- |
| `✔ v0.0.24` e *"{name} está atualizado ({version})."* | O ficheiro passa a transportar a versão atual — ou acabado de descarregar, ou uma cópia que já estava atual |
| `✖ não actualizado` e *"Não foi possível descarregar {name}. A cópia anterior continua em uso."* | O descarregamento falhou. Nada se perdeu: a cópia anterior está intacta e continua em uso |
| *"O inglês não precisa de pacote de tradução — não há nada para descarregar."* | O pacote de tradução não tem edição em inglês para obter, já que o inglês é incorporado |

O veredicto vem de uma nova leitura do `~/.gitpr/.env` depois do descarregamento, nunca de `os.getenv()`: o `load_dotenv()` corre com `override=False`, pelo que o processo continua a deter o valor com que arrancou.

### 1.5 Ligação para a Documentação

**📚 Documentação** no topo do painel direito abre a documentação técnica da categoria que está a ver, e o URL é impresso ao lado do botão para que o possa ler ou copiar primeiro.

| Categoria | Documento |
| --- | --- |
| Geral | `config-tui.md` |
| Fornecedores de IA | `providers-ia.md` |
| Pull Request | `pull-request-publication.md` |
| Revisão de Código | `code-review-ia.md` |
| Issue | `gitpr-issue-option.md` |
| Blame | `blame-arqueologo.md` |
| Linter | `linter-regras-customizadas.md` |
| Release | `release-notes.md` |
| SCM / Forge | `scm-multiforge.md` |
| Filtros de Diff | `smart-excludes.md` |
| Skills | `skill-template.md` |
| Avançado | `version-markers.md` |

A ligação segue o idioma da interface (`?lang=pt_pt`), e a linha desaparece na vista de procura e em **Desconhecidas**, que não é uma categoria que o GitPR possua.

### 1.6 O Toggle de Avançadas

**Mostrar avançadas** na barra superior revela a categoria `Avançado` e todo o campo marcado como interno. São marcadores de versão que o GitPR mantém sozinho ao descarregar traduções, presets de linter, palavras do spinner e listas de filtros; aparecem por transparência, não para edição. O toggle fica desligado em todas as aberturas.

Duas dessas entradas não são marcadores e vale a pena conhecê-las:

- **Idioma dos hooks** (`SCRIPTS_LANG`) — o idioma em que os Git hooks são instalados. Vazio significa "seguir o idioma da interface", que é o que a maioria dos utilizadores quer; escolher um instala os hooks nesse idioma na execução seguinte. **Idioma dos hooks instalados** ao lado é apenas leitura e regista o que está realmente em disco, para que os dois nunca se confundam.
- **Palavras do spinner** — a própria lista, apenas leitura, na caixa descrita em §1.2.

### 1.7 A Secção Skills

Em todo o resto, o ecrã edita `~/.gitpr/.env`. **Skills** é a única secção que não o faz: edita os ficheiros de skill do próprio projeto — as instruções de IA lidas de `./.gitpr/skill/` ([Sistema de Skills e Templates](skill-template.pt_pt.md)).

A lista tem uma entrada por skill suportada pelo GitPR: **Commit**, **Pull Request**, **Code Review**, **File Review**, **Issue**, **Blame**, **Release**. É a lista das skills que os comandos carregam, e não um espelho da pasta — um ficheiro em `.gitpr/skill/` que nenhum comando lê não é oferecido aqui.

| A entrada mostra | Significado |
| --- | --- |
| nada | O ficheiro existe e permite gravação — edite-o na caixa à direita e pressione `F2` |
| **● editado** | Uma edição sua ainda não foi guardada |
| **não está neste projeto** | O ficheiro não existe. A caixa apresenta *"Este projeto ainda não tem o ficheiro {name}."* e o editor fica desativado — uma caixa vazia seria lida como "esta skill está vazia", que é o oposto do que é verdade |
| **apenas leitura** | O ficheiro existe mas não permite gravação. É apresentado, bloqueado, e não há nada a guardar |

**📥 Descarregar o template** aparece para uma skill ausente e vai buscar o template publicado para o seu idioma de interface, como os botões de descarregamento da §1.4. Quando nem isso pode ser gravado — uma pasta `.gitpr/skill/` sem permissão de escrita — o botão fica desativado com o motivo ao lado.

O `F2` guarda os campos do `.env` **e** os ficheiros de skill na mesma passagem, e o contador de pendências cobre os dois. Dentro do painel, o `Ctrl+R` descarta a edição e devolve o texto do disco — o mais próximo de um padrão que um ficheiro tem — e o `Esc` pergunta antes de descartar, como em todo o resto.

Cada ficheiro mantém o fim de linha que já tinha, por isso um ficheiro `CRLF` continua `CRLF` e o seu diff mostra apenas as linhas que editou.

---

## 2. Como os Valores São Lidos

**O ecrã mostra o que está no ficheiro, não o que o processo está a usar.** A diferença importa, porque o `load_dotenv()` corre com `override=False` em todo o GitPR: quando uma variável também está exportada na sua shell, o ambiente vence e o ficheiro é ignorado em tempo de execução.

Um campo nessa situação é marcado com **⚠ no ambiente**, e o valor no ecrã continua a ser o do ficheiro. Editá-lo é permitido — só não terá efeito enquanto a variável não for removida do ambiente. Isto é propositado: sem a marcação veria um valor que silenciosamente não é o que está em uso, que é a falha mais confusa que este ficheiro pode produzir.

Os valores são lidos com um parser que olha apenas para o ficheiro, nunca com `os.getenv()`, pelo que nada do processo atual se infiltra no ecrã.

---

## 3. Edição e Gravação

Nada é gravado até pressionar `F2`. Enquanto edita, o `F2` mostra um contador de alterações pendentes e o `Esc` pede confirmação antes de sair:

- **Guardar** grava apenas os campos que realmente alterou, pelo que as linhas não relacionadas mantêm os seus comentários e a sua posição no ficheiro.
- **Ficheiros de skill** são gravados na mesma gravação: um `F2` cobre os campos pendentes do `.env` e as skills editadas (§1.7). Uma skill que falha ao gravar é reportada pelo nome e mantém a edição pendente — os outros ficheiros são gravados na mesma.
- **`Ctrl+R`** num campo **não** reescreve o padrão incorporado — marca a linha para **remoção**, para que o valor volte ao que o código define como padrão. O campo apresenta `— será removido —` e um novo `Ctrl+R` desfaz a marcação. Este é o reset honesto: gravar o padrão atual iria congelá-lo no ficheiro e interromper o acompanhamento de alterações futuras ao padrão.
- **Esvaziar um campo** limpa a sobreposição.
- Depois de guardar, o ecrã permanece aberto, relê o ficheiro e informa quantas definições foram guardadas.

### 3.1 Validação

O `F2` valida antes de gravar seja o que for. Um campo que falha ganha contorno vermelho e uma mensagem inline, nada é guardado, e o ecrã salta para o primeiro campo problemático — trocando de categoria e ligando **Mostrar avançadas** se for ali que ele vive.

| Regra | Porquê |
| --- | --- |
| Apenas `true` / `false`, mais `1`/`0`, `yes`/`no`, `y`/`n`, `off` | O GitPR tem dois leitores de booleano que discordam fora deste conjunto. `on` parece simétrico a `off`, mas é lido como **false** por um e como **true** pelo outro |
| Inteiros devem ser maiores que zero | Um tempo limite que não pode ser interpretado é substituído pelo padrão em silêncio, pelo que um erro de escrita nunca aparece como erro |
| Enums devem ser uma das opções declaradas | Um nome de fornecedor desconhecido não é rejeitado no arranque, simplesmente não funciona |
| Templates devem usar placeholders conhecidos e manter `{datetime}` | Um placeholder desconhecido é um `KeyError` no comando seguinte; sem `{datetime}` cada execução resolve para o mesmo nome de ficheiro e sobrescreve o relatório anterior |

### 3.2 Validação de Credencial

Um segredo (chave de API, token da forge) é validado junto do seu fornecedor antes de ser guardado, porque uma credencial errada só é descoberta mais tarde, a meio de um comando real. A validação corre em segundo plano para o ecrã nunca bloquear, e o resultado decide:

| Resultado | Comportamento |
| --- | --- |
| Aceite | Guardada |
| Recusada (HTTP 401/403, ou uma resposta "invalid API key") | **Bloqueia** — a credencial está errada e guardá-la não ajuda ninguém |
| Falha de rede, tempo limite, fornecedor inalcançável | **Guarda com aviso** — uma chave correta escrita atrás de um proxy não pode ser recusada |

Apenas os segredos que alterou nesta sessão são revalidados. Uma chave que já estava no ficheiro e não foi tocada não é sondada a cada gravação.

Valores de segredo **nunca são apresentados de volta**. O campo fica vazio quando nada está guardado, e mostra um placeholder fixo (`•••••••• (definido — escreva para substituir)`) quando existe um valor — a mesma máscara independentemente do segredo, porque o valor real nunca é lido para o ecrã. Só entra na gravação quando escreve algo nele. Os segredos são encriptados em repouso com a chave Fernet local em `~/.gitpr/secret.key`; o ecrã encripta na altura de gravar e nunca desencripta para preencher um campo.

---

## 4. Procura e Chaves Fora do Schema

Escrever na caixa de procura filtra por nome de variável **e** por rótulo, em todas as categorias de uma vez — `timeout` encontra os tempos limite da IA e do linter sem saber em que categoria estão. Enquanto uma procura está ativa, a área principal mostra os resultados como uma lista plana, com uma contagem, em vez dos campos da categoria selecionada; o menu lateral continua onde está. O `Esc` limpa a procura — e devolve o foco ao menu lateral — antes de poder sair do ecrã.

Variáveis presentes no ficheiro que o GitPR não declara caem numa categoria **Desconhecidas** que só aparece quando tais chaves existem. São apenas de leitura: o ecrã nunca grava uma chave que não é dele. Alterar uma significa editar o ficheiro à mão.

---

## 5. Deliberadamente Não Editável

Estas chaves não recebem campo editável. O ecrã nunca esconde uma chave que está no seu ficheiro — recusa-se apenas a **escrever** numa que não é dele — por isso todas menos a última continuam a aparecer, apenas de leitura, em **Desconhecidas** (ver §4).

| Variável | Porquê |
| --- | --- |
| `GITPR_SCM_TOKEN` | O token cru de CI/CD tem precedência sobre o encriptado e é guardado em texto simples. Tem uma linha em **SCM / Forge** — apenas leitura e nunca apresentada — a apontar para `gitpr --init`, que é a única coisa que o deve escrever; um campo editável convidaria a sobrepor o token que aí configurou |
| `PR_AUTO_PUBLISH` | Sobra de antes de publicar passar a ser o fluxo padrão. Lida em lado nenhum: o que a substituiu é a flag `--no-edit`. Uma instalação antiga pode ainda transportar a linha dela no `.env`, e é por isso que aparece em **Desconhecidas** |
| `CI`, `GITHUB_ACTIONS` | Marcadores de ambiente do processo, nunca gravados neste ficheiro, por isso nunca aparecem |

---

## 6. Para Programadores

O ecrã é construído a partir de um schema declarativo, pelo que adicionar uma definição é uma alteração de dados e não de interface.

| Ficheiro | Papel |
| --- | --- |
| `src/config_schema.py` | Dado puro: `ConfigField`, `Category`, `Group`, `CATEGORIES`, `GROUPS`, `FIELDS` (56 campos), mais `fields_of()`, `validate_field_value()` e os auxiliares de procura. Fonte única de verdade para menu, widgets, padrões, sub-secções, visibilidade e validação |
| `src/doc_links.py` | `doc_url(filename)` — o URL base da documentação e a regra do `?lang=`. Separado do `core.py` porque o ecrã não pode importar `src.core`, que puxa os SDKs de IA a cada abertura |
| `src/ui/config_app.py` | `ConfigApp` mais os modais de ajuda e confirmação. Layout master-detail, dirty state, procura, o toggle de avançadas, o filtro de visibilidade, os workers de descarregamento, o painel de Skills (§1.7) e o pipeline de gravação |
| `src/config.py` | Quatro funções novas: `read_env_file_values()`, `save_config_values()`, `remove_config_value()`, `validate_ai_key()`. Guarda também o registo de skills (`SKILL_FILES_BY_TYPE`, `SKILL_TYPES`) e os auxiliares de ficheiro (`read_skill_file()`, `write_skill_file()`, `skill_file_status()`) que o `get_skill_context()` e a secção Skills leem (§1.7) |
| `src/main.py` | O subcomando `config` — sem `setup_environment()`, para que nada possa pedir entrada no stdin dentro da app de ecrã inteiro |

Três atributos de um `ConfigField` determinam o layout: `group` coloca o campo sob um sub-cabeçalho, `show_if` esconde-o a menos que outro campo contenha um dos valores listados, e `action` associa um botão de descarregamento. `version_source` diz que constante apresentar quando um marcador de versão ainda não está no ficheiro — um `LINTER_PRESETS_VERSION` vazio mostra a versão enviada no código em vez de uma caixa vazia.

**Adicionar uma definição:** declare um `ConfigField` com rótulo e descrição literais `__("…")`, adicione a chave ao `DEFAULT_CONFIG` se for um novo padrão de semeação, e traduza as chaves novas nos seis `langs/*.json`. O `tests/test_config_schema.py` falha enquanto o schema e o `DEFAULT_CONFIG` não concordarem — e enquanto um novo `group`, `show_if` ou `action` não apontar para algo que existe — e o `tests/test_i18n.py` falha enquanto cada ficheiro de idioma não transportar as chaves novas.

**Modelo de estado:** as edições pendentes vivem num dicionário indexado pelo nome da variável, não nos widgets. O conjunto de linhas visíveis muda conforme navega ou procura, e um valor lido de volta de um controlo oculto seria frágil — por isso o `F2` é independente do que está no ecrã naquele momento.

**As gravações em disco** passam pelo `set_key()`/`unset_key()` do `python-dotenv`, que escrevem um ficheiro temporário e o renomeiam, preservando comentários e ordem. O ecrã nunca reescreve o ficheiro por inteiro.

Vocabulário de arquitetura: [Glossário da Configuração](plans/glossary-config-tui.md).

> **Nota:** `gitpr -h config` abre o ecrã e ignora o `-h`, porque o callback raiz retorna cedo para todo o subcomando. Use `gitpr config -h` para o texto de ajuda.
