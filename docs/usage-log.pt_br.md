# Log de Uso — todo comando que o GitPR executa

O GitPR mantém um registro do próprio uso: uma linha para cada comando, gravada no momento em que o comando começa. É a resposta para "o que eu realmente executei, e quando?" — útil quando uma flag se comportou de forma inesperada, quando você quer saber com que frequência um recurso é usado, ou quando está reconstruindo o que aconteceu em um repositório na semana passada.

O log é local, em texto puro, e nunca sai da sua máquina. Nada é enviado a lugar nenhum.

---

## 1. Onde os Arquivos Ficam

Todo comando acrescenta uma linha em `~/.gitpr/logs/<uuid>.log`, e há **um arquivo por dia**:

```text
~/.gitpr/logs/
├── 4b1c8d3e-1f27-5a44-9c0b-7d2e5f8a1b30.log   ← hoje
├── 9f2a7c10-6b83-5e21-8a4d-1c9f0e7b2d55.log   ← ontem
└── pr_desc/                                   ← o log de publicação de PR, um recurso separado
```

O nome do arquivo é um UUID **derivado da data** — `uuid5` de `gitpr.usage.<YYYY-MM-DD>` — e não um aleatório. Isso é proposital: um nome aleatório precisaria de um contador ou de um arquivo de estado para saber qual arquivo pertence a hoje, e dois processos do GitPR rodando no mesmo instante poderiam discordar sobre isso. Derivado da data, o mesmo dia sempre resolve para o mesmo nome, então comandos simultâneos simplesmente acrescentam ao mesmo arquivo.

Um novo dia começa um novo arquivo. O GitPR nunca rotaciona nem apaga esses arquivos — limpar os antigos é tarefa sua.

---

## 2. O Que uma Linha Contém

```text
[2026-09-12 14:32:01] | v1.0.0 | gitpr -c | gitpr-cli/gitpr | Nataniel Fiuza <natan.fiuza@gmail.com>
```

| Campo | Origem | Observações |
| --- | --- | --- |
| Data e hora | o relógio local, quando o comando começa | `YYYY-MM-DD HH:MM:SS` |
| Versão | a versão do GitPR em execução | |
| Comando | o nome do programa e as flags exatamente como digitadas | `gitpr -c`, `gitpr-mcp --list` |
| Repositório | `remote.origin.url`, reduzida a `owner/repo` | `-` fora de um repositório, ou sem remote de origem |
| Autor | `user.name` e `user.email` da configuração do Git | `-` quando o Git não tem identidade configurada |

O repositório é reduzido ao seu caminho, qualquer que seja a forge: `git@github.com:owner/repo.git`, `https://gitlab.com/group/repo` e `https://dev.azure.com/org/project/_git/repo` viram `owner/repo`, `group/repo` e `org/project/repo`.

Toda invocação é registrada, incluindo `--help` e as que falham. No caso do servidor MCP isso significa a sua partida: o `gitpr-mcp` grava uma linha quando o servidor sobe, não uma por chamada de ferramenta.

---

## 3. Como Desligar

Quem controla é a `GITPR_SHOW_LOGS`, e ela vem **ligada** por padrão — toda instalação já tem a linha semeada em `~/.gitpr/.env`.

| Onde | Como |
| --- | --- |
| Na tela de configuração | `gitpr config` → **Geral** → **Salvar logs gerais** |
| No arquivo | `GITPR_SHOW_LOGS=false` em `~/.gitpr/.env` |
| Em uma única execução | `GITPR_SHOW_LOGS=false gitpr -c` |

O ambiente sempre vence o arquivo (veja [a tela de configuração](config-tui.pt_br.md) §2), então a última linha desliga aquele comando específico sem mexer em mais nada.

Desligar interrompe novas linhas. Não apaga o que já está lá.

---

## 4. O Que Ele Não Registra

O log é deliberadamente enxuto: registra *que* um comando rodou e *qual* foi, e nada sobre o que ele leu ou produziu.

Ele nunca contém o diff, conteúdo de arquivos, caminhos de arquivos, texto de prompt ou de skill, respostas da IA, as mensagens de commit e descrições de PR geradas, nem qualquer credencial.

Os dois valores pessoais que ele guarda — o repositório e o autor do Git — ficam na máquina, já que o arquivo é local e nada é transmitido.

---

## 5. Notas para Desenvolvedores

| Arquivo | Papel |
| --- | --- |
| `src/usage_log.py` | O recurso inteiro: derivação do caminho, a consulta única ao git, o formato da linha e a gravação |
| `src/main.py` | Uma chamada no topo do callback raiz — o ponto único por onde passa toda flag, todo subcomando e o `--help` |
| `src/mcp_server.py` | Uma chamada em `main()`, porque o script de console `gitpr-mcp` nunca carrega o `main.py` |

Duas garantias que a implementação dá de propósito:

- **A gravação é síncrona.** Uma thread de fundo — como faz o registrador de métricas locais — perde a entrada sempre que o processo termina antes de a thread ser escalonada, e um log que descarta comandos em silêncio é pior do que nenhum log.
- **Ela nunca atrapalha um comando.** Toda falha — sem git, sem permissão, sem diretório home — é engolida: `log_usage()` retorna sem gravar e o comando segue. Ela também nunca imprime nada, porque o servidor MCP reserva o stdout para o seu fluxo JSON-RPC.

Adicionar um terceiro ponto de entrada significa acrescentar uma chamada nele. Nada chega ao log sozinho.
