# Documentação Técnica: Sistema de Skills e Templates (--skill)

O GitPR utiliza um sistema de **Skills** (Prompt Engineering) que permite customizar o comportamento da inteligência artificial de acordo com as regras de negócio da sua empresa. Os arquivos de template atuam como *System Instructions* da IA.

---

## 1. Baixar os Templates

```bash
gitpr -s
# ou
gitpr --skill
```

Este comando cria os seguintes arquivos na raiz do seu projeto:

| Arquivo | Função |
| --- | --- |
| `.gitpr.commit.md` | Regras para geração de mensagens de commit |
| `.gitpr.pr.md` | Estrutura exigida para descrição de Pull Request |
| `.gitpr.review.md` | Foco de arquitetura para code review de diffs |
| `.gitpr.filereview.md` | Regras de coesão para auditoria de arquivo completo |
| `.gitpr.issue.md` | Estrutura e detalhe para geração de Issues |
| `.gitpr.blame.md` | Foco da análise arqueológica de código |
| `.gitpr.linter.yml` | Regras de regex para validação estática |

> **Importante:** O comando `--skill` **nunca sobrescreve** arquivos locais existentes. Se um `.gitpr.*.md` já existir, ele é preservado.

---

## 2. Como Funciona

Cada comando do GitPR procura automaticamente pelo arquivo de skill correspondente:

| Comando | Arquivo de skill usado |
| --- | --- |
| `gitpr -c` | `.gitpr.commit.md` |
| `gitpr` (padrão) | `.gitpr.pr.md` |
| `gitpr -r` / `gitpr -f` | `.gitpr.review.md` |
| `gitpr -r -i arquivo` | `.gitpr.filereview.md` |
| `gitpr -is` | `.gitpr.issue.md` |
| `gitpr -b arquivo` | `.gitpr.blame.md` |
| `gitpr -l` / `gitpr -r` | `.gitpr.linter.yml` |

Se o arquivo de skill não existir, o GitPR usa um template interno padrão.

---

## 3. Exemplo de Customização

**Ficheiro `.gitpr.commit.md`:**

```markdown
Todas as mensagens de commit DEVEM:
- Usar prefixo JIRA obrigatório: [PROJ-1234]
- Seguir Conventional Commits (feat, fix, refactor...)
- Ser escritas em português (Brasil)
- Não exceder 72 caracteres na linha de assunto
```

Após criar este arquivo, todas as execuções de `gitpr -c` seguirão estas regras.

---

## 4. Templates Remotos

Os templates oficiais estão disponíveis em:
```
https://github.com/natanfiuza/gitpr/tree/main/templates/
```

O comando `--skill` faz download da versão mais recente de cada template do repositório oficial.

> **Nota:** Os arquivos de skill podem ser commitados no repositório da sua equipa para partilhar as regras com todos os developers.
