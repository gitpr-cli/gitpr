# Documentação Técnica: Selo de Pull Request

Todo o pull request publicado pelo GitPR leva um selo pequeno no rodapé do corpo: `GitPR` e as contagens do linter para a alteração. É montado a partir de uma medição que o GitPR fez de facto — o linter estático local, sobre o diff que está a ser publicado — e é uma imagem Markdown que o shields.io renderiza no navegador de quem lê, por isso nada é pedido à rede enquanto o pull request é escrito.

Há um segundo selo, estático, para o README do seu projeto. `gitpr badge --readme` imprime o snippet e não escreve nada.

---

## 1. Visão Geral

O selo é um recurso com opt-out. Vem ligado por predefinição, nunca pergunta nada — nenhum prompt, nenhuma confirmação na primeira execução — e é avisado duas vezes: uma quando o `gitpr --init` configura uma forge, que é onde publicar passa a ser possível, e outra numa publicação que o anexa sem que tenha visto o corpo antes.

### 1.1 Referência do Comando — `gitpr badge`

Todas as opções do subcomando, como mostradas por `gitpr badge -h` (ou `--help`):

```bash
gitpr badge                          # o que é, mais o snippet
gitpr badge --readme                 # só o snippet, pronto para pipe
gitpr badge --style for-the-badge    # outro estilo do shields.io
```

| Opção | Descrição |
| --- | --- |
| **`--readme`** | Imprime apenas o snippet, sem nada em volta — seguro para `>>` e para pipe |
| **`--style <style>`** | `flat` (predefinido), `flat-square` ou `for-the-badge`. Um valor desconhecido avisa no stderr e recua para `flat` |
| **`-h` / `--help`** | Ajuda mais a ligação da documentação no idioma atual |

| Característica | Descrição |
| --- | --- |
| **Ficheiros escritos** | Nenhum. O comando imprime; nunca edita o seu README |
| **Rede** | Nenhuma. O URL é montado, nunca pedido |
| **Configuração** | Nenhuma é lida: o snippet não depende do seu fornecedor, da sua forge nem do seu idioma |
| **Código de saída** | 0. Um `--style` desconhecido é um aviso, não uma falha |

---

## 2. O Que o Selo Diz

As contagens vêm das regras YAML do linter estático local, executadas sobre o mesmo diff do pull request. Só as regras são usadas — a ponte de linters externos é saltada, porque executa binários contra a árvore de trabalho, e não contra a revisão que está a ser publicada.

| errors | warnings | Cor | Mensagem |
| --- | --- | --- | --- |
| **> 0** | qualquer | `red` | `N errors · M warnings` |
| **0** | **> 0** | `yellow` | `0 errors · M warnings` |
| **0** | **0** | `brightgreen` | `no issues` |

Duas regras moldam o texto:

- **Um zero aparece ao lado de uma contagem diferente de zero.** `0 errors · 2 warnings` diz o que foi medido; esconder o zero daria a entender que os erros nunca foram contados. Cada contagem é pluralizada por conta própria, por isso `1 error · 1 warning` é escrito assim.
- **O selo nunca afirma uma revisão.** Relata o que o linter contou, no vocabulário do linter. Um selo verde significa *nenhuma violação de regra foi encontrada*, não *este código foi revisto e aprovado* — a revisão por IA é outro passo, sem qualquer participação nisto.

O que vê no pull request é uma única imagem. `GitPR | 0 errors · 2 warnings` é como o shields.io a desenha, não uma segunda linha de texto no corpo, e a imagem é uma ligação para [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/).

O texto do selo é **inglês fixo**, seja qual for o idioma da interface. Como o corpo do pull request em que fica, é um artefacto público que sobrevive à máquina que o escreveu, e aterra num repositório cujos leitores podem não falar o seu idioma.

---

## 3. Onde É Anexado

O selo é adicionado num único lugar, depois de o corpo do pull request estar pronto e antes de qualquer um dos publicadores o ler:

