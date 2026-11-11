# Guia de Publicação e Configuração nos Marketplaces (VS Code & Cursor)

Este guia fornece instruções passo a passo para publicar a **Extensão de Editor do GitPR** no **Visual Studio Marketplace** (para o VS Code) e no **Open VSX Registry** (para o Cursor e outros editores de código aberto).

---

## Visão Geral

A publicação é totalmente automatizada via GitHub Actions (`.github/workflows/extension.yml`). Quando uma etiqueta (tag) de lançamento oficial (`ext-v*`) é enviada, o fluxo de trabalho:
1. Valida que a versão da tag git corresponde rigorosamente ao campo `"version"` em `extensions/vscode/package.json`.
2. Compila o TypeScript e executa os testes de integração do Mocha.
3. Empacota a extensão num pacote `.vsix` contendo o ícone oficial e a licença.
4. **Cria um GitHub Release oficial** com o pacote `.vsix` anexado permanentemente para descarregamento direto.
5. Avalia `VSCE_PAT` e `OVSX_PAT` de forma independente (**Granular Marketplace Gate**):
   - Se `VSCE_PAT` estiver configurado, publica no Visual Studio Marketplace.
   - Se `OVSX_PAT` estiver configurado, publica no Open VSX Registry.
   - Se algum dos segredos estiver em falta, regista uma notificação informativa e uma tabela de resumo no fluxo sem bloquear o GitHub Release.

---

## Configuração Rápida com o Assistente de Marketplaces (Recomendado)

Para agilizar a geração de tokens, validação local via CLI e aprovisionamento de segredos no repositório, execute o assistente interativo:

```bash
chmod +x scripts/marketplace-setup-wizard.sh
./scripts/marketplace-setup-wizard.sh
```

O assistente orienta o registo no Azure DevOps e no Open VSX, abre as páginas de configuração no navegador, valida os tokens localmente (`vsce verify-pat`, `ovsx verify-pat`), aprovisiona `VSCE_PAT` e `OVSX_PAT` nos secrets do repositório GitHub via `gh secret set`, e oferece opcionalmente a criação e envio da etiqueta (tag) de lançamento `ext-v0.1.0`.

Para instruções manuais detalhadas, siga as secções abaixo.

---

## 1. Configuração do Visual Studio Marketplace (Microsoft / VS Code)

