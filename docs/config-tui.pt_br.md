# Documentação Técnica: Tela de Configuração Interativa (`gitpr config`)

O GitPR é configurado pelo `~/.gitpr/.env`, um arquivo dotenv com cerca de cinquenta variáveis. Até agora, mudar uma delas exigia saber o nome exato, abrir o arquivo à mão e adivinhar se o valor é `true`, `1` ou `yes` — e um valor que o leitor não entende é engolido em silêncio, então um erro de digitação nunca aparece como erro.

O `gitpr config` abre uma tela master-detail sobre esse mesmo arquivo: categorias à esquerda, as configurações da selecionada à direita, editadas no lugar. É uma camada fina sobre o arquivo que você já tem — não uma segunda fonte de configuração.

```bash
gitpr config
```

---

## 1. A Tela

```text
┌ Header ──────────────────────────────────────────────┐
│ Configurações      [/ buscar…]   ● 2 não salvas      │
├──────────────┬───────────────────────────────────────┤
│ Geral        │  Idioma da interface                  │
│ Provedores…  │  [ pt_br            ▾ ]               │
│ Pull Request │                                       │
│ …            │  Co-autor                             │
│              │  [ ●] habilitado                      │
├──────────────┴───────────────────────────────────────┤
│ F1 Ajuda · F2 Salvar · ^R Restaurar · / Buscar · Esc │
└──────────────────────────────────────────────────────┘
```

| Tecla | Ação |
| --- | --- |
| `F1` | Ajuda — a lista de atalhos e como os valores são lidos |
| `F2` | Valida e salva as alterações pendentes |
| `Ctrl+R` | Restaura o padrão do campo em foco (remove a linha) |
| `/` | Busca um nome de variável ou um rótulo em todas as categorias |
| `Esc` | Sai — ou limpa a busca primeiro; pergunta antes de descartar |

### 1.1 Categorias

O menu lateral espelha os comandos e flags da CLI, então a configuração que você quer está onde está a funcionalidade que você usa. A primeira entrada é sempre **Geral**:

| Categoria | Contém |
| --- | --- |
| **Geral** | Idioma da interface, trailer de co-autor, log geral |
| **Provedores de IA** | Mecanismo padrão, timeout da IA, as duas chaves de API, e os modelos de cada provedor — sob uma sub-seção por provedor, exibida uma de cada vez |
| **Pull Request** | `OUTPUT_FILE_NAME`, branch base, auto commit/stage/merge, pular linter, log de publicação, sugestão de revisores |
| **Revisão de Código** | `OUTPUT_FILE_NAME_REVIEW`, `_FULLREVIEW`, `_FILEREVIEW` |
| **Issue** | `OUTPUT_FILE_NAME_ISSUE` |
| **Blame** | `OUTPUT_FILE_NAME_BLAME` |
| **Linter** | `OUTPUT_FILE_NAME_LINTER`, `GITPR_LINTER_TIMEOUT` |
| **Release** | Caminho do changelog, resumo por IA, bump automático, rascunho por padrão, `OUTPUT_FILE_NAME_RELEASE` |
| **SCM / Forge** | Provedor, token de CI/CD, token da forge, URL base; sub-seções **GitHub**, **Bitbucket** e **Azure DevOps** com o que cada forge precisa |
| **Filtros de Diff** | Chave dos smart excludes e os dois caminhos de lista de filtros |
| **Skills** | Os sete arquivos de skill deste projeto — uma entrada por skill, editadas ali mesmo (§1.7) |
| **Avançado** | Três sub-seções — **Spinner**, **Git Hooks**, **Downloads** — ocultas até você ligar **Mostrar avançadas** |
| **Desconhecidas** | Chaves no arquivo que o schema não declara — aparece só quando existem |

Cada uma das doze categorias tem um link para a sua própria documentação técnica (§1.5).

### 1.2 Controles

Cada campo recebe o controle que o seu tipo merece, para que um valor inválido seja difícil de produzir desde o início:

