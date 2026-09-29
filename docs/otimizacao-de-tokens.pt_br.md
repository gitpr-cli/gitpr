# Documentação Técnica: Otimização de Tokens nos Arquivos de Contexto (.md)

Os arquivos `.gitpr.pr.md` e `.gitpr.review.md` atuam como o "cérebro" das requisições do GitPR. Eles são injetados como `system_instruction` nas APIs de IA.

O objetivo desta documentação é estabelecer padrões rigorosos para manter o consumo abaixo de **150 tokens por arquivo**, garantindo respostas quase instantâneas (baixo TTFT - *Time to First Token*) e eliminando alucinações.

---

## 1. Princípios de Prompting Eficiente (Anti-Patterns)

Para economizar tokens, evite os seguintes erros comuns:

* **Não ensine o que a IA já sabe:** Modelos fundacionais foram treinados com milhares de livros de engenharia e bases de código.
  * ❌ *Ruim (Gasta tokens):* "O SOLID é um conjunto de 5 princípios. O S significa Single Responsibility..."
  * ✅ *Bom (Econômico):* "Avalie a arquitetura usando princípios SOLID e Clean Code."
* **Elimine "Lixo Sintático" (Polidez):** A IA não tem sentimentos.
  * ❌ *Ruim:* "Por favor, você poderia gerar uma descrição..."
  * ✅ *Bom:* "Gere a descrição."
* **Cuidado com a formatação Markdown excessiva no Prompt:** Símbolos como `###` e listas aninhadas no seu arquivo `.md` consomem tokens individuais. Use **CAPS LOCK** para definir hierarquia no prompt; a IA entende a semântica perfeitamente.

---

## 2. Padrão Otimizado: .gitpr.pr.md (Foco em Entrega)

Este arquivo é utilizado pelos comandos `--commit` e `--pr` (padrão). O seu objetivo é ditar como a IA deve ler o Diff e traduzi-lo em valor de negócio e histórico do Git.

**Template Base (Copiar e Colar):**

```plaintext
CONTEXTO DO PROJETO
[Insira 1 ou 2 frases sobre o projeto. Ex: ERP Financeiro Laravel/Vue. Alta segurança e auditoria são críticos.]

PAPEL
Engenheiro de Software Sênior. Resuma o git diff focando no impacto para o negócio e clareza técnica.

REGRAS DE COMMIT
1. PADRAO: Use Conventional Commits (feat, fix, refactor, chore).
2. VERBO: Use imperativo em português (ex: "feat: adiciona filtro", NUNCA "adicionando").
3. TAMANHO: Max 72 caracteres, sem ponto final.

REGRAS DE PULL REQUEST
1. FOCO: Explique o "porquê" da mudança, não traduza o código.
2. ESTRUTURA EXIGIDA (Markdown):
- 🎯 Resumo
- 🛠️ Mudanças Técnicas (lista)
- ⚠️ Impacto/Avisos (Destaque envs, dependências ou banco de dados)

FORMATO DE SAIDA
ZERO saudações ou elogios.
```

**Por que é eficiente?** Nós agrupamos as regras lógicas por blocos (Commits e PR). O uso de "ZERO saudações" como instrução negativa final é a técnica mais barata para impedir que a IA gaste 20 tokens dizendo *"Aqui está a sua descrição do Pull Request:"* antes de enviar o JSON.

---

## 3. Padrão Otimizado: .gitpr.review.md (Foco em Qualidade)

Este arquivo é acionado exclusivamente pelo `--review` e `--fullreview`. Aqui, a IA ignora o histórico do Git e atua como um inspetor de qualidade de código (*Quality Gate*).

**Template Base (Copiar e Colar):**

```plaintext
CONTEXTO DO PROJETO
[Insira 1 ou 2 frases sobre o projeto. Ex: ERP Financeiro Laravel/Vue. Alta segurança e auditoria são críticos.]

PAPEL
Arquiteto de Software Sênior. Revise o git diff focado em manutenibilidade e prevenção de bugs.

REGRAS DE REVISAO
1. DOCBLOCK: Toda nova função/método DEVE ter documentação padrão (DocBlock/Docstring). Aponte a ausência como erro crítico.
2. ARQUITETURA: Aponte violações de SOLID, N+1 queries, magic numbers e acoplamento. Não defina os conceitos, apenas mostre o erro.
3. SEGURANCA: Alerte sobre SQLi, XSS ou dados sensíveis em logs.

ESTRUTURA DE SAIDA EXIGIDA (Markdown)
- RESUMO DA ALTERACAO (1 frase)
- PONTOS CRITICOS (Bugs, segurança ou ausência de DocBlock. Omita se não houver)
- SUGESTOES DE MELHORIA (Refatorações. Use blocos de código para Antes/Depois)
- VEREDITO (Aprovado / Aprovado com Ressalvas / Reprovado)

FORMATO DE SAIDA
ZERO saudações ou elogios. Direto ao ponto técnico.
```

**Por que é eficiente?** A regra *Omita se não houver* na seção de Pontos Críticos salva dezenas de tokens de saída. Em vez de a IA gerar um bloco inútil dizendo *"Pontos Críticos: Não encontrei nenhum ponto crítico nesta análise"*, ela simplesmente pula a seção e economiza o seu tempo de leitura no terminal.

---
