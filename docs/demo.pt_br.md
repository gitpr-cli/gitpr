# Documentação Técnica: Tour Guiado (gitpr demo)

O `gitpr demo` percorre as três coisas que o GitPR faz com uma mudança — a mensagem de commit, a revisão de código e a descrição de pull request — sobre um diff de exemplo que viaja dentro do pacote. Nada é gerado e nada é enviado a lugar algum: as respostas foram gravadas uma vez e são reproduzidas, então o tour roda **sem chave de API, sem repositório Git e sem conexão**.

Ele existe para encurtar a distância entre o `pip install gitpr-cli` e o "entendi para que serve esta ferramenta". Todo outro recurso precisa de configuração antes de mostrar qualquer coisa: um provedor, uma chave, um token de forge, um repositório com um diff dentro. O tour não precisa de nenhum deles, o que faz dele o único comando que funciona numa máquina onde o GitPR nunca rodou.

---

## 1. Visão Geral

O tour é um subcomando, não uma flag: o `gitpr demo` nunca chega à configuração da chave de API, ao bloqueio de atualização do PyPI nem à verificação de internet, porque nada depois dele precisa de um ambiente configurado.

### 1.1 Referência do Comando — `gitpr demo`

Todas as opções do subcomando, como mostra o `gitpr demo -h` (ou `--help`):

```bash
gitpr demo                                  # o cenário padrão, na tela
gitpr demo --scenario security-issue        # o outro exemplo incluído
gitpr demo --no-tui                         # texto simples, sem tela
gitpr demo --lang pt_br --no-tui            # o tour em português
```

| Opção | Descrição |
| --- | --- |
| **`--scenario <name>`** | Qual exemplo percorrer. Sem ele, o primeiro cenário registrado é usado. Um nome desconhecido sai com código 1 e lista os que existem |
| **`--lang <code>`** | Idioma da interface nesta execução (`en_us`, `pt_br`, `pt_pt`, `es_es`, `fr_fr`). Sobrepõe o `GITPR_LANG` nesta execução e não é persistido |
| **`--no-tui`** | Imprime o tour em texto simples em vez de abrir a tela. Para CI, para terminais limitados e para gravações |
| **`-h` / `--help`** | Ajuda mais o link da documentação no idioma atual |

| Característica | Descrição |
| --- | --- |
| **Conteúdo** | Respostas gravadas uma vez pelo GitPR e embarcadas como código no pacote — reproduzidas, nunca regeradas |
| **Provedor de IA** | Nenhum é instanciado e nenhuma chave é lida. O pipeline roda de verdade, com a chamada ao modelo substituída |
| **Rede** | Nenhuma. Nenhuma requisição HTTPS, nenhum DNS, nenhum socket |
| **Git** | Nenhum. Nenhum repositório é necessário; o tour não roda um único comando `git` próprio |
| **Arquivos escritos** | Nenhum. Nenhum `.md`, nenhum `.txt`, nenhuma entrada de cache, nenhuma métrica |
| **Tela** | Um app Textual, ou texto simples com `--no-tui` (conteúdo idêntico nos dois) |
| **Código de saída 1** | Um nome de `--scenario` desconhecido |

---

## 2. As Seis Etapas

O tour é linear: seis telas, nesta ordem, cada uma com um título, uma linha de texto de contexto e o artefato sobre o qual ela fala.

| # | Etapa | O que mostra |
| --- | --- | --- |
| 1 | **Bem-vindo ao GitPR** | O que a ferramenta faz e a promessa do tour: um exemplo gravado, sem chave, sem repositório, sem conexão |
| 2 | **A mudança de exemplo** | O diff unificado — código, em inglês, em todos os idiomas |
| 3 | **Mensagem de commit** | O que o `gitpr -c` escreve para esse diff: um assunto no padrão Conventional Commits mais a justificativa que não cabe nele |
| 4 | **Revisão de código** | O que o `gitpr -r` reporta, composto exatamente como a revisão local é: os alertas do linter primeiro, a revisão abaixo |
| 5 | **Descrição do pull request** | O que o `gitpr` escreve para a branch: o que mudou, por que, e o que o revisor deve olhar |
| 6 | **Próximos passos** | O `gitpr --init` para a coisa de verdade, o link da documentação e como rodar o tour de novo |

