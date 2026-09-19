# Documentação Técnica: Visita Guiada (gitpr demo)

O `gitpr demo` percorre as três coisas que o GitPR faz com uma alteração — a mensagem de commit, a revisão de código e a descrição de pull request — sobre um diff de exemplo que viaja dentro do pacote. Nada é gerado e nada é enviado para lado nenhum: as respostas foram gravadas uma vez e são reproduzidas, por isso a visita corre **sem chave de API, sem repositório Git e sem ligação**.

Existe para encurtar a distância entre o `pip install gitpr-cli` e o "percebi para que serve esta ferramenta". Todas as outras funcionalidades precisam de configuração antes de mostrar seja o que for: um fornecedor, uma chave, um token de forge, um repositório com um diff lá dentro. A visita não precisa de nenhum deles, o que faz dela o único comando que funciona numa máquina onde o GitPR nunca correu.

---

## 1. Visão Geral

A visita é um subcomando, não uma flag: o `gitpr demo` nunca chega à configuração da chave de API, ao bloqueio de atualização do PyPI nem à verificação de internet, porque nada depois dele precisa de um ambiente configurado.

### 1.1 Referência do Comando — `gitpr demo`

Todas as opções do subcomando, como mostra o `gitpr demo -h` (ou `--help`):

```bash
gitpr demo                                  # o cenário predefinido, no ecrã
gitpr demo --scenario security-issue        # o outro exemplo incluído
gitpr demo --no-tui                         # texto simples, sem ecrã
gitpr demo --lang pt_pt --no-tui            # a visita em português
```

| Opção | Descrição |
| --- | --- |
| **`--scenario <name>`** | Que exemplo percorrer. Sem ele, o primeiro cenário registado é usado. Um nome desconhecido sai com código 1 e lista os que existem |
| **`--lang <code>`** | Idioma da interface nesta execução (`en_us`, `pt_br`, `pt_pt`, `es_es`, `fr_fr`). Sobrepõe o `GITPR_LANG` nesta execução e não é persistido |
| **`--no-tui`** | Imprime a visita em texto simples em vez de abrir o ecrã. Para CI, para terminais limitados e para gravações |
| **`-h` / `--help`** | Ajuda mais a ligação da documentação no idioma atual |

| Característica | Descrição |
| --- | --- |
| **Conteúdo** | Respostas gravadas uma vez pelo GitPR e embarcadas como código no pacote — reproduzidas, nunca regeradas |
| **Fornecedor de IA** | Nenhum é instanciado e nenhuma chave é lida. O pipeline corre a sério, com a chamada ao modelo substituída |
| **Rede** | Nenhuma. Nenhum pedido HTTPS, nenhum DNS, nenhum socket |
| **Git** | Nenhum. Nenhum repositório é necessário; a visita não corre um único comando `git` próprio |
| **Ficheiros escritos** | Nenhum. Nenhum `.md`, nenhum `.txt`, nenhuma entrada de cache, nenhuma métrica |
| **Ecrã** | Uma app Textual, ou texto simples com `--no-tui` (conteúdo idêntico nos dois) |
| **Código de saída 1** | Um nome de `--scenario` desconhecido |

---

## 2. As Seis Etapas

A visita é linear: seis ecrãs, por esta ordem, cada um com um título, uma linha de texto de enquadramento e o artefacto sobre o qual fala.

| # | Etapa | O que mostra |
| --- | --- | --- |
| 1 | **Bem-vindo ao GitPR** | O que a ferramenta faz e a promessa da visita: um exemplo gravado, sem chave, sem repositório, sem ligação |
| 2 | **A alteração de exemplo** | O diff unificado — código, em inglês, em todos os idiomas |
| 3 | **Mensagem de commit** | O que o `gitpr -c` escreve para esse diff: um assunto no padrão Conventional Commits mais a justificação que não cabe nele |
| 4 | **Revisão de código** | O que o `gitpr -r` reporta, composto exatamente como a revisão local é: os alertas do linter primeiro, a revisão abaixo |
| 5 | **Descrição do pull request** | O que o `gitpr` escreve para a branch: o que mudou, porquê, e o que o revisor deve olhar — mais o selo que uma publicação anexa, contado dos alertas gravados do linter |
| 6 | **Próximos passos** | O `gitpr --init` para a coisa a sério, a ligação da documentação e como correr a visita outra vez |