| Tipo | Controle |
| --- | --- |
| Booleano | Switch |
| Enum | Select |
| Inteiro | Campo de texto, validado |
| Template de nome de arquivo | Campo de texto, validado contra os placeholders |
| Caminho, texto livre | Campo de texto |
| Segredo | Campo mascarado |
| Lista de palavras | Caixa somente leitura que rola sozinha, com a contagem de entradas acima dela e um botão de download (§1.4) |

### 1.3 Filtrado pelo Valor Selecionado

Duas configurações decidem quais outras configurações ficam na tela, e o painel segue a seleção **imediatamente** — antes de qualquer coisa ser salva:

| Quando você seleciona | Você vê |
| --- | --- |
| Um **Provedor padrão** | Apenas os modelos daquele provedor. Sem nada selecionado, nenhuma seção de provedor é exibida |
| Um **Provedor da forge** | Apenas a sub-seção daquela forge, mais os campos que todas as forges compartilham |

A busca ignora o filtro de propósito: buscar `deepseek` com o Gemini selecionado ainda encontra os modelos do DeepSeek, para você já preencher um provedor para o qual vai trocar. Um campo oculto com edição pendente ainda é salvo — visibilidade é uma visão, não uma permissão.

### 1.4 Botões de Download

Quatro listas são servidas do repositório do GitPR e atualizadas quando o marcador de versão delas muda. **📥 Forçar download** ao lado de um marcador de versão o baixa novamente sob demanda, e **📥 Baixar a lista de palavras** faz o mesmo com as palavras do spinner. Esta é a saída manual para o caso que a verificação automática não consegue enxergar: a lista está presente, atualizada, e ainda assim não é a que você quer.

O botão informa o resultado com honestidade, porque um download pode falhar e cair na cópia que já está em disco sem nenhuma forma de distinguir as duas de fora:

| Retorno | Significado |
| --- | --- |
| `✔ v0.0.24` e *"{name} está atualizado ({version})."* | O arquivo agora carrega a versão atual — ou recém-baixada, ou uma cópia que já estava atual |
| `✖ não atualizado` e *"Não foi possível baixar {name}. A cópia anterior continua em uso."* | O download falhou. Nada foi perdido: a cópia anterior está intacta e continua em uso |
| *"O inglês não precisa de pacote de tradução — não há nada para baixar."* | O pacote de tradução não tem edição em inglês para buscar, já que o inglês é embutido |

O veredito vem da releitura do `~/.gitpr/.env` depois do download, nunca de `os.getenv()`: o `load_dotenv()` roda com `override=False`, então o processo ainda mantém o valor com que começou.

### 1.5 Link da Documentação

**📚 Documentação** no topo do painel direito abre a documentação técnica da categoria que você está vendo, e a URL é impressa ao lado do botão para você lê-la ou copiá-la antes.

| Categoria | Documento |
| --- | --- |
| Geral | `config-tui.md` |
| Provedores de IA | `providers-ia.md` |
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

O link segue o idioma da interface (`?lang=pt_br`), e a linha desaparece na visão de busca e em **Desconhecidas**, que não é uma categoria do GitPR.

### 1.6 O Toggle de Avançadas

**Mostrar avançadas** na barra superior revela a categoria `Avançado` e todo campo marcado como interno. São marcadores de versão que o GitPR mantém sozinho ao baixar traduções, presets de linter, palavras do spinner e listas de filtros; aparecem por transparência, não para edição. O toggle fica desligado em toda abertura.

Dois desses campos não são marcadores e vale a pena conhecê-los:

- **Idioma dos hooks** (`SCRIPTS_LANG`) — o idioma em que os Git hooks são instalados. Vazio significa "seguir o idioma da interface", que é o que a maioria dos usuários quer; escolher um instala os hooks naquele idioma na próxima execução. **Idioma dos hooks instalados** ao lado é somente leitura e registra o que está de fato em disco, para que os dois nunca sejam confundidos.
- **Palavras do spinner** — a própria lista, somente leitura, na caixa descrita na §1.2.

