# Documentação Técnica: Interface Gráfica de Terminal (TUI) — Issues

Esta documentação descreve o funcionamento da interface gráfica interativa (TUI) do GitPR para a geração e gestão de Issues, construída com a biblioteca Python `textual`.

---

## 1. O que é a TUI de Issues?

Quando você executa o comando `gitpr --issue` (ou `-is`), o GitPR analisa o seu código e abre um painel interativo diretamente no terminal. Isso permite que você revise, edite e aprimore a issue gerada pela Inteligência Artificial antes de salvá-la ou enviá-la para o repositório remoto.

---

## 2. Motores de Contexto (3 Modos de Geração)

A funcionalidade de Issues possui **3 motores de contexto** distintos, acionados conforme as flags combinadas com `--issue`. Cada motor alimenta a IA com um conjunto diferente de informações, adequado ao momento do ciclo de desenvolvimento.

### 2.1 Issue de Código Novo — `gitpr -is`

**Contexto:** `git diff` atual (alterações não commitadas).

```bash
gitpr -is
```

| Característica | Descrição |
| --- | --- |
| **Fonte de dados** | Diff local (`git diff HEAD`) |
| **Quando usar** | Antes de commitar — você acabou de programar e quer documentar a tarefa |
| **Resultado** | Issue descrevendo exatamente o que está no seu working tree |
| **Ideal para** | Documentação rápida de features, correções e refatorações recém-implementadas |

> **Dica:** Este é o modo mais rápido. A IA lê apenas as linhas que você alterou e gera uma issue focada e objetiva.

---

### 2.2 Issue de Épico / Release — `gitpr -is -ht`

**Contexto:** Histórico completo da branch atual (Git Log + Cache de PRs anteriores).

```bash
gitpr -is -ht
```

| Característica | Descrição |
| --- | --- |
| **Fonte de dados** | `git log` da branch + cache local de PRs gerados pelo GitPR |
| **Quando usar** | Ao final de uma feature branch com múltiplos commits ou ao fechar uma release |
| **Resultado** | Issue consolidada com o panorama completo de tudo que foi desenvolvido |
| **Ideal para** | Épicos, releases, features grandes que levaram vários dias/commits para serem concluídas |

> **Dica:** O GitPR vasculha o histórico de commits exclusivos da sua branch e os relatórios de PR já gerados para montar uma visão de alto nível. Se não houver commits exclusivos ou PRs anteriores, o comando exibirá um aviso e abortará.

---

### 2.3 Issue Arqueológica / Dívida Técnica — `gitpr -is -b arquivo:linhas`

**Contexto:** Linha do tempo de um bloco específico de código via `git blame`.

```bash
gitpr -is -b src/core.py:140-195
```

| Característica | Descrição |
| --- | --- |
| **Fonte de dados** | `git blame` (histórico de alterações linha a linha) + rastreamento de commits pai (até 4 níveis) |
| **Quando usar** | Ao identificar código legado que precisa de refatoração ou documentar dívida técnica |
| **Resultado** | Issue contendo a cronologia do bloco: quando surgiu, quem alterou, como evoluiu e por que precisa ser refatorado |
| **Ideal para** | Documentar dívidas técnicas, justificar refatorações, entender a evolução de código crítico |

> **Dica:** Pode usar o formato interativo também: `gitpr -is -b arquivo` (sem especificar linhas). O GitPR perguntará quais linhas investigar.

---

## 3. Estrutura da Issue (O Que / Por Que / Onde / Como)

A IA do GitPR é instruída a gerar o rascunho da issue seguindo um padrão rigoroso de engenharia de software para facilitar a comunicação da equipe:

| Seção | Descrição |
| --- | --- |
| **O Que (What)** | Checklists diretos sobre as funcionalidades criadas ou problemas identificados |
| **Por Que (Why)** | O contexto e a motivação técnica por trás da implementação |
| **Onde (Where)** | Especificação das rotas, módulos, páginas ou recursos afetados |
| **Como (How)** | Detalhamento técnico dividido em Backend/Motor, Banco de Dados/Dados e Frontend/CLI/Interface |

> **Personalização:** Você pode customizar o template usado pela IA através do arquivo `.gitpr.issue.md` na raiz do projeto (baixe com `gitpr -s`).

---

## 4. Atalhos e Navegação da TUI

A interface foi desenhada para ser rápida e dispensar o uso constante do mouse. Você pode navegar pelos campos usando a tecla `Tab` e utilizar os seguintes atalhos:

| Tecla | Ação | Descrição |
| --- | --- | --- |
| **`F1`** | Ajuda | Abre um modal flutuante com instruções rápidas de uso da interface |
| **`F2`** | Salvar `.md` Local | Exporta o conteúdo da tela para um arquivo Markdown na pasta atual do projeto. Ideal para quando você deseja apenas o rascunho para refinar posteriormente |
| **`F3`** | Criar no GitHub | Conecta-se à API REST do GitHub e cria a issue automaticamente no repositório remoto. O link direto para a issue recém-criada será exibido no terminal |
| **`F4`** | Ajuda (alternativo) | Atalho alternativo para abrir as instruções da TUI |
| **`Esc`** | Sair | Aborta a operação e fecha a interface sem salvar nenhuma alteração |
| **`Tab`** | Navegar | Alterna o foco entre os campos de título e corpo da issue |

---

## 5. Integração com GitHub (Token PAT)

Para criar issues diretamente no repositório remoto (`F3`), o GitPR precisa de um **Personal Access Token (PAT)** do GitHub com escopo `repo`.

### 5.1 Configuração do Token

Na primeira vez que usar `F3`, o GitPR irá:

1. Detetar que não há token configurado
2. Exibir a URL de geração do token com os parâmetros pré-preenchidos (escopo `repo`)
3. Solicitar que você cole o token gerado
4. Armazená-lo criptografado (Fernet) no arquivo `~/.gitpr/.env`

### 5.2 Segurança

- O token é armazenado como hash criptografado — nunca em texto plano
- A chave mestra de desencriptação fica em `~/.gitpr/secret.key`
- Consulte o guia completo em [github-pat-integration.md](github-pat-integration.md)

---

## 6. Exemplos Práticos

### Exemplo 1: Documentar uma feature antes de commitar

```bash
# Você acabou de implementar um sistema de login
gitpr -is
# → A IA lê o diff, gera o rascunho e abre a TUI
# → Revise, ajuste o texto se necessário
# → Pressione F3 para criar a issue no GitHub
```

### Exemplo 2: Gerar uma issue de release

```bash
# Sua branch feature/payment tem 15 commits ao longo de 3 dias
git checkout feature/payment
gitpr -is -ht
# → A IA consolida todo o histórico em uma issue de épico
```

### Exemplo 3: Documentar dívida técnica

```bash
# Você encontrou um bloco de código confuso no arquivo legado
gitpr -is -b src/legacy/parser.py:200-350
# → A IA rastreia a evolução do bloco desde o commit original
# → Gera uma issue explicando a dívida técnica e sugerindo refatoração
```

---

## 7. Arquivos Relacionados

| Arquivo | Função |
| --- | --- |
| `.gitpr.issue.md` | Template local com regras customizadas para geração de issues (baixe com `gitpr -s`) |
| `~/.gitpr/.env` | Configuração global: chaves de API e token GitHub criptografado |
| `~/.gitpr/secret.key` | Chave mestra Fernet para desencriptação das credenciais |

> **Nota:** Consulte também a [documentação principal (README.md)](../README.md) para visão geral de todas as funcionalidades do GitPR.