### 2.1 Teclas

| Tecla | Ação |
| --- | --- |
| `n`, `→`, `Enter` | Etapa seguinte. Na última etapa, encerra a visita |
| `p`, `←` | Etapa anterior. Na primeira etapa não faz nada (um sinal sonoro, não uma saída) |
| `F1` | Janela de ajuda: as teclas e sobre o que a visita está a correr |
| `Esc` | Encerra a visita, de qualquer etapa — e de dentro da janela de ajuda |

Voltar é gratuito: os três artefactos são gerados uma vez, antes do primeiro ecrã, por isso voltar nunca regera nada e a visita não consegue mostrar uma resposta diferente à segunda vez. Uma etapa conta como vista quando a deixa para a frente, por isso reler uma anterior não a desmarca.

---

## 3. De Onde Vêm as Respostas

A visita não é uma apresentação de ecrãs fixos: chama o mesmo `generate_pr_content()` que o `gitpr -c`, o `gitpr -r` e o `gitpr` chamam, e o mesmo `compose_review_content()` que renderiza a revisão local. Só a chamada ao modelo é substituída — por um fake que devolve a resposta gravada do cenário — e é isso que impede a visita de se afastar do que os comandos reais imprimem.

Tudo o que o pipeline procuraria lá fora é neutralizado durante a visita:

| Substituído | Porquê |
| --- | --- |
| **`call_ai_model`** | A origem dos dados: um fake que reproduz a resposta gravada e registra a chamada |
| **`get_cached_response` / `save_cached_response`** | Uma leitura de cache reproduziria a *sua* revisão antiga de uma branch real, e uma gravação arquivaria a resposta da demo sob um prompt real — a visita não lê nem escreve nada |
| **`log_command_metric` / `log_local_metric`** | A telemetria grava em `~/.gitpr/metrics/` sem desligamento, e uma visita não é uso de uma funcionalidade |
| **`get_api_key` / `get_api_model`** | O pipeline de PR desiste *antes* de chamar o modelo quando falta a chave ou o modelo, por isso isso tem de ser respondido |
| **`get_skill_context`** | Determinismo: um ficheiro local em `.gitpr/skill/` mudaria o que a visita mostra, e imprimiria a linha "template carregado" no meio dela |

O diff em si é código do repositório e permanece em inglês em todos os idiomas — traduzir `Rule::unique()` deturparia o que a ferramenta lê. A prosa à volta, as revisões e as descrições de PR são traduzidas.

Um cenário que falha ao produzir um dos três artefactos levanta erro em vez de renderizar um ecrã em branco: uma visita vazia parece que a ferramenta não encontrou nada, quando a causa real é que o pipeline nunca chegou ao fornecedor.

---

## 4. Os Cenários Incluídos

| Cenário | Stack | A alteração |
| --- | --- | --- |
| **`laravel-bug-fix`** (predefinido) | PHP / Laravel | Uma atualização de perfil que rejeita o próprio e-mail do utilizador — `unique:users,email` sem `ignore()`, onde a correção acrescenta a regra de ignore |
| **`security-issue`** | TypeScript / Express | Um IDOR no download de faturas: a linha é resolvida apenas pela chave primária, por isso qualquer utilizador autenticado descarrega a fatura de outra organização |

Cada um é um módulo Python em `src/demo/scenarios/` que expõe três nomes:

```python
NAME = "laravel-bug-fix"   # o valor que --scenario recebe
DIFF = """..."""           # o diff unificado — código, nunca traduzido
TEXT = {"en": {...}, "pt_br": {...}, ...}   # a prosa e as respostas gravadas
```