### 1.7 A Seção Skills

Em todo o resto, a tela edita `~/.gitpr/.env`. **Skills** é a única seção que não: ela edita os arquivos de skill do próprio projeto — as instruções de IA lidas de `./.gitpr/skill/` ([Sistema de Skills e Templates](skill-template.pt_br.md)).

A lista tem uma entrada por skill suportada pelo GitPR: **Commit**, **Pull Request**, **Code Review**, **File Review**, **Issue**, **Blame**, **Release**. É a lista das skills que os comandos carregam, e não um espelho da pasta — um arquivo em `.gitpr/skill/` que nenhum comando lê não é oferecido aqui.

| A entrada mostra | Significado |
| --- | --- |
| nada | O arquivo existe e permite gravação — edite-o na caixa à direita e pressione `F2` |
| **● editado** | Uma edição sua ainda não foi gravada |
| **não está neste projeto** | O arquivo não existe. A caixa exibe *"Este projeto ainda não tem o arquivo {name}."* e o editor fica desabilitado — uma caixa vazia seria lida como "esta skill está vazia", que é o oposto do que é verdade |
| **somente leitura** | O arquivo existe mas não permite gravação. Ele é exibido, travado, e não há nada a gravar |

**📥 Baixar o template** aparece para uma skill ausente e busca o template publicado para o seu idioma de interface, como os botões de download da §1.4. Quando nem isso pode ser gravado — uma pasta `.gitpr/skill/` sem permissão de escrita — o botão fica desabilitado com o motivo ao lado.

O `F2` grava os campos do `.env` **e** os arquivos de skill na mesma passada, e o contador de pendências cobre os dois. Dentro do painel, o `Ctrl+R` descarta a edição e devolve o texto do disco — o mais próximo de um padrão que um arquivo tem — e o `Esc` pergunta antes de descartar, como em todo o resto.

Cada arquivo mantém o fim de linha que já tinha, então um arquivo `CRLF` continua `CRLF` e o seu diff mostra apenas as linhas que você editou.

---

## 2. Como os Valores São Lidos

**A tela mostra o que está no arquivo, não o que o processo está usando.** A diferença importa, porque o `load_dotenv()` roda com `override=False` em todo o GitPR: quando uma variável também está exportada no seu shell, o ambiente vence e o arquivo é ignorado em tempo de execução.

Um campo nessa situação é marcado com **⚠ no ambiente**, e o valor na tela continua sendo o do arquivo. Editá-lo é permitido — só não terá efeito enquanto a variável não for removida do ambiente. Isso é proposital: sem a marcação você veria um valor que silenciosamente não é o que está em uso, que é a falha mais confusa que este arquivo pode produzir.

Os valores são lidos com um parser que olha apenas o arquivo, nunca com `os.getenv()`, então nada do processo atual vaza para a tela.

---

## 3. Edição e Gravação

Nada é gravado até você pressionar `F2`. Enquanto edita, o `F2` mostra um contador de alterações pendentes e o `Esc` pede confirmação antes de sair:

- **Salvar** grava apenas os campos que você realmente alterou, então as linhas não relacionadas mantêm os seus comentários e a sua posição no arquivo.
- **Arquivos de skill** são gravados na mesma salvaguarda: um `F2` cobre os campos pendentes do `.env` e as skills editadas (§1.7). Uma skill que falha ao gravar é reportada pelo nome e mantém a edição pendente — os outros arquivos são gravados de qualquer forma.
- **`Ctrl+R`** em um campo **não** reescreve o padrão embutido — ele marca a linha para **remoção**, para que o valor volte ao que o código define como padrão. O campo exibe `— será removido —` e um novo `Ctrl+R` desfaz a marcação. Este é o reset honesto: gravar o padrão atual o congelaria no arquivo e interromperia o acompanhamento de mudanças futuras no padrão.
- **Esvaziar um campo** limpa a sobrescrita.
- Depois de salvar, a tela permanece aberta, relê o arquivo e informa quantas configurações foram salvas.

