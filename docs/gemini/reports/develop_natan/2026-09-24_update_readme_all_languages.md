## Completion Report — Sincronização e Atualização do README em Todos os Idiomas

### What was done
- Analisou a base de código e documentações técnicas em busca de novas funcionalidades implementadas e não documentadas no README principal (`README.md`).
- Documentou novos subcomandos: `gitpr config`, `gitpr release`, `gitpr fix [<finding_id>]`, `gitpr split`, `gitpr tests generate`, `gitpr explain`, `gitpr review-pr <pr_number>`.
- Documentou novas opções e flags: `--init`, `--explain`, `--no-suggest-reviewers`.
- Atualizou a seção do Publicador de Pull Request com suporte multi-forge (GitHub, GitLab, Bitbucket Cloud, Azure DevOps) e sugestão automática de revisores via `git blame`.
- Atualizou a seção de Linter Local com a integração de pontas SAST (Semgrep, Gitleaks, Bandit) e verificação embutida de segredos/tokens de alta entropia.
- Adicionou links para novos guias técnicos na seção de Configuração e Infraestrutura (`config-tui`, `scm-multiforge`, `suggested-reviewers`, `usage-log`).
- Sincronizou todas as adições de forma simétrica em todos os 5 idiomas suportados (`README.md` [EN], `README.pt_br.md` [PT-BR], `README.pt_pt.md` [PT-PT], `README.es_es.md` [ES-ES], `README.fr_fr.md` [FR-FR]).

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `README.md` | docs | Adicionadas novas features, comandos, flags, multi-forge e links de docs em inglês |
| `README.pt_br.md` | docs | Adicionadas novas features, comandos, flags, multi-forge e links de docs em português brasileiro |
| `README.pt_pt.md` | docs | Adicionadas novas features, comandos, flags, multi-forge e links de docs em português de Portugal |
| `README.es_es.md` | docs | Adicionadas novas features, comandos, flags, multi-forge e links de docs em espanhol |
| `README.fr_fr.md` | docs | Adicionadas novas features, comandos, flags, multi-forge e links de docs em francês |

### Impact
- **Functionality:** Os arquivos README agora refletem 100% dos comandos, subcomandos e recursos disponíveis no GitPR CLI.
- **Performance:** N/A (alteração puramente em documentação).
- **Compatibility:** Total paridade e simetria entre as 5 traduções oficiais do projeto.

### Next steps (if applicable)
- Manter os arquivos de documentação sincronizados conforme novas funcionalidades forem criadas nas branches de desenvolvimento.
