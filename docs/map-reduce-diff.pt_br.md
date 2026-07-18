# 📦 Como o GitPR Lida com Diffs Gigantes (Map-Reduce)

Se o GitPR exibiu a mensagem **"📦 Diff gigante detectado! Processando em N lotes (Map-Reduce)..."**, suas alterações eram grandes demais para serem analisadas pela IA em uma única chamada. Não se preocupe — nada se perde. Esta página explica o que acontece nos bastidores.

## 🔍 Por que existe um limite de tamanho?

Modelos de IA têm uma janela de contexto limitada. O GitPR estima o tamanho do seu diff usando a regra segura de **4 caracteres por token**. Quando a estimativa ultrapassa **90.000 tokens** (cerca de 360.000 caracteres), uma única chamada de API poderia falhar, truncar a análise ou produzir resultados de baixa qualidade.

## ⚙️ Como funciona o pipeline Map-Reduce?

1. **Divisão (Split):** o diff é dividido em lotes, sempre respeitando os limites de arquivo (os cabeçalhos `diff --git`). Um arquivo nunca é cortado ao meio.
2. **Map:** cada lote é enviado à IA, que retorna um resumo técnico do que mudou naquela parte. O console mostra o progresso:

   ```text
   📦 Diff gigante detectado! Processando em 4 lotes (Map-Reduce)...
   ⏳ Analisando lote 1/4...
   ⏳ Analisando lote 2/4...
   ```

3. **Reduce:** os resumos parciais são unificados e enviados em uma chamada final que gera o resultado real — a mensagem de commit (`-c`), o code review (`-r`/`-f`) ou a descrição do Pull Request (comando padrão).

## 💡 Bom saber

- **Totalmente automático:** não existe flag para ativar. O chunking só entra em ação quando o diff ultrapassa o limite; diffs menores continuam usando uma única chamada de IA.
- **Mesmo provedor e modelo:** os lotes usam o motor de IA que você configurou (Gemini, DeepSeek ou Ollama), com pausa de 1 segundo entre as chamadas para respeitar limites de requisição.
- **Smart excludes vêm primeiro:** lock files, assets minificados e outros ruídos são removidos do diff antes da estimativa de tamanho — o que muitas vezes evita o chunking por completo.
- **Custo de qualidade:** o resultado final é gerado a partir de resumos técnicos em vez do diff bruto, então detalhes muito finos podem ser condensados. Para branches gigantes, dividir o trabalho em PRs menores continua dando à IA o melhor material possível.

🔗 Repositório: [github.com/natanfiuza/gitpr](https://github.com/natanfiuza/gitpr)