### 3.1 Validação

O `F2` valida antes de gravar qualquer coisa. Um campo que falha ganha borda vermelha e uma mensagem inline, nada é salvo, e a tela pula para o primeiro campo problemático — trocando de categoria e ligando **Mostrar avançadas** se for ali que ele vive.

| Regra | Por quê |
| --- | --- |
| Apenas `true` / `false`, mais `1`/`0`, `yes`/`no`, `y`/`n`, `off` | O GitPR tem dois leitores de booleano que discordam fora deste conjunto. `on` parece simétrico a `off`, mas é lido como **false** por um e como **true** pelo outro |
| Inteiros devem ser maiores que zero | Um timeout que não pode ser interpretado é substituído pelo padrão em silêncio, então um erro de digitação nunca aparece como erro |
| Enums devem ser uma das opções declaradas | Um nome de provedor desconhecido não é rejeitado na inicialização, ele simplesmente não funciona |
| Templates devem usar placeholders conhecidos e manter `{datetime}` | Um placeholder desconhecido é um `KeyError` no próximo comando; sem `{datetime}` toda execução resolve para o mesmo nome de arquivo e sobrescreve o relatório anterior |

### 3.2 Validação de Credencial

Um segredo (chave de API, token da forge) é validado junto ao seu provedor antes de ser salvo, porque uma credencial errada só é descoberta depois, no meio de um comando real. A validação roda em segundo plano para a tela nunca travar, e o resultado decide:

| Resultado | Comportamento |
| --- | --- |
| Aceita | Salva |
| Recusada (HTTP 401/403, ou uma resposta "invalid API key") | **Bloqueia** — a credencial está errada e guardá-la não ajuda ninguém |
| Falha de rede, timeout, provedor inalcançável | **Salva com aviso** — uma chave correta digitada atrás de um proxy não pode ser recusada |

Apenas os segredos que você alterou nesta sessão são revalidados. Uma chave que já estava no arquivo e não foi tocada não é sondada a cada gravação.

Valores de segredo **nunca são exibidos de volta**. O campo fica vazio quando nada está guardado, e mostra um placeholder fixo (`•••••••• (definido — digite para substituir)`) quando existe um valor — a mesma máscara independentemente do segredo, porque o valor real nunca é lido para a tela. Ele entra na gravação apenas quando você digita algo nele. Os segredos são criptografados em repouso com a chave Fernet local em `~/.gitpr/secret.key`; a tela criptografa na hora de gravar e nunca descriptografa para preencher um campo.

---

## 4. Busca e Chaves Fora do Schema

Digitar na caixa de busca filtra por nome de variável **e** por rótulo, em todas as categorias de uma vez — `timeout` encontra os timeouts da IA e do linter sem você saber em que categoria eles estão. Enquanto uma busca está ativa, a área principal mostra os resultados como uma lista plana, com uma contagem, em vez dos campos da categoria selecionada; o menu lateral continua onde está. O `Esc` limpa a busca — e devolve o foco ao menu lateral — antes de poder sair da tela.

Variáveis presentes no arquivo que o GitPR não declara caem numa categoria **Desconhecidas** que só aparece quando tais chaves existem. Elas são somente leitura: a tela nunca grava uma chave que não é dela. Mudar uma significa editar o arquivo à mão.

---

## 5. Deliberadamente Não Editável

Estas chaves não recebem campo editável. A tela nunca esconde uma chave que está no seu arquivo — ela só se recusa a **escrever** numa que não é dela — então todas menos a última ainda aparecem, somente leitura, em **Desconhecidas** (ver §4).

