# Tarefa: Remover binário do release e forçar atualização via pip

## Contexto

O projeto atualmente publica um binário (`gitpr.exe`, Windows) em cada release. Essa funcionalidade deve ser removida. Em seu lugar, a detecção de nova versão (já implementada) deve passar a exigir que o usuário execute `pip install --upgrade gitpr-cli`.

## Regras de implementação

1. Remover completamente a geração e o upload do binário `gitpr.exe` no pipeline de release.
2. Remover qualquer step, job ou configuração de build relacionada à geração desse binário (empacotamento, assinatura, compressão, etc.).
3. Na rotina existente de detecção de nova tag/release, adicionar bloqueio obrigatório: ao detectar versão mais nova, instruir e/ou forçar o usuário a executar `pip install --upgrade gitpr-cli` antes de continuar o uso da ferramenta.
4. Não implementar fallback, flag ou modo de compatibilidade que mantenha o binário disponível.
5. Atualizar o `README` removendo toda menção ao `gitpr.exe` como artefato de release ou método de instalação.
6. Atualizar todos os documentos em `docs/` removendo referências ao `gitpr.exe`, ajustando instruções de instalação/atualização para refletir exclusivamente o fluxo via `pip`.
7. Revisar changelog, scripts de release e templates de release notes para eliminar referências ao binário.
8. Não gerar código de exemplo na resposta — aplicar as alterações diretamente nos arquivos do projeto.
9. Validar, ao final, que nenhuma ocorrência de `gitpr.exe` permanece no repositório (código, pipeline, documentação).
