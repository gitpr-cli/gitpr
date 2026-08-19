# Correção de bugs no modal de erros do linter (fluxo gitpr)

## Contexto

Ao executar o comando `gitpr`, a interface de publicação do pull request é aberta e dispara um processo de commit. Esse processo executa o linter local antes de gerar a mensagem de commit. Quando o linter encontra erros, um modal é exibido com a lista de erros e opções de ação.

## Problemas a corrigir

1. **Sobreposição de botões**: no modal de erros do linter, o botão "Fazer commit com --no-verify" está sobreposto ao botão "Abort". Ajustar o layout para que os dois botões fiquem posicionados lado a lado, sem sobreposição.

2. **Botão sem funcionalidade**: ao clicar em "Fazer commit com --no-verify", nenhuma ação é executada. O modal simplesmente fecha e retorna à interface anterior, sem realizar o commit com a flag `--no-verify`. Implementar a execução correta do commit ignorando os hooks do linter.

3. **Tradução ausente**: o botão "Abort" no modal de erros do linter não está traduzido para o idioma da interface. Verificar o sistema de internacionalização e aplicar a tradução correspondente.

## Escopo do trabalho

- Localizar o componente responsável pela renderização do modal de erros do linter.
- Corrigir o CSS/layout para eliminar a sobreposição entre os botões de ação.
- Corrigir o handler do botão "Fazer commit com --no-verify" para que execute o commit com a flag `--no-verify` e feche o modal apenas após a execução ser concluída (com sucesso ou erro tratado).
- Adicionar a chave de tradução faltante para o botão "Abort" no arquivo de idioma correspondente e referenciá-la no componente.
- Validar que ambos os botões continuam funcionais após o reposicionamento visual.
- Testar o fluxo completo: `gitpr` → erro de linter → modal exibido → clique em cada botão → resultado esperado.

## Critério de conclusão

O modal de erros do linter deve exibir os botões "Fazer commit com --no-verify" e "Abort" lado a lado, ambos funcionais e corretamente traduzidos, com o commit `--no-verify` sendo executado de fato ao ser acionado.
