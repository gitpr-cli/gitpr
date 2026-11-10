# 0017 — Contrato de fallback multilíngue no site de documentação (Degradação Graciosa)

- **Status:** Aceito
- **Data:** 2026-11-10
- **Decisores:** Natan Fiuza, Antigravity
- **Contexto:** Item herdado de acompanhamento de fallback ES/FR no site oficial (`https://gitpr.natanfiuza.dev.br/docs/`), originado na unificação de URLs canônicas em `src/doc_links.py`, `tests/test_doc_links.py`, `README.es_es.md` e `README.fr_fr.md`.

## Contexto e Decisão

O GitPR CLI centralizou em `src/doc_links.py` o contrato de links públicos da documentação técnica oficial:
1. Links em inglês omitem parâmetros de consulta (`https://gitpr.natanfiuza.dev.br/docs/<slug>`);
2. Links localizados anexam parâmetros de linguagem conforme o contrato do site: `?lang=pt_br`, `?lang=pt_pt`, `?lang=es` e `?lang=fr`.

Os arquivos estáticos do repositório (`README.es_es.md` e `README.fr_fr.md`) e os pontos de chamada da CLI (`src/ui/help_screen.py`, `src/ui/chat_app.py`, `src/ui/config_app.py`, `src/core.py`) foram 100% migrados para emitir exclusivamente `?lang=es` e `?lang=fr`, com testes unitários em `tests/test_doc_links.py` que impedem regressões para `?lang=es_es` ou `?lang=fr_fr`.

No entanto, como o portal web de documentação (`gitpr.natanfiuza.dev.br`) é um serviço de publicação separado e a tradução integral de todas as páginas técnicas em espanhol e francês pode ocorrer de forma contínua e assíncrona, havia um item de acompanhamento em aberto: *"os links dos READMEs já usam ?lang=es e ?lang=fr, mas o site ainda pode servir inglês"*.

Decidimos formalizar que **o comportamento do site de servir o conteúdo canônico em inglês com status HTTP 200 na ausência de uma tradução específica em espanhol ou francês é a definição arquitetural correta de Degradação Graciosa (Graceful Degradation)**:

1. **Garantia anti-404**: O usuário que clica em um link de documentação no terminal ou nos READMEs traduzidos nunca deve encontrar erro 404 (Not Found).
2. **Separação de Preocupações**: O repositório do CLI é estritamente responsável por emitir os parâmetros corretos do contrato (`?lang=es`, `?lang=fr`); a infraestrutura web do portal é responsável por resolver o locale solicitado ou degradar com segurança para a versão canônica em inglês.
3. **Fechamento do Item Herdado**: Com a validação do contrato e o estabelecimento da degradação graciosa como comportamento esperado, o item herdado é declarado formalmente **CONCLUÍDO (FECHADO POR PROJETO)**.

## Opções Consideradas

- **Manter o item indefinidamente aberto até 100% das páginas em ES/FR estarem traduzidas:** Rejeitado. Confunde a responsabilidade do software CLI com a esteira editorial contínua de conteúdo do site web, gerando ruído permanente nos relatórios de auditoria do CLI.
- **Configurar o site para retornar erro 404 para traduções ausentes:** Rejeitado. Degrada a experiência do usuário final, impedindo o acesso à documentação técnica em caso de tradução não publicada.
- **Degradação graciosa com HTTP 200 servindo a documentação base em inglês:** **Adotado.** Padrão de resiliência amplamente adotado em sites de documentação técnica multilíngue, mantendo os links válidos e úteis em qualquer idioma.

## Consequências

- O item herdado *"Acompanhar o fallback ES/FR no site"* é formalmente encerrado e deixa de constar como pendência em relatórios de status futuros.
- O conceito ubíquo `Documentation site fallback` fica registrado de forma canônica no `CONTEXT.md`.
- A invariante de links do CLI segue protegida por `tests/test_doc_links.py` (`TestReadmeAndDocsParity.test_readme_es_and_fr_use_site_lang_params`).
