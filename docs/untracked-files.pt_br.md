# ⚠️ Por que o GitPR ignorou meus arquivos novos?

Se você rodou o GitPR e recebeu um aviso de que **arquivos não monitorados (untracked)** foram detectados, não se preocupe! Este é um comportamento de segurança e otimização nativo do sistema.

## 🔍 O que significa "Não Monitorado"?

Quando você cria um arquivo novo no seu projeto, o Git não o rastreia automaticamente. Ele fica no estado *Untracked*. O comando que o GitPR usa para ler o seu código (`git diff HEAD`) analisa apenas os arquivos que o Git já conhece ou que foram preparados para commit (*Staged*).

## 🛡️ Por que o GitPR não lê esses arquivos automaticamente?

O GitPR foi desenhado com três pilares em mente:
1. **Segurança (Prevenção de Vazamentos):** Imagine que você crie um arquivo `.env.local` com senhas do banco de dados de produção e esqueça de colocá-lo no `.gitignore`. Se o GitPR lesse tudo automaticamente, ele enviaria suas senhas para a API da IA.
2. **Economia de Tokens (Dinheiro):** Alguns frameworks geram pastas gigantes de cache ou arquivos compilados. Enviar lixo para a IA consumiria seus tokens atoa e deixaria a resposta extremamente lenta.
3. **Padrão Git:** O GitPR respeita o ciclo de vida oficial do Git. A IA só analisa o que você, como desenvolvedor, decide que tem valor.

## ✅ Como resolver?

A solução é muito simples. Você só precisa dizer ao Git quais arquivos novos fazem parte do seu próximo commit usando o comando `add`:

```bash
# Para adicionar um arquivo específico:
git add src/meu_novo_arquivo.py

# OU para adicionar todos os arquivos novos de uma vez:
git add .

```

Após rodar o `git add`, basta rodar o comando do **GitPR** novamente. A IA agora enxergará as suas novidades e gerará a análise perfeitamente! 🚀

## 🔎 Verificação Rápida: Quais arquivos não estão em stage?

Você pode verificar rapidamente quais arquivos não estão em stage usando a flag `--status` — **sem IA, sem rede, instantâneo**:

```bash
gitpr --status
```

Isso mostra todas as alterações não commitadas em 3 categorias: novos (não rastreados), modificados e deletados. Veja a [documentação do Git Status](git-status.pt_br.md) para mais detalhes.

## 🛑 Pular a verificação de unstaged

Se quiser pular a verificação de arquivos unstaged que roda antes dos comandos de IA, use:

```bash
gitpr -c --no-unstaged-check
```

Ou defina `GITPR_SKIP_UNSTAGED_CHECK=true` no seu arquivo `~/.gitpr/.env` para pular permanentemente.

> 📖 **Documentação completa:** [docs/git-status.pt_br.md](git-status.pt_br.md) — cobre `--status`, `--no-unstaged-check`, ferramentas MCP e a verificação de unstaged que agora roda em todos os comandos (`-c`, `-r`, `-f`, `-is`).