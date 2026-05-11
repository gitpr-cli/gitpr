# 🧪 Como testar sem gastar versão no PyPI

Antes de fazermos o upload de novo para o PyPI e gastar a versão `0.1.1` , **vamos testar na sua própria máquina**.

## Instale no modo "Desenvolvedor" (Editável)

Em vez de usar o comando normal, adicione a flag -e (de editable):

Abra o terminal, garanta que está na raiz do projeto e rode:

```bash
pip install -e .

```
> (Atenção ao espaço e ao ponto no final)
*(Esse ponto `.` no final significa "instale o pacote deste diretório atual").*


### 🪄 Por que isso é mágico?
Quando você usa o -e, o Python não copia os arquivos. Ele cria um atalho (link simbólico) direto para a sua pasta de desenvolvimento.
Isso significa que, a partir de agora, qualquer alteração que você salvar no VS Code já vai valer instantaneamente no terminal, sem nunca mais precisar rodar pip install para testar!

Depois de instalar, digite `gitpr` no seu terminal. Se o banner abrir bonitão e não der o erro do módulo, bingo! O problema está resolvido.

## Publicar uma nova versão

Para publicar no PyPI e só rodar a dobradinha:

```bash
pipenv run python -m build
pipenv run twine upload dist/*

```
> Verifique se na pasta /dist não existe mais nenhuma outro arquivo, como o gitpr.exe isso causa um erro.
