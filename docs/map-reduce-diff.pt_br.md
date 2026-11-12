# 📦 Como o GitPR Lida com Diffs Gigantes (Map-Reduce)

Se o GitPR exibiu a mensagem **"📦 Diff gigante detectado! Processando em N lotes (Map-Reduce)..."**, suas alterações eram grandes demais para serem analisadas pela IA em uma única chamada. Não se preocupe — nada se perde. Esta página explica o que acontece nos bastidores.

## 🔍 Por que existe um limite de tamanho?

Modelos de IA têm uma janela de contexto limitada. O GitPR estima o tamanho do seu diff usando a regra segura de **4 caracteres por token**. Quando a estimativa ultrapassa **90.000 tokens** (cerca de 360.000 caracteres), uma única chamada de API poderia falhar, truncar a análise ou produzir resultados de baixa qualidade.

## ⚙️ Como funciona o pipeline Map-Reduce?

1. **Divisão (Split):** o diff é dividido em lotes limitados a **50.000 tokens** cada (`GITPR_MAP_REDUCE_MAX_PART_TOKENS`). Embora os limites de arquivo (`diff --git`) sejam preservados sempre que possível, arquivos individuais que ultrapassem esse teto são particionados em cascata (fronteiras de hunks `@@` e fatias de linhas), repetindo o cabeçalho do arquivo e marcadores contextuais em cada fatia para que nenhum lote estoure os limites do modelo (como o teto de 1.048.576 tokens do Gemini).
2. **Map:** cada lote é enviado à IA, que retorna um resumo técnico do que mudou naquela parte. O console mostra o progresso:

   ```text
   📦 Diff gigante detectado! Processando em 4 lotes (Map-Reduce)...
   ⏳ Analisando lote 1/4...
   ⏳ Analisando lote 2/4...
   ```

3. **Reduce:** os resumos parciais são unificados e enviados em uma chamada final que gera o resultado real — a mensagem de commit (`-c`), o code review (`-r`/`-f`) ou a descrição do Pull Request (comando padrão). Se o conjunto de resumos exceder o teto de disparo, uma redução intermediária consolida os resumos de forma limpa antes da análise final.

## 💡 Bom saber

- **Totalmente automático:** não existe flag para ativar. O chunking só entra em ação quando o diff ultrapassa o limite de disparo (**90.000 tokens** por padrão); diffs menores continuam usando uma única chamada de IA.
- **Limites configuráveis por provider:** você pode customizar tanto o teto de disparo (`GITPR_MAP_REDUCE_MAX_TOKENS`) quanto o tamanho máximo de cada lote (`GITPR_MAP_REDUCE_MAX_PART_TOKENS`), globalmente ou especificamente por provedor (`GITPR_MAP_REDUCE_MAX_TOKENS_<PROVIDER>`, `GITPR_MAP_REDUCE_MAX_PART_TOKENS_<PROVIDER>`) via `gitpr config` ou no `~/.gitpr/.env`. Veja também [ADR-0022](adr/0022-map-reduce-per-provider-token-partitioning.md).
- **Mesmo provedor e modelo:** os lotes usam o motor de IA que você configurou (Gemini, DeepSeek ou Ollama), com pausa de 1 segundo entre as chamadas para respeitar limites de requisição.
- **Smart excludes vêm primeiro:** lock files, assets minificados e outros ruídos são removidos do diff antes da estimativa de tamanho — o que muitas vezes evita o chunking por completo.
- **Custo de qualidade:** o resultado final é gerado a partir de resumos técnicos em vez do diff bruto, então detalhes muito finos podem ser condensados. Para branches gigantes, dividir o trabalho em PRs menores continua dando à IA o melhor material possível.

🔗 Repositório: [https://github.com/gitpr-cli/gitpr.git](https://github.com/gitpr-cli/gitpr.git)
