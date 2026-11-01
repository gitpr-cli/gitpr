# Glossário

| Termo | Definição |
|---|---|
| Registro de issue | Arquivo `.gitpr/conf/github.yml` com a última issue criada por `gitpr -is` neste repositório. |
| Issue registrada | Issue descrita em `last_issue` dentro do registro. |
| Linha de fechamento | Linha `close #N` inserida na descrição do PR. |
| Keyword de fechamento | Palavra que o GitHub reconhece para fechar issue ao mergear (`close`, `closes`, `fix`, `resolve` e variações). |
| Branch padrão | Branch default do repositório no GitHub. O fechamento automático só ocorre quando o PR é mergeado nela. |
| Branch de destino | Branch alvo do PR, configurada pelo usuário no gitpr. |
| Badge | Selo "Reviewed by GitPR" no fim do corpo do PR. |
| Verificação de estado | Consulta ao GitHub para saber se a issue registrada está `open`. |
| Registro obsoleto | Issue fechada, inexistente ou que na verdade é um PR. Deve ser limpa. |
| Registro de outro repositório | Entrada cujo `repo` difere do remote atual. É ignorada, sem limpar. |
| Modo interativo | Execução com terminal (TTY) em que o gitpr pode perguntar ao usuário. |
| Modo não interativo | Sem TTY: CI, scripts, MCP. Nunca pergunta. |
| PrContext | Estrutura em memória que carrega decisões do fluxo `gitpr` até a montagem da descrição. |
| ScmProvider | Abstração de provedor Git já implementada no projeto (GitHub, GitLab etc.). |
