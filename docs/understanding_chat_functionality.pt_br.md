# Entendendo o Chat Interativo do GitPR

O Chat Interativo do GitPR é um **assistente de pair-programming com IA** que roda diretamente no seu terminal. Ele enxerga suas alterações não commitadas (`git diff`) e mantém uma conversa contextual, ajudando você a entender, refatorar, testar e otimizar seu código.

## Iniciando o Chat

```bash
gitpr -ch
# ou
gitpr --chat
```

Para sobrescrever o idioma da interface em uma sessão:

```bash
gitpr --lang en_us -ch
gitpr --lang pt_br -ch
```

## Atalhos de Teclado

| Tecla | Ação | Descrição |
|-------|------|-----------|
| **F1** | Ajuda | Abre um modal mostrando todos os atalhos e comandos slash |
| **F2** | Atualizar Diff | Atualiza o contexto da IA com as últimas alterações de código |
| **F5** | Auto-Patch | Extrai blocos de código da última resposta da IA e salva em arquivo |
| **F6** | Exportar | Salva toda a conversa em um arquivo Markdown estruturado |
| **Esc** | Sair | Fecha o aplicativo de chat |

## Comandos Slash

Digite `/` no campo de entrada para ver uma lista suspensa de comandos disponíveis. Continue digitando para filtrar.

| Comando | Descrição |
|---------|-----------|
| `/explain` | Explica o diff atual linha por linha |
| `/tests` | Gera testes unitários para as funções alteradas |
| `/optimize` | Analisa complexidade ciclomática e sugere melhorias de performance |
| `/clear` | Limpa a conversa e inicia uma nova sessão de chat para o diff atual |

Você pode digitar um comando parcial (ex.: `/ex`) e pressionar **Enter** — ele auto-completa para o comando completo.

## Memória e Sessões

O chat persiste automaticamente sua conversa e histórico de diffs em disco:

- **Local:** `~/.gitpr/cache/chat/<UUID>/`
- **Chave da sessão:** Um UUID único de 15 caracteres (formato `XXXX-XXXXX-XXXX`) gerado por branch e repositório
- **Persistência:** Retornar à mesma branch reabre a sessão existente com todo o histórico da conversa
- **Rastreamento de diff:** Cada alteração de código é registrada. A IA sabe quando você modificou arquivos e atualiza seu contexto

## Auto-Patch (F5)

Quando a IA sugere alterações de código (em blocos Markdown), pressione **F5** para extraí-las e salvá-las:

1. A última resposta da IA é escaneada por blocos de código com crases triplas (` ```python ... ``` `)
2. Todos os blocos são concatenados e salvos em `GITPR_PATCH_SUGGESTION_<chave-aleatoria>.txt`
3. Cada chave é única (formato `aB3-xK9`), então patches anteriores nunca são sobrescritos

Revise o arquivo gerado e aplique as alterações manualmente no seu projeto.

### Ações por Mensagem (Ctrl+Shift+A / Ctrl+Shift+E)

Você pode aplicar Auto-Patch e Exportar em **qualquer** mensagem da IA na conversa, não apenas na última.

Navegue entre as mensagens da IA usando **F7** e **F8**. A mensagem em foco é destacada com uma borda esquerda mais brilhante, e uma barra de ações aparece acima do campo de entrada.

- **Ctrl+Shift+S** — Extrai blocos de código apenas da **mensagem em foco** e salva em `GITPR_PATCH_SUGGESTION_<chave>.txt`
- **Ctrl+Shift+E** — Exporta apenas a **mensagem em foco** para `MESSAGE_<id-sessao>_<chave>.md`

O foco padrão é sempre a resposta mais recente da IA.

## Exportar (F6)

Pressione **F6** para salvar toda a conversa em um arquivo Markdown estruturado:

- **Nome do arquivo:** `GITPR_CHAT_EXPORT_<uuid-da-sessão>.md`
- **Formato:** Cada mensagem é rotulada com seu papel (Usuário / Assistente IA / Sistema) e separada por linhas horizontais
- **Casos de uso:** Documentação, compartilhamento com a equipe ou alimentação de contexto para outras ferramentas de IA

## Atualizar Diff (F2)

Enquanto programa em outro editor, pressione **F2** para atualizar o contexto do chat:

- Se novas alterações forem detectadas desde o último snapshot do diff, a IA é notificada e passa a ver suas edições mais recentes
- Se nada mudou, uma mensagem de confirmação é exibida

## Saindo do Chat

Pressione **Esc** ou **Ctrl+C** para fechar o chat. Sua sessão é salva automaticamente.

## Dicas

- Use `/clear` para começar do zero se a conversa ficar muito longa ou se quiser mudar de tópico
- Combine `--lang` com `--provider` para personalizar idioma e modelo de IA: `gitpr --lang pt_br --provider gemini -ch`
- Os arquivos `GITPR_CHAT_EXPORT_*.md` podem ser commitados no seu repositório como notas de desenvolvimento
