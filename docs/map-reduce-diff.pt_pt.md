# 📦 Como o GitPR Lida com Diffs Gigantes (Map-Reduce)

Se o GitPR exibiu a mensagem **"📦 Diff gigante detetado! A processar em N lotes (Map-Reduce)..."**, as suas alterações eram demasiado grandes para serem analisadas pela IA numa única chamada. Não te preocupes — nada se perde. Esta página explica o que acontece nos bastidores.

## 🔍 Porque existe um limite de tamanho?

Os modelos de IA têm uma janela de contexto limitada. O GitPR estima o tamanho do teu diff usando a regra segura de **4 caracteres por token**. Quando a estimativa ultrapassa os **90.000 tokens** (cerca de 360.000 caracteres), uma única chamada à API poderia falhar, truncar a análise ou produzir resultados de baixa qualidade.

## ⚙️ Como funciona o pipeline Map-Reduce?

1. **Divisão (Split):** o diff é dividido em lotes, respeitando sempre os limites de ficheiro (os cabeçalhos `diff --git`). Um ficheiro nunca é cortado ao meio.
2. **Map:** cada lote é enviado à IA, que devolve um resumo técnico do que mudou naquela parte. A consola mostra o progresso:

   ```text
   📦 Diff gigante detetado! A processar em 4 lotes (Map-Reduce)...
   ⏳ A analisar o lote 1/4...
   ⏳ A analisar o lote 2/4...
   ```

3. **Reduce:** os resumos parciais são unificados e enviados numa chamada final que gera o resultado real — a mensagem de commit (`-c`), o code review (`-r`/`-f`) ou a descrição do Pull Request (comando padrão).

## 💡 Convém saber

- **Totalmente automático:** não existe flag para ativar. O chunking só entra em ação quando o diff ultrapassa o limite; diffs mais pequenos continuam a usar uma única chamada à IA.
- **Mesmo fornecedor e modelo:** os lotes usam o motor de IA que configuraste (Gemini, DeepSeek ou Ollama), com uma pausa de 1 segundo entre chamadas para respeitar os limites de pedidos.
- **Os smart excludes vêm primeiro:** lock files, assets minificados e outros ruídos são removidos do diff antes da estimativa de tamanho — o que muitas vezes evita o chunking por completo.
- **Compromisso de qualidade:** o resultado final é gerado a partir de resumos técnicos em vez do diff em bruto, pelo que detalhes muito finos podem ser condensados. Para branches gigantes, dividir o trabalho em PRs mais pequenos continua a dar à IA o melhor material possível.

🔗 Repositório: [github.com/natanfiuza/gitpr](https://github.com/natanfiuza/gitpr)
