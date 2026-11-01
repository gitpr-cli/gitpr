# ADR-007 — Ciclo de vida do registro
Status: Aceito

| Evento | Ação |
|---|---|
| `gitpr -is` cria issue com sucesso | Sobrescreve `last_issue`. |
| Issue criada pela TUI de Issue, MCP ou chat | Mesma função de gravação. |
| Issue registrada fechada, inexistente ou é PR | Limpa o registro em silêncio. |
| Registro de outro repositório (`repo` diferente do remote) | Ignora, sem limpar. |
| Usuário responde "sim" e o PR é criado com sucesso | Limpa o registro depois da criação. |
| Usuário responde "sim" mas o PR não chega a ser criado | Mantém o registro. |
| Usuário responde "não" | Mantém o registro; a pergunta volta no próximo `gitpr`. |
| Falha de rede na verificação | Mantém o registro. |

Fora de escopo: "não perguntar mais para esta issue".