| Caminho | O selo |
| --- | --- |
| **`gitpr`** (TUI) | **Sim** — semeado no corpo editável, por isso pode alterá-lo ou apagá-lo antes de publicar |
| **`gitpr --no-edit`** | **Sim** — composto no pedido que é enviado |
| **`gitpr --no-publish`** | **Não** — o `.md` escrito localmente é a saída da IA, antes de o selo ser montado |
| **`gitpr review-pr`** | **Não** — um comentário de revisão é outro artefacto, e o GitPR não o assina |
| **Ferramentas MCP** | **Não** — as ferramentas devolvem o que o modelo produziu |

A TUI é a razão de o selo ser semeado em vez de injetado na hora do envio: está no ecrã, na área de texto que já está a editar, e a última palavra é sua. Atualizar um pull request existente reenvia o corpo que está no ecrã — incluindo o selo, se o tiver mantido.

O anexo é idempotente. Um corpo que já traz um selo é deixado como está, por isso republicar nunca empilha dois.

---

## 4. Quando Não Há Selo

**Sem regras de linter, sem selo.** Um `.gitpr/skill/.gitpr.linter.yml` vazio — o estado de quem nunca executou `gitpr --skill` — significa que o linter não tem o que executar, e o seu resultado vazio é indistinguível de um diff limpo. Um selo verde sobre um diff que ninguém verificou seria uma afirmação que o GitPR não pode sustentar, por isso é omitido por completo.

**O opt-out é `GITPR_BADGE=false`.** Como no trailer de co-autoria, `false`, `0`, `no`, `off` e `n` desligam, sem distinguir maiúsculas e ignorando espaços em volta; qualquer outra coisa — ou a variável ausente — mantém-no ligado. Nunca é escrita no `.env` em seu nome.

Com a flag desligada, nenhum selo é montado e nenhum aviso é impresso: o pull request sai exatamente como saía antes de este recurso existir.

---

## 5. O Selo do README

O selo que pode colocar no seu próprio projeto é outro: estático, sempre o mesmo, e diz o que a ferramenta faz, e não o que mediu.

```markdown
[![GitPR](https://img.shields.io/badge/GitPR-quality--checked-blue)](https://gitpr.natanfiuza.dev.br/)
```

`gitpr badge` imprime-o com uma explicação curta; `gitpr badge --readme` imprime a linha sozinha, que é o que quer para `gitpr badge --readme >> README.md`. De uma forma ou de outra o comando só imprime — colocá-lo é decisão sua, porque só você sabe onde fica bem no seu README.

---

## 6. Configuração

| Onde | Nome | Observações |
| --- | --- | --- |
| `~/.gitpr/.env` | `GITPR_BADGE` | Ligado por predefinição; `false` desliga o selo. Só de leitura — o GitPR nunca a escreve |
| Ecrã de configuração | **Selo de pull request** | Secção Geral, o mesmo interruptor, com a predefinição explícita na descrição |
| `gitpr --init` | Aviso | Mostrado quando a forge é configurada, junto com o interruptor que o desliga |
| `gitpr --no-edit` | Aviso | Mostrado quando um selo foi anexado a um corpo que não viu |

---

## 7. Variáveis de Ambiente

| Variável | Para que serve |
| --- | --- |
| `GITPR_BADGE` | `false` (ou `0`, `no`, `off`, `n`) publica corpos de pull request sem o selo |
| `GITPR_LANG` | Idioma da interface. O selo em si é sempre em inglês |

> **Nota:** Veja também a [documentação de Publicação de PR no GitHub](pull-request-publication.pt_pt.md) para o fluxo ao qual o selo é anexado, e a [documentação do Linter Estático Personalizável](linter-regras-customizadas.pt_pt.md) para as regras de onde vêm as contagens — o selo não tem o que relatar enquanto essas regras não existirem.
