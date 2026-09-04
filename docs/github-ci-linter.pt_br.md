# **Documentação Técnica: Integração de Linter Local com GitHub Actions**

Esta documentação descreve o processo de implementação do `gitpr --linter` como um "Quality Gate" no ciclo de vida de desenvolvimento, impedindo que códigos que violem as regras estáticas do projeto sejam integrados à branch principal.

---

## **1. Funcionamento Técnico**

O comando `gitpr --linter` foi projetado para operar com **códigos de saída (exit codes)** semânticos:

* **Exit Code 0:** Sucesso. Nenhuma violação encontrada.  
* **Exit Code 1:** Falha. Violações detectadas (bloqueia o workflow do GitHub).

Diferente dos modos de IA, o modo linter não requer chaves de API, tornando-o ideal para ambientes de execução efêmeros.

---

## **2. Configuração do Workflow (.yml)**

Crie o arquivo `.github/workflows/gitpr-linter.yml` no seu repositório com a configuração abaixo. Esta action será disparada em todos os Pull Requests destinados às branches `main` ou `develop`.

```yaml
name: 🛡️ GitPR Static Analysis

on:  
  pull_request:  
    branches: [ "main", "develop" ]

jobs:  
  linter-validation:  
    runs-on: ubuntu-latest  
      
    steps:  
      - name: 📥 Checkout do Repositório  
        uses: actions/checkout@v4  
        with:  
          # Necessário para permitir o 'git diff' contra a branch base  
          fetch-depth: 0 

      - name: 🐍 Setup Python Environment  
        uses: actions/setup-python@v5  
        with:  
          python-version: '3.12'

      - name: ⚙️ Instalação de Dependências  
        run: |  
          git clone https://github.com/gitpr-cli/gitpr.git.git /tmp/gitpr  
          pip install google-genai python-dotenv click cryptography pyyaml

      - name: 🚨 Execução do Linter Local  
        # O workflow falhará automaticamente se o exit code for 1  
        run: python /tmp/gitpr/src/main.py --linter
```

---

## **3. Travamento do Botão de Merge (Branch Protection)**

Apenas configurar o arquivo `.yml` não impede fisicamente o merge; ele apenas indica a falha. Para "travar" o botão de merge, siga estes passos na interface do GitHub:

1. Vá em **Settings** > **Branches**.  
2. Em **Branch protection rules**, clique em **Add rule** (ou Edit na regra da `main`).  
3. Marque a opção: **"Require status checks to pass before merging"**.  
4. No campo de busca que aparecerá, procure por: `linter-validation` (ou o nome do job definido no seu YAML).  
5. Marque também **"Require branches to be up to date before merging"** para garantir que o diff testado seja o mais recente.  
6. Clique em **Save changes**.

---

## **4. Benefícios da Implementação**

* **Zero Latência de IA:** A validação é baseada em Regex local, levando milissegundos.  
* **Custo Zero:** Não consome tokens da API Gemini.  
* **Segurança:** Bloqueia strings sensíveis (senhas, IPs de teste, logs de debug) antes do Code Review humano.