### Passo 1.1: Organização no Azure DevOps
1. Inicie sessão no [Azure DevOps](https://dev.azure.com) com a conta Microsoft que faz a gestão da extensão do GitPR.
2. Se ainda não possui uma organização, crie uma (por exemplo, `natanfiuza` ou o nome da organização de desenvolvimento pretendido).

### Passo 1.2: Gerar Personal Access Token (PAT)
1. No Azure DevOps, clique no ícone de engrenagem **User Settings** (canto superior direito, junto à foto de perfil) e selecione **Personal access tokens**.
2. Clique em **+ New Token**.
3. Preencha os detalhes:
   - **Name**: `gitpr-marketplace-publish`
   - **Organization**: Selecione **All accessible organizations**. *(Crucial: o vsce exige um PAT com âmbito multi-organização).*
   - **Expiration**: Selecione 1 ano (ou 90 dias, consoante as políticas de segurança).
   - **Scopes**: Clique em **Show all scopes** no fundo, desloque-se até **Marketplace** e selecione:
     - `Acquire`
     - `Manage` (permite publicar extensões)
4. Clique em **Create** e **copie o PAT de imediato**.

### Passo 1.3: Criar Publisher no Visual Studio Marketplace
1. Aceda ao [Portal de Gestão do Visual Studio Marketplace](https://marketplace.visualstudio.com/manage).
2. Clique em **Create publisher**.
3. Introduza os detalhes:
   - **ID**: `natanfiuza` *(deve corresponder a `"publisher": "natanfiuza"` em `package.json`)*.
   - **Name**: `Natan Fiuza`
   - **Email**: `contato@natanfiuza.dev.br`
4. Confirme a criação.

### Passo 1.4: Adicionar o Segredo ao GitHub
1. No repositório do GitHub, navegue até **Settings > Secrets and variables > Actions**.
2. Clique em **New repository secret**.
3. Nome: `VSCE_PAT`
4. Valor: Cole o seu Personal Access Token do Azure DevOps.

---

## 2. Configuração do Open VSX Registry (Eclipse Foundation / Cursor)

O Open VSX Registry suporta a pesquisa de extensões no Cursor, VSCodium, Gitpod e outros IDEs abertos.

### Passo 2.1: Criar Conta
1. Aceda a [open-vsx.org](https://open-vsx.org) e inicie sessão utilizando a sua conta do GitHub (`natanfiuza`).

### Passo 2.2: Regista o Namespace
1. Aceda à secção [Open VSX Namespaces](https://open-vsx.org/user-settings/namespaces) ou solicite a criação do namespace `natanfiuza`.
2. Se a criação self-service estiver disponível nas suas definições de utilizador, crie o namespace `natanfiuza` *(deve corresponder a `"publisher": "natanfiuza"` em `package.json`)*.
3. Se a titularidade do namespace exigir verificação, associe a sua organização do GitHub ou perfil pessoal conforme as instruções do Open VSX.

### Passo 2.3: Gerar Access Token
1. Aceda a [User Settings > Access Tokens](https://open-vsx.org/user-settings/tokens) em open-vsx.org.
2. Crie um novo token (por exemplo, `gitpr-ovsx-token`).
3. Copie a cadeia de caracteres (string) do token gerado.

### Passo 2.4: Adicionar o Segredo ao GitHub
1. No repositório do GitHub, navegue até **Settings > Secrets and variables > Actions**.
2. Clique em **New repository secret**.
3. Nome: `OVSX_PAT`
4. Valor: Cole o seu Access Token do Open VSX.

---

## 3. Verificação Local e Dry-Run (Opcional)

Antes de desencadear o lançamento público, pode testar a autenticação e o empacotamento localmente:

### Verificar PATs com as CLIs
```bash
cd extensions/vscode

# Testar PAT do Visual Studio Marketplace
npx @vscode/vsce verify-pat natanfiuza -p "<O_SEU_VSCE_PAT>"

# Testar PAT do Open VSX
npx ovsx verify-pat -p "<O_SEU_OVSX_PAT>"
```

### Teste Local de Empacotamento
```bash
npm run compile
npm test
npm run package
```
Isto produz `gitpr-0.1.0.vsix` contendo `images/icon.png`, `LICENSE.txt`, bundles compilados e ficheiros de manifesto.

---

## 4. Desencadear o Lançamento Automatizado

Quando estiver pronto para publicar uma nova versão:

1. Certifique-se de que `extensions/vscode/package.json` possui a versão pretendida para o lançamento (por exemplo, `"version": "0.1.0"`).
2. Submeta (commit) quaisquer alterações pendentes na `main` ou no seu ramo (branch) de lançamento.
3. Crie e envie uma tag git anotada correspondente a `ext-v<versão>`:
   ```bash
   git tag ext-v0.1.0
   git push origin ext-v0.1.0
   ```
4. O GitHub Actions executará o fluxo de trabalho **Editor Extension**:
   - Valida que `ext-v0.1.0` corresponde a `0.1.0`.
   - Executa os testes e compila o VSIX.
   - **Cria o GitHub Release** com `gitpr-0.1.0.vsix` anexado como recurso (asset).
   - Publica automaticamente no Visual Studio Marketplace e/ou Open VSX Registry caso os respetivos segredos (`VSCE_PAT`, `OVSX_PAT`) estejam configurados. Caso ainda não estejam configurados, o VSIX permanece disponível no GitHub Releases e a publicação nos mercados digitais será ativada assim que os segredos forem adicionados.

---

## 5. Manutenção e Lançamentos Futuros

- **Atualização de versão**: Atualize `"version"` em `extensions/vscode/package.json` e envie a tag correspondente (por exemplo, `ext-v0.1.1`).
- **Expiração de tokens**: Os PATs do Azure DevOps expiram após um máximo de 1 ano. Lembre-se de regenerar o `VSCE_PAT` e atualizar o segredo do repositório antes da expiração.
