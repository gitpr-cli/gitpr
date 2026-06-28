# Como formatar e atualizar uma issue do GitHub via CLI

## Ferramenta usada

GitHub CLI (`gh`) — permite editar issues diretamente do terminal, sem abrir o browser.

### Instalação (se não tiver)

Baixe o zip portátil (sem precisar instalar):
```
https://github.com/cli/cli/releases/latest
```
Extraia e use o `gh.exe` direto, ou instale via `winget install GitHub.cli`.

### Autenticação

```bash
gh auth login
# Escolha: GitHub.com → HTTPS → Login via browser
```

---

## Estrutura de formatação das issues

As issues do projeto seguem o padrão **O Que / Por Que / Onde / Como**:

```markdown
## Título descritivo da implementação

### O Que (What)

- [x] **Funcionalidade A:** descrição do que foi feito.
- [x] **Funcionalidade B:** descrição do que foi feito.

### Por Que (Why)

Contexto e motivação da tarefa — qual problema resolve e por quê foi necessário.

### Onde (Where)

Página: Nome da página
URL: `/rota/da/pagina`

### Como (How)

1. **Backend (Laravel):**
   - Arquivo criado/alterado e o que faz.
2. **Banco de Dados:**
   - Migrations criadas/alteradas.
3. **Frontend (Vue/Inertia):**
   - Componentes criados/alterados.

---

## Avisos de Impacto

- **Item crítico:** descrição e consequência se ignorado.
- **Dependência:** o que precisa estar configurado.
```

---

## Comando para atualizar a issue

Escreva o conteúdo em um arquivo `.md` e use:

```bash
gh issue edit <NUMERO_DA_ISSUE> --repo <ORG>/<REPO> --body-file caminho/para/arquivo.md
```

**Exemplo real usado neste projeto:**
```bash
gh issue edit 13131 --repo EngenhariadeProcessos/SIG-JB --body-file feat_issue_13131_formatted.md
```

O comando retorna a URL da issue atualizada.

---

## Dica: usando AI para gerar o conteúdo

Você pode passar a descrição técnica da sua tarefa para um AI (ex: Claude) com o seguinte pedido:

> "Formate o texto abaixo como uma issue GitHub seguindo a estrutura O Que / Por Que / Onde / Como, com itens concluídos em `- [x]`, seção de Backend/Banco/Frontend no Como, e uma seção de Avisos de Impacto no final. Sem emojis nos títulos."

Cole a descrição técnica junto e ele gera o markdown pronto para usar no `gh issue edit`.
