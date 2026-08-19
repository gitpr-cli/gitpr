# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
```text
feat: add --version option and bump version to 0.0.34
```

---

🎯 Summary

Adiciona a flag `--version` ao CLI e exibe a versão atual ao mostrar a ajuda. A versão é atualizada para 0.0.34 e a versão do dicionário de idiomas para 0.0.12.

🛠️ Technical Changes

- Adicionado `@click.version_option` no comando `cli` para exibir a versão via `--version`.
- Exibe a versão no cabeçalho da ajuda (`gitpr v0.0.34`) quando nenhum argumento é fornecido.
- Versão de aplicação atualizada de 0.0.33 para 0.0.34 em `src/updater.py`.
- Versão do dicionário de idiomas atualizada de v0.0.11 para v0.0.12.

⚠️ Impact/Warnings

- Nenhum impacto em banco de dados ou dependências.
- Apenas mudanças cosméticas e de metadados.

close #104