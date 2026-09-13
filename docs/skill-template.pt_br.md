# Documentação Técnica: Sistema de Skills e Templates (--skill)

O GitPR utiliza um sistema de **Skills** (Prompt Engineering) que permite customizar o comportamento da inteligência artificial de acordo com as regras de negócio da sua empresa. Os arquivos de template atuam como *System Instructions* da IA.

---

## 1. Baixar os Templates

```bash
gitpr -s
# ou
gitpr --skill
```

Este comando cria os seguintes arquivos na pasta `.gitpr/skill/` do projeto:

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
https://github.com/gitpr-cli/gitpr.git/tree/main/templates/
```

O comando `--skill` faz download da versão mais recente de cada template do repositório oficial.

> **Nota:** Os arquivos de skill podem ser commitados no repositório da sua equipa para partilhar as regras com todos os developers.

---

## 5. Editar pela tela `gitpr config`

A tela `gitpr config` tem uma seção **Skills** que lista estes mesmos arquivos e abre cada um num editor, para ajustar uma regra sem sair do terminal ([Tela de Configuração Interativa](config-tui.pt_br.md), §1.7).

- Uma entrada por skill suportada pelo GitPR — os sete arquivos `.gitpr.*.md` da seção 1 acima.
- Uma skill que o projeto ainda não tem é listada como **não está neste projeto**, com um botão **📥 Baixar o template** que busca o template publicado para o seu idioma de interface.
- O `F2` grava as skills editadas junto com as configurações do `.env`; o `Ctrl+R` dentro do painel descarta a edição e devolve o texto do disco.
- Cada arquivo mantém o fim de linha que já tinha, então gravar nunca transforma uma linha intocada em alteração.

Duas coisas ficam de fora dessa lista de propósito: o `.gitpr.linter.yml`, que nenhum comando carrega por esse mecanismo ([Regras Customizadas do Linter](linter-regras-customizadas.pt_br.md)), e qualquer outro arquivo que você guarde em `.gitpr/skill/` — a tela oferece as skills que os comandos leem, não tudo o que a pasta contém.