### 2.1 Teclas

| Tecla | Ação |
| --- | --- |
| `n`, `→`, `Enter` | Próxima etapa. Na última etapa, encerra o tour |
| `p`, `←` | Etapa anterior. Na primeira etapa não faz nada (um bipe, não uma saída) |
| `F1` | Janela de ajuda: as teclas e sobre o que o tour está rodando |
| `Esc` | Encerra o tour, de qualquer etapa — e de dentro da janela de ajuda |

Voltar é de graça: os três artefatos são gerados uma vez, antes da primeira tela, então voltar nunca regera nada e o tour não consegue mostrar uma resposta diferente na segunda vez. Uma etapa conta como vista quando você a deixa para a frente, então reler uma anterior não a desmarca.

---

## 3. De Onde Vêm as Respostas

O tour não é uma apresentação de telas fixas: ele chama o mesmo `generate_pr_content()` que o `gitpr -c`, o `gitpr -r` e o `gitpr` chamam, e o mesmo `compose_review_content()` que renderiza a revisão local. Só a chamada ao modelo é substituída — por um fake que devolve a resposta gravada do cenário — e é isso que impede o tour de se afastar do que os comandos reais imprimem.

Tudo o que o pipeline procuraria para fora é neutralizado durante o tour:

| Substituído | Por quê |
| --- | --- |
| **`call_ai_model`** | A origem dos dados: um fake que reproduz a resposta gravada e registra a chamada |
| **`get_cached_response` / `save_cached_response`** | Uma leitura de cache reproduziria a *sua* revisão antiga de uma branch real, e uma gravação arquivaria a resposta do demo sob um prompt real — o tour não lê nem escreve nada |
| **`log_command_metric` / `log_local_metric`** | A telemetria grava em `~/.gitpr/metrics/` sem desligamento, e um tour não é uso de um recurso |
| **`get_api_key` / `get_api_model`** | O pipeline de PR desiste *antes* de chamar o modelo quando falta a chave ou o modelo, então isso precisa ser respondido |
| **`get_skill_context`** | Determinismo: um arquivo local em `.gitpr/skill/` mudaria o que o tour mostra, e imprimiria a linha "template carregado" no meio dele |

O diff em si é código do repositório e permanece em inglês em todos os idiomas — traduzir `Rule::unique()` deturparia o que a ferramenta lê. A prosa ao redor, as revisões e as descrições de PR são traduzidas.

Um cenário que falha ao produzir um dos três artefatos levanta erro em vez de renderizar uma tela em branco: um tour vazio parece que a ferramenta não encontrou nada, quando a causa real é que o pipeline nunca chegou ao provedor.

---

## 4. Os Cenários Incluídos

| Cenário | Stack | A mudança |
| --- | --- | --- |
| **`laravel-bug-fix`** (padrão) | PHP / Laravel | Uma atualização de perfil que rejeita o próprio e-mail do usuário — `unique:users,email` sem `ignore()`, onde a correção acrescenta a regra de ignore |
| **`security-issue`** | TypeScript / Express | Um IDOR no download de fatura: a linha é resolvida apenas pela chave primária, então qualquer usuário autenticado baixa a fatura de outra organização |

Cada um é um módulo Python em `src/demo/scenarios/` que expõe três nomes:

```python
NAME = "laravel-bug-fix"   # o valor que --scenario recebe
DIFF = """..."""           # o diff unificado — código, nunca traduzido
TEXT = {"en": {...}, "pt_br": {...}, ...}   # a prosa e as respostas gravadas
```

