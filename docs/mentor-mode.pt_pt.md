# Documentação Técnica: Modo Mentor Júnior (gitpr mentor / --mentor)

O `gitpr mentor` transforma apontamentos de revisão de código em feedback pedagógico, prático e formativo. Projetado especialmente para programadores juniores e em aprendizagem, foca-se em explicar **o que** está a acontecer, **porque** é que isso importa na prática, **analogias** do quotidiano e conceitos essenciais **para aprender mais**.

O recurso é estritamente **aditivo e opcional (opt-in)**: a análise técnica original da revisão de código nunca é alterada ou removida.

---

## 1. Visão Geral

O Modo Mentor Júnior atua em duas superfícies complementares:

1. **Flag `-r --mentor` / `-f --mentor`**: Executa o review de código padrão e adiciona automaticamente uma secção formatada `## 🎓 Mentor (Orientação para Juniores)` ao final do relatório (`*_PR_REVIEW.txt` ou `*_PR_FULLREVIEW.txt`).
2. **Comando Avulso `gitpr mentor [--finding <id>]`**: Lê os apontamentos do review mais recente e exibe a orientação didática diretamente no terminal, sem reprocessar o review e sem gravar ficheiros no disco.

### 1.1 Referência de Comandos

```bash
gitpr -r --mentor              # Executa review local e anexa secção do Mentor ao relatório
gitpr -f --mentor              # Executa review completo e anexa secção do Mentor
gitpr mentor                   # Explica os apontamentos do último review no terminal
gitpr mentor --finding FIX-002 # Explica um apontamento específico pelo seu ID
gitpr mentor --provider gemini # Força fornecedor de IA específico
```

---

## 2. Configuração (`~/.gitpr/.env`)

| Chave | Tipo | Padrão | Descrição |
|---|---|---|---|
| `GITPR_REVIEW_MENTOR_MODE` | booleano | `false` | Quando `true`, ativa automaticamente o modo mentor em todo `-r` e `-f`. |
| `GITPR_MENTOR_INCLUDE_ANALOGY` | booleano | `true` | Quando `false`, omite analogias para respostas mais diretas. |

