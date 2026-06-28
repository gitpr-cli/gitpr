# Documentação Técnica: Interface Gráfica de Terminal (TUI) - Issues

Esta documentação descreve o funcionamento da interface gráfica interativa (TUI) do GitPR para a geração e gestão de Issues, construída com a biblioteca Python `textual`.

## 1. O que é a TUI de Issues?
Quando você executa o comando `gitpr --issue` (ou `-is`), o GitPR analisa o seu código e abre um painel interativo diretamente no terminal. Isso permite que você revise, edite e aprimore a issue gerada pela Inteligência Artificial antes de salvá-la ou enviá-la para o repositório remoto.

## 2. Estrutura da Issue (O Que / Por Que / Onde / Como)
A IA do GitPR é instruída a gerar o rascunho da issue seguindo um padrão rigoroso de engenharia de software para facilitar a comunicação da equipe:
* **O Que (What):** Checklists diretos sobre as funcionalidades criadas.
* **Por Que (Why):** O contexto e a motivação técnica por trás da implementação.
* **Onde (Where):** Especificação das rotas, módulos ou páginas afetadas.
* **Como (How):** Detalhamento técnico dividido entre Backend, Banco de Dados e Frontend.

## 3. Atalhos e Navegação
A interface foi desenhada para ser rápida e dispensar o uso constante do mouse. Você pode navegar pelos campos usando a tecla `Tab` e utilizar os seguintes atalhos:

* **`F1` (Ajuda):** Abre um modal flutuante com instruções rápidas de uso da interface.
* **`F2` (Salvar Local):** Exporta o conteúdo da tela para um arquivo Markdown (`.md`) na pasta atual do projeto. Ideal para quando você deseja apenas o rascunho para refinar posteriormente.
* **`F3` (Criar no GitHub):** Conecta-se à API REST do GitHub e cria a issue automaticamente no repositório remoto. O link direto para a issue recém-criada será exibido no terminal.
* **`Esc` (Sair):** Aborta a operação e fecha a interface sem salvar nenhuma alteração.