Os cenários são módulos e não arquivos de dados JSON porque o pacote não embarca nenhum arquivo que não seja `.py`: o `pyproject.toml` coleta `src` e `src.*` via `packages.find` e não tem `package_data`, então um arquivo de dados ficaria de fora da wheel sem nada falhar na build.

Para acrescentar um, coloque um módulo nesse diretório, registre-o em `src/demo/scenarios/__init__.py` e copie o formato acima. O `TEXT["en"]` é obrigatório e é o fallback para todos os outros idiomas; os testes exigem que cada idioma presente carregue `title`, `description`, `commit_message`, `review`, `linter` e `pr_description`, não vazios, com os cabeçalhos de hunk do `DIFF` fechando a conta.

---

## 5. Idiomas

O tour tem duas metades e elas são traduzidas separadamente:

| Metade | Onde vive | Idiomas |
| --- | --- | --- |
| **Chrome** — títulos das etapas, prosa de contexto, janela de ajuda, próximos passos | `langs/*.json`, como qualquer outra string da ferramenta | `pt_br`, `pt_pt`, `es_es`, `es`, `fr_fr`, `fr` |
| **Prosa dos cenários** — título do exemplo, revisão, mensagem de commit, descrição do PR | Dentro de cada módulo de cenário, em `TEXT` | `en`, `pt_br`, `pt_pt`, `es_es`, `fr_fr` |

Um cenário cujo idioma não tem entrada em `TEXT` cai no inglês naquela metade, em vez de falhar ou misturar — um idioma parcialmente traduzido degrada em vez de quebrar. O cenário informa em qual idioma ele de fato rodou.

O `--lang` é declarado pelo próprio subcomando, porque o callback raiz retorna antes do handler de `--lang` dele para qualquer subcomando. Sem a flag, o tour segue o `GITPR_LANG` / o idioma detectado do sistema, o mesmo da interface ao redor, então as duas metades sempre concordam.

---

## 6. O Que o Tour Não Toca

| Não toca | Porque |
| --- | --- |
| Seu provedor de IA e suas chaves | A chamada ao modelo é substituída; nenhuma chave é lida, e nenhuma precisa existir |
| `~/.gitpr/cache/prompts/` | As duas chamadas de cache são substituídas, então o tour não lê uma revisão real em cache nem envenena o cache com uma gravada |
| `~/.gitpr/metrics/` | As duas chamadas de métrica são substituídas |
| Sua árvore de trabalho e seu repositório | Nenhum comando `git` do próprio tour roda, e nenhum arquivo é escrito — nenhum relatório, nenhum `.md`, nenhum `.txt` |
| `.gitpr/skill/` | A busca de skill é substituída, então um template local nunca muda o que o tour mostra |
| A forge | Nenhum token, nenhuma chamada de API, nenhum repositório |

**Uma linha ainda é escrita.** O log de invocações (`~/.gitpr/logs/`) registra a execução como qualquer outro comando, a partir do callback raiz da CLI por onde todo comando e todo `-h` passam, junto com a única consulta ao `git config` que rotula a linha com o repositório e o autor. Ele é local e best-effort — um home somente leitura ou um `git` ausente nunca viram um comando falho — e o `GITPR_SHOW_LOGS=false` o desliga. Nada mais do tour deixa rastro.

---

## 7. Variáveis de Ambiente

O tour não introduz **nenhuma configuração nova**. Ele lê o que o resto da ferramenta já lê:

| Variável | Para quê |
| --- | --- |
| `GITPR_LANG` | Idioma da interface, quando o `--lang` não é dado |
| `GITPR_SHOW_LOGS` | Desliga o log de invocações (`false`), para qualquer comando |

Nenhuma variável de chave, token, modelo ou caminho é lida: numa máquina com o `~/.gitpr/` vazio, o `gitpr demo` é o único comando que ainda funciona.

> **Nota:** Veja também a [documentação de Revisão de Código](code-review-ia.pt_br.md) para o que a quarta etapa está pré-visualizando, e a de [Mensagens de Commit](commit-message-ia.pt_br.md) para a terceira.