| Variável | Por quê |
| --- | --- |
| `GITPR_SCM_TOKEN` | O token cru de CI/CD tem precedência sobre o criptografado e é guardado em texto plano. Ele tem uma linha em **SCM / Forge** — somente leitura e nunca exibida — apontando para o `gitpr --init`, que é a única coisa que deveria gravá-lo; um campo editável convidaria a sombrear o token que você configurou lá |
| `PR_AUTO_PUBLISH` | Sobra de antes de publicar virar o fluxo padrão. Lida em lugar nenhum: o que a substituiu é a flag `--no-edit`. Uma instalação antiga pode ainda carregar a linha dela no `.env`, e é por isso que ela aparece em **Desconhecidas** |
| `CI`, `GITHUB_ACTIONS` | Marcadores de ambiente do processo, nunca gravados neste arquivo, então nunca aparecem |

---

## 6. Para Desenvolvedores

A tela é construída a partir de um schema declarativo, então adicionar uma configuração é uma mudança de dados e não de interface.

| Arquivo | Papel |
| --- | --- |
| `src/config_schema.py` | Dado puro: `ConfigField`, `Category`, `Group`, `CATEGORIES`, `GROUPS`, `FIELDS` (56 campos), mais `fields_of()`, `validate_field_value()` e os auxiliares de busca. Fonte única de verdade para menu, widgets, padrões, sub-seções, visibilidade e validação |
| `src/doc_links.py` | `doc_url(filename)` — a URL base da documentação e a regra do `?lang=`. Separado do `core.py` porque a tela não pode importar `src.core`, que carrega os SDKs de IA a cada abertura |
| `src/ui/config_app.py` | `ConfigApp` mais os modais de ajuda e confirmação. Layout master-detail, dirty state, busca, o toggle de avançadas, o filtro de visibilidade, os workers de download, o painel de Skills (§1.7) e o pipeline de gravação |
| `src/config.py` | Quatro funções novas: `read_env_file_values()`, `save_config_values()`, `remove_config_value()`, `validate_ai_key()`. Guarda também o registro de skills (`SKILL_FILES_BY_TYPE`, `SKILL_TYPES`) e os auxiliares de arquivo (`read_skill_file()`, `write_skill_file()`, `skill_file_status()`) que o `get_skill_context()` e a seção Skills leem (§1.7) |
| `src/main.py` | O subcomando `config` — sem `setup_environment()`, para que nada possa pedir entrada no stdin dentro do app de tela cheia |

Três atributos de um `ConfigField` carregam o layout: `group` coloca o campo sob um sub-cabeçalho, `show_if` o oculta a menos que outro campo tenha um dos valores listados, e `action` anexa um botão de download. `version_source` diz qual constante exibir quando um marcador de versão ainda não está no arquivo — um `LINTER_PRESETS_VERSION` vazio mostra a versão enviada no código em vez de uma caixa vazia.

**Adicionando uma configuração:** declare um `ConfigField` com rótulo e descrição literais `__("…")`, adicione a chave ao `DEFAULT_CONFIG` se for um novo padrão de semeadura, e traduza as chaves novas nos seis `langs/*.json`. O `tests/test_config_schema.py` falha enquanto o schema e o `DEFAULT_CONFIG` não concordarem — e enquanto um novo `group`, `show_if` ou `action` não apontar para algo que existe — e o `tests/test_i18n.py` falha enquanto cada arquivo de idioma não carregar as chaves novas.

**Modelo de estado:** as edições pendentes vivem num dicionário indexado pelo nome da variável, não nos widgets. O conjunto de linhas visíveis muda conforme você navega ou busca, e um valor lido de volta de um controle oculto seria frágil — por isso o `F2` é independente do que está na tela naquele momento.

**As gravações em disco** passam pelo `set_key()`/`unset_key()` do `python-dotenv`, que escrevem um arquivo temporário e o renomeiam, preservando comentários e ordem. A tela nunca reescreve o arquivo por inteiro.

Vocabulário de arquitetura: [Glossário da Configuração](plans/glossary-config-tui.md).

> **Nota:** `gitpr -h config` abre a tela e ignora o `-h`, porque o callback raiz retorna cedo para todo subcomando. Use `gitpr config -h` para o texto de ajuda.
