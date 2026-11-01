# Entrevista — decisões e premissas

## Pedido original
Ao criar uma issue com `gitpr -is`, registrar o número em `.gitpr/conf/github.yml` (provider GitHub). No `gitpr` seguinte, se a última issue registrada ainda estiver aberta, perguntar se deve adicionar `close #N` ao final da descrição do PR, antes do badge.

## Respostas da rodada 1

| # | Tema | Decisão |
|---|---|---|
| Q1 | Versionamento do arquivo | Fica no `.gitignore`, não é versionado. |
| Q2 | Chave de usuário | **Não há subdivisão por usuário.** Como o arquivo não é versionado, o registro é único por repositório local. Isso substitui a exigência original de subdividir por usuário. |
| Q3 | Dados guardados | `number`, `title`, `url`, `created_at`, `branch`, `repo` (`owner/name`). |
| Q4 | Branch | Não influencia a decisão. A branch é gravada só como informação. |
| Q5 | Falha na verificação | Sem pergunta, aviso de uma linha, fluxo segue. |
| Q6 | Ciclo de vida | Issue fechada, inexistente ou PR: limpar em silêncio. "Sim" e PR criado: limpar. "Não": manter. Nova `gitpr -is`: sobrescrever. |
| Q7 | Momento da pergunta | Antes da geração da descrição. O fluxo abre primeiro a TUI de stage. Veja a premissa P1. |
| Q8 | Texto | `close #N` em linha própria, antes do badge, sem duplicar. |
| Q9 | Branch de destino | Mostrar aviso quando a branch de destino configurada não for a padrão do repositório. A decisão continua com o usuário. |
| Q10 | Modo não interativo | Nunca pergunta. Flags `--close-issue` e `--no-close-issue`. Opção para ligar/desligar na TUI "config". |
| Q11 | Quem grava | Todo caminho que cria issue no GitHub (CLI, TUI de Issue, MCP, chat) usa a mesma função de gravação. |
| Q12 | Escopo | Só GitHub, usando o `ScmProvider` já implementado. Outros provedores ficam para o futuro. |

## Premissas assumidas (confirmar na T0)

- **P1.** A resposta da Q7 estava ambígua. Interpretei assim: a pergunta é feita no início do fluxo `gitpr`, **antes** da TUI de stage, e a resposta fica em memória até a montagem da descrição. Se você preferir perguntar depois da TUI de stage e antes de chamar a IA, só o ponto de chamada muda (T6). O restante da spec não depende disso.
- **P2.** A branch de destino do PR já é conhecida no início do fluxo, pois vem da configuração do usuário.
- **P3.** Resposta padrão do prompt: **Sim** (Enter confirma), porque esse é o seu fluxo habitual.
- **P4.** "Não perguntar mais para esta issue" não foi pedido e fica fora do escopo.
- **P5.** O `.gitignore` recebe a entrada `.gitpr/conf/` automaticamente na primeira gravação, com aviso de uma linha (ADR-001).
- **P6.** O selo (badge) já pode existir ou não no corpo do PR. Se não existir, a linha de fechamento vai ao fim do corpo.
