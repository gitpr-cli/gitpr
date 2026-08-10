# ⚠️ Porque é que o GitPR ignorou os meus ficheiros novos?

Se executou o GitPR e recebeu um aviso de que **ficheiros não monitorizados (untracked)** foram detetados, não se preocupe! Este é um comportamento de segurança e otimização nativo do sistema.

## 🔍 O que significa "Não Monitorizado"?

Quando cria um ficheiro novo no seu projeto, o Git não o rastreia automaticamente. Ele fica no estado *Untracked*. O comando que o GitPR usa para ler o seu código (`git diff HEAD`) analisa apenas os ficheiros que o Git já conhece ou que foram preparados para commit (*Staged*).

## 🛡️ Porque é que o GitPR não lê esses ficheiros automaticamente?

Desenhámos o GitPR com três pilares em mente:
1. **Segurança (Prevenção de Fugas):** Imagine que cria um ficheiro `.env.local` com palavras-passe da base de dados de produção e se esquece de o colocar no `.gitignore`. Se o GitPR lesse tudo automaticamente, enviaria as suas palavras-passe para a API da IA.
2. **Economia de Tokens (Dinheiro):** Alguns frameworks geram pastas gigantes de cache ou ficheiros compilados. Enviar lixo para a IA consumiria os seus tokens à toa e tornaria a resposta extremamente lenta.
3. **Padrão Git:** O GitPR respeita o ciclo de vida oficial do Git. A IA só analisa o que você, enquanto programador, decide que tem valor.

## ✅ Como resolver?

A solução é muito simples. Só precisa de dizer ao Git quais os ficheiros novos que fazem parte do seu próximo commit usando o comando `add`:

```bash
# Para adicionar um ficheiro específico:
git add src/meu_novo_arquivo.py

# OU para adicionar todos os ficheiros novos de uma vez:
git add .

```

Depois de executar o `git add`, basta executar o comando do **GitPR** novamente. A IA agora verá as suas novidades e gerará a análise perfeitamente! 🚀

## 🔎 Verificação Rápida: Quais ficheiros não estão em stage?

Pode verificar rapidamente quais ficheiros não estão em stage usando a flag `--status` — **sem IA, sem rede, instantâneo**:

```bash
gitpr --status
```

Isto mostra todas as alterações não commitadas em 3 categorias: novos (não rastreados), modificados e eliminados. Consulte a [documentação do Git Status](git-status.pt_pt.md) para mais detalhes.

## 🛑 Ignorar a verificação de unstaged

Se quiser ignorar a verificação de ficheiros unstaged que é executada antes dos comandos de IA, use:

```bash
gitpr -c --no-unstaged-check
```

Ou defina `GITPR_SKIP_UNSTAGED_CHECK=true` no seu ficheiro `~/.gitpr/.env` para ignorar permanentemente.

> 📖 **Documentação completa:** [docs/git-status.pt_pt.md](git-status.pt_pt.md) — cobre `--status`, `--no-unstaged-check`, ferramentas MCP e a verificação de unstaged que agora é executada em todos os comandos (`-c`, `-r`, `-f`, `-is`).
