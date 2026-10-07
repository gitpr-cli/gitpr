# Documentação Técnica: Modo Mentor Júnior (gitpr mentor / --mentor)

O `gitpr mentor` transforma apontamentos de revisão de código em feedback pedagógico, prático e formativo. Projetado especialmente para desenvolvedores juniores e em aprendizagem, foca em explicar **o que** está acontecendo, **por que** isso importa na prática, **analogias** do cotidiano e conceitos essenciais **para aprender mais**.

O recurso é estritamente **aditivo e opcional (opt-in)**: a análise técnica original da revisão de código nunca é alterada ou removida.

---

## 1. Visão Geral

O Modo Mentor Júnior atua em duas superfícies complementares:

1. **Flag `-r --mentor` / `-f --mentor`**: Executa o review de código padrão e adiciona automaticamente uma seção formatada `## 🎓 Mentor (Orientação para Juniores)` ao final do relatório (`*_PR_REVIEW.txt` ou `*_PR_FULLREVIEW.txt`).
2. **Comando Avulso `gitpr mentor [--finding <id>]`**: Lê os apontamentos do review mais recente e exibe a orientação didática diretamente no terminal, sem reprocessar o review e sem gravar arquivos no disco.

### 1.1 Referência de Comandos

```bash
gitpr -r --mentor              # Executa review local e anexa seção do Mentor ao relatório
gitpr -f --mentor              # Executa review completo e anexa seção do Mentor
gitpr mentor                   # Explica os apontamentos do último review no terminal
gitpr mentor --finding FIX-002 # Explica um apontamento específico pelo seu ID
gitpr mentor --provider gemini # Força provedor de IA específico
```

| Opção | Descrição |
|---|---|
| **`-r --mentor`** | Anexa orientações pedagógicas ao relatório de review local |
| **`-f --mentor`** | Anexa orientações pedagógicas ao relatório de review completo contra origin/main |
| **`gitpr mentor`** | Exibe orientações no terminal para os apontamentos do último review (até o teto) |
| **`--finding <id>`** | Foca a explicação em um apontamento específico (ex: `FIX-002`) |
| **`--provider <nome>`** | Substitui temporariamente o provedor de IA configurado (`gemini`, `deepseek` ou `ollama`) |

---

## 2. Estrutura da Explicação

Para cada apontamento analisado, a saída do mentor apresenta:

1. **Apontamento Técnico Original**: Mantido intacto como citação (`>`).
2. **O que está acontecendo**: Explicação simples e direta do padrão encontrado no código.
3. **Por que isso importa**: Consequências reais e práticas caso o problema persista (vulnerabilidades, vazamento de recursos, quebras em produção).
4. **Analogia (opcional)**: Baseada em situações do dia a dia ou conceitos fundamentais de programação.
5. **Para aprender mais**: Princípios de arquitetura ou tópicos consolidados para estudo (ex: *Princípio da Responsabilidade Única*, *Prevenção de SQL Injection OWASP*). Nunca contém links ou URLs inventadas.

---

## 3. Configuração (`~/.gitpr/.env`)

| Chave | Tipo | Padrão | Descrição |
|---|---|---|---|
| `GITPR_REVIEW_MENTOR_MODE` | booleano | `false` | Quando `true`, ativa automaticamente o modo mentor em todo `-r` e `-f` sem exigir a flag `--mentor`. |
| `GITPR_MENTOR_INCLUDE_ANALOGY` | booleano | `true` | Quando `false`, instrui a IA a omitir analogias para explicações mais diretas. |

---

## 4. Desempenho, Cache e Teto (Cap)

- **Processamento em Lote**: As explicações são geradas em uma única chamada de IA em lote, em vez de uma chamada por finding.
- **Teto de Segurança (10 apontamentos)**: Se um review gerar mais de 10 apontamentos, os 10 mais graves por severidade (`blocker` > `critical` > `high` > `medium` > `low`) são expandidos. Os demais são listados ao final para consulta avulsa com `gitpr mentor --finding <id>`.
- **Cache Local**: Respostas ficam em cache sob `~/.gitpr/cache/prompts/mentor/<md5>.json`, com zero custo de API em execuções repetidas.