Os cenários são módulos e não ficheiros de dados JSON porque o pacote não embarca nenhum ficheiro que não seja `.py`: o `pyproject.toml` recolhe `src` e `src.*` via `packages.find` e não tem `package_data`, por isso um ficheiro de dados ficaria de fora da wheel sem nada falhar na build.

Para acrescentar um, coloque um módulo nesse diretório, registe-o em `src/demo/scenarios/__init__.py` e copie o formato acima. O `TEXT["en"]` é obrigatório e é o fallback para todos os outros idiomas; os testes exigem que cada idioma presente carregue `title`, `description`, `commit_message`, `review`, `linter` e `pr_description`, não vazios, com os cabeçalhos de hunk do `DIFF` a fechar a conta.

---

## 5. Idiomas

A visita tem duas metades e são traduzidas separadamente:

| Metade | Onde vive | Idiomas |
| --- | --- | --- |
| **Chrome** — títulos das etapas, prosa de enquadramento, janela de ajuda, próximos passos | `langs/*.json`, como qualquer outra string da ferramenta | `pt_br`, `pt_pt`, `es_es`, `es`, `fr_fr`, `fr` |
| **Prosa dos cenários** — título do exemplo, revisão, mensagem de commit, descrição do PR | Dentro de cada módulo de cenário, em `TEXT` | `en`, `pt_br`, `pt_pt`, `es_es`, `fr_fr` |

Um cenário cujo idioma não tem entrada em `TEXT` cai no inglês nessa metade, em vez de falhar ou misturar — um idioma parcialmente traduzido degrada em vez de quebrar. O cenário informa em que idioma correu de facto.

O `--lang` é declarado pelo próprio subcomando, porque o callback raiz retorna antes do handler de `--lang` dele para qualquer subcomando. Sem a flag, a visita segue o `GITPR_LANG` / o idioma detetado do sistema, o mesmo da interface à volta, por isso as duas metades concordam sempre.

---

## 6. O Que a Visita Não Toca

| Não toca | Porque |
| --- | --- |
| O seu fornecedor de IA e as suas chaves | A chamada ao modelo é substituída; nenhuma chave é lida, e nenhuma precisa de existir |
| `~/.gitpr/cache/prompts/` | As duas chamadas de cache são substituídas, por isso a visita não lê uma revisão real em cache nem envenena o cache com uma gravada |
| `~/.gitpr/metrics/` | As duas chamadas de métrica são substituídas |
| A sua árvore de trabalho e o seu repositório | Nenhum comando `git` da própria visita corre, e nenhum ficheiro é escrito — nenhum relatório, nenhum `.md`, nenhum `.txt` |
| `.gitpr/skill/` | A procura de skill é substituída, por isso um template local nunca muda o que a visita mostra |
| A forge | Nenhum token, nenhuma chamada de API, nenhum repositório |

**Uma linha ainda é escrita.** O log de invocações (`~/.gitpr/logs/`) registra a execução como qualquer outro comando, a partir do callback raiz da CLI por onde todo o comando e todo o `-h` passam, junto com a única consulta ao `git config` que rotula a linha com o repositório e o autor. É local e best-effort — um home só de leitura ou um `git` em falta nunca viram um comando falhado — e o `GITPR_SHOW_LOGS=false` desliga-o. Nada mais da visita deixa rasto.

---

## 7. Variáveis de Ambiente

A visita não introduz **nenhuma configuração nova**. Lê o que o resto da ferramenta já lê:

| Variável | Para quê |
| --- | --- |
| `GITPR_LANG` | Idioma da interface, quando o `--lang` não é dado |
| `GITPR_SHOW_LOGS` | Desliga o log de invocações (`false`), para qualquer comando |

Nenhuma variável de chave, token, modelo ou caminho é lida: numa máquina com o `~/.gitpr/` vazio, o `gitpr demo` é o único comando que ainda funciona.

> **Nota:** Veja também a [documentação de Revisão de Código](code-review-ia.pt_pt.md) para o que a quarta etapa está a pré-visualizar, a de [Mensagens de Commit](commit-message-ia.pt_pt.md) para a terceira, e a do [Selo](badge.pt_pt.md) para a marca no rodapé da quinta.
