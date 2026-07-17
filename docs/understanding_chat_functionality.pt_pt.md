# Compreender o Chat Interativo do GitPR

O Chat Interativo do GitPR é um **assistente de pair-programming com IA** que é executado diretamente no teu terminal. Ele vê as tuas alterações não commitadas (`git diff`) e mantém uma conversa contextual, ajudando-te a compreender, refatorar, testar e otimizar o teu código.

## Iniciar o Chat

```bash
gitpr -ch
# ou
gitpr --chat
```

Para sobrescrever o idioma da interface numa única sessão:

```bash
gitpr --lang en_us -ch
gitpr --lang pt_pt -ch
```

## Atalhos de Teclado

| Tecla | Ação | Descrição |
|-------|------|-----------|
| **F1** | Ajuda | Abre um modal com todos os atalhos e comandos slash |
| **F2** | Atualizar Diff | Atualiza o contexto da IA com as últimas alterações de código |
| **F5** | Auto-Patch | Extrai blocos de código da última resposta da IA e guarda num ficheiro |
| **F6** | Exportar | Guarda toda a conversa num ficheiro Markdown estruturado |
| **Esc** | Sair | Fecha a aplicação de chat |

## Comandos Slash

Digita `/` no campo de entrada para veres uma lista dos comandos disponíveis. Continua a digitar para filtrar.

| Comando | Descrição |
|---------|-----------|
| `/explain` | Explica o diff atual linha a linha |
| `/tests` | Gera testes unitários para as funções alteradas |
| `/optimize` | Analisa a complexidade ciclomática e sugere melhorias de desempenho |
| `/clear` | Limpa a conversa e inicia uma nova sessão de chat para o diff atual |

Podes digitar um comando parcial (ex.: `/ex`) e pressionar **Enter** — faz auto-complete para o comando completo.

## Memória e Sessões

O chat persiste automaticamente a tua conversa e o histórico de diffs em disco:

- **Localização:** `~/.gitpr/cache/chat/<UUID>/`
- **Chave da sessão:** Um UUID único de 15 caracteres (formato `XXXX-XXXXX-XXXX`) gerado por branch e repositório
- **Persistência:** Voltar à mesma branch reabre a sessão existente com todo o histórico da conversa
- **Rastreamento de diff:** Cada alteração de código é registada. A IA sabe quando modificaste ficheiros e atualiza o seu contexto

## Auto-Patch (F5)

Quando a IA sugere alterações de código (em blocos Markdown), pressiona **F5** para as extrair e guardar:

1. A última resposta da IA é analisada à procura de blocos de código com crases triplas (` ```python ... ``` `)
2. Todos os blocos são concatenados e guardados em `GITPR_PATCH_SUGGESTION_<chave-aleatoria>.txt`
3. Cada chave é única (formato `aB3-xK9`), portanto patches anteriores nunca são sobrescritos

Revê o ficheiro gerado e aplica as alterações manualmente no teu projeto.

### Ações por Mensagem (Ctrl+Shift+A / Ctrl+Shift+E)

Podes aplicar Auto-Patch e Exportar em **qualquer** mensagem da IA na conversa, não apenas na última.

Navega entre as mensagens da IA usando **F7** e **F8**. A mensagem em foco é destacada com uma borda esquerda mais brilhante, e uma barra de ações aparece acima do campo de entrada.

- **Ctrl+Shift+S** — Extrai blocos de código apenas da **mensagem em foco** e guarda em `GITPR_PATCH_SUGGESTION_<chave>.txt`
- **Ctrl+Shift+E** — Exporta apenas a **mensagem em foco** para `MESSAGE_<id-sessao>_<chave>.md`

O foco padrão é sempre a resposta mais recente da IA.

## Exportar (F6)

Pressiona **F6** para guardar toda a conversa num ficheiro Markdown estruturado:

- **Nome do ficheiro:** `GITPR_CHAT_EXPORT_<uuid-da-sessão>.md`
- **Formato:** Cada mensagem é rotulada com o seu papel (Utilizador / Assistente IA / Sistema) e separada por linhas horizontais
- **Casos de uso:** Documentação, partilha com a equipa ou fornecimento de contexto para outras ferramentas de IA

## Atualizar Diff (F2)

Enquanto programas noutro editor, pressiona **F2** para atualizar o contexto do chat:

- Se forem detetadas novas alterações desde o último snapshot do diff, a IA é notificada e passa a ver as tuas edições mais recentes
- Se nada mudou, é exibida uma mensagem de confirmação

## Sair do Chat

Pressiona **Esc** ou **Ctrl+C** para fechar o chat. A tua sessão é guardada automaticamente.

## Dicas

- Usa `/clear` para começar do zero se a conversa ficar muito longa ou se quiseres mudar de tópico
- Combina `--lang` com `--provider` para personalizar idioma e modelo de IA: `gitpr --lang pt_pt --provider gemini -ch`
- Os ficheiros `GITPR_CHAT_EXPORT_*.md` podem ser commitados no teu repositório como notas de desenvolvimento
