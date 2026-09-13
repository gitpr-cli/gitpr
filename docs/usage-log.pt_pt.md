# Registo de Utilização — todo comando que o GitPR executa

O GitPR mantém um registo do seu próprio uso: uma linha por cada comando, gravada no momento em que o comando começa. É a resposta a "o que é que eu executei realmente, e quando?" — útil quando uma flag se comportou de forma inesperada, quando quer saber com que frequência um recurso é usado, ou quando está a reconstruir o que aconteceu num repositório na semana passada.

O registo é local, em texto simples, e nunca sai da sua máquina. Nada é enviado para lado nenhum.

---

## 1. Onde Ficam os Ficheiros

Cada comando acrescenta uma linha em `~/.gitpr/logs/<uuid>.log`, e há **um ficheiro por dia**:

```text
~/.gitpr/logs/
├── 4b1c8d3e-1f27-5a44-9c0b-7d2e5f8a1b30.log   ← hoje
├── 9f2a7c10-6b83-5e21-8a4d-1c9f0e7b2d55.log   ← ontem
└── pr_desc/                                   ← o registo de publicação de PR, um recurso separado
```

O nome do ficheiro é um UUID **derivado da data** — `uuid5` de `gitpr.usage.<YYYY-MM-DD>` — e não um aleatório. Isto é propositado: um nome aleatório precisaria de um contador ou de um ficheiro de estado para saber qual ficheiro pertence a hoje, e dois processos do GitPR a correr no mesmo instante poderiam discordar sobre isso. Derivado da data, o mesmo dia resolve sempre para o mesmo nome, pelo que comandos simultâneos limitam-se a acrescentar ao mesmo ficheiro.

Um novo dia começa um novo ficheiro. O GitPR nunca roda nem apaga estes ficheiros — limpar os antigos é tarefa sua.

---

## 2. O Que Contém uma Linha

```text
[2026-09-12 14:32:01] | v1.0.0 | gitpr -c | gitpr-cli/gitpr | Nataniel Fiuza <natan.fiuza@gmail.com>
```

| Campo | Origem | Notas |
| --- | --- | --- |
| Data e hora | o relógio local, quando o comando começa | `YYYY-MM-DD HH:MM:SS` |
| Versão | a versão do GitPR em execução | |
| Comando | o nome do programa e as flags exatamente como foram escritas | `gitpr -c`, `gitpr-mcp --list` |
| Repositório | `remote.origin.url`, reduzida a `owner/repo` | `-` fora de um repositório, ou sem remote de origem |
| Autor | `user.name` e `user.email` da configuração do Git | `-` quando o Git não tem identidade configurada |

O repositório é reduzido ao seu caminho, seja qual for a forge: `git@github.com:owner/repo.git`, `https://gitlab.com/group/repo` e `https://dev.azure.com/org/project/_git/repo` tornam-se `owner/repo`, `group/repo` e `org/project/repo`.

Toda invocação é registada, incluindo `--help` e as que falham. No caso do servidor MCP isso significa a sua partida: o `gitpr-mcp` grava uma linha quando o servidor arranca, não uma por chamada de ferramenta.

---

## 3. Como Desligar

Quem controla é a `GITPR_SHOW_LOGS`, e vem **ligada** por omissão — todas as instalações já têm a linha semeada em `~/.gitpr/.env`.

| Onde | Como |
| --- | --- |
| No ecrã de configuração | `gitpr config` → **Geral** → **Salvar logs gerais** |
| No ficheiro | `GITPR_SHOW_LOGS=false` em `~/.gitpr/.env` |
| Numa única execução | `GITPR_SHOW_LOGS=false gitpr -c` |

O ambiente vence sempre o ficheiro (veja [o ecrã de configuração](config-tui.pt_pt.md) §2), pelo que a última linha desliga aquele comando específico sem mexer em mais nada.

Desligar interrompe novas linhas. Não apaga o que já lá está.

---

## 4. O Que Não Regista

O registo é deliberadamente enxuto: regista *que* um comando correu e *qual* foi, e nada sobre o que leu ou produziu.

Nunca contém o diff, conteúdo de ficheiros, caminhos de ficheiros, texto de prompt ou de skill, respostas da IA, as mensagens de commit e descrições de PR geradas, nem qualquer credencial.

Os dois valores pessoais que guarda — o repositório e o autor do Git — ficam na máquina, já que o ficheiro é local e nada é transmitido.

---

## 5. Notas para Programadores

| Ficheiro | Papel |
| --- | --- |
| `src/usage_log.py` | O recurso completo: derivação do caminho, a consulta única ao git, o formato da linha e a gravação |
| `src/main.py` | Uma chamada no topo do callback raiz — o ponto único por onde passa toda a flag, todo o subcomando e o `--help` |
| `src/mcp_server.py` | Uma chamada em `main()`, porque o script de consola `gitpr-mcp` nunca carrega o `main.py` |

Duas garantias que a implementação dá de propósito:

- **A gravação é síncrona.** Uma thread de fundo — como faz o registador de métricas locais — perde a entrada sempre que o processo termina antes de a thread ser escalonada, e um registo que descarta comandos em silêncio é pior do que nenhum registo.
- **Nunca atrapalha um comando.** Todas as falhas — sem git, sem permissão, sem diretório home — são engolidas: `log_usage()` regressa sem gravar e o comando continua. Também nunca imprime nada, porque o servidor MCP reserva o stdout para o seu fluxo JSON-RPC.

Acrescentar um terceiro ponto de entrada significa acrescentar uma chamada nele. Nada chega ao registo sozinho.
