# Guia de Publicação e Configuração nos Marketplaces (VS Code e Cursor)

Este guia fornece instruções passo a passo para publicar a **Extensão de Editor do GitPR** no **Visual Studio Marketplace** (para VS Code) e no **Open VSX Registry** (para Cursor e outros editores de código aberto).

---

## Visão Geral

A publicação é totalmente automatizada via GitHub Actions (`.github/workflows/extension.yml`). Quando uma tag de release oficial (`ext-v*`) é enviada, o workflow:
1. Valida que a versão da tag git corresponde estritamente ao campo `"version"` em `extensions/vscode/package.json`.
2. Compila o TypeScript e executa os testes de integração do Mocha.
3. Empacota a extensão em um pacote `.vsix` contendo o ícone oficial e a licença.
4. **Cria um GitHub Release oficial** com o pacote `.vsix` anexado permanentemente para download direto.
5. Avalia `VSCE_PAT` e `OVSX_PAT` de forma independente (**Granular Marketplace Gate**):
   - Se `VSCE_PAT` estiver configurado, publica no Visual Studio Marketplace.
   - Se `OVSX_PAT` estiver configurado, publica no Open VSX Registry.
   - Se algum dos segredos estiver ausente, registra uma notificação informativa e uma tabela de resumo no workflow sem bloquear o GitHub Release.

---

## 1. Configuração do Visual Studio Marketplace (Microsoft / VS Code)

### Passo 1.1: Organização no Azure DevOps
1. Faça login no [Azure DevOps](https://dev.azure.com) com a conta Microsoft que gerencia a extensão do GitPR.
2. Se você ainda não possui uma organização, crie uma (por exemplo, `natanfiuza` ou o nome de organização de desenvolvimento escolhido).

### Passo 1.2: Gerar Personal Access Token (PAT)
1. No Azure DevOps, clique no ícone de engrenagem **User Settings** (canto superior direito, próximo à sua foto de perfil) e selecione **Personal access tokens**.
2. Clique em **+ New Token**.
3. Preencha os detalhes:
   - **Name**: `gitpr-marketplace-publish`
   - **Organization**: Selecione **All accessible organizations**. *(Crucial: o vsce exige um PAT com escopo multi-organização).*
   - **Expiration**: Selecione 1 ano (ou 90 dias, conforme suas políticas de segurança).
   - **Scopes**: Clique em **Show all scopes** na parte inferior, role até **Marketplace** e selecione:
     - `Acquire`
     - `Manage` (permite publicar extensões)
4. Clique em **Create** e **copie o PAT imediatamente**.

### Passo 1.3: Criar Publisher no Visual Studio Marketplace
1. Acesse o [Portal de Gerenciamento do Visual Studio Marketplace](https://marketplace.visualstudio.com/manage).
2. Clique em **Create publisher**.
3. Insira os detalhes:
   - **ID**: `natanfiuza` *(deve corresponder a `"publisher": "natanfiuza"` em `package.json`)*.
   - **Name**: `Natan Fiuza`
   - **Email**: `contato@natanfiuza.dev.br`
4. Confirme a criação.

### Passo 1.4: Adicionar o Segredo ao GitHub
1. No repositório do GitHub, navegue até **Settings > Secrets and variables > Actions**.
2. Clique em **New repository secret**.
3. Nome: `VSCE_PAT`
4. Valor: Cole seu Personal Access Token do Azure DevOps.

---

## 2. Configuração do Open VSX Registry (Eclipse Foundation / Cursor)

O Open VSX Registry alimenta a busca de extensões no Cursor, VSCodium, Gitpod e outros IDEs abertos.

### Passo 2.1: Criar Conta
1. Acesse [open-vsx.org](https://open-vsx.org) e faça login utilizando sua conta do GitHub (`natanfiuza`).

### Passo 2.2: Registrar o Namespace
1. Acesse a seção de [Open VSX Namespaces](https://open-vsx.org/user-settings/namespaces) ou solicite a criação do namespace `natanfiuza`.
2. Se a criação self-service estiver disponível nas configurações de usuário, crie o namespace `natanfiuza` *(deve corresponder a `"publisher": "natanfiuza"` em `package.json`)*.
3. Se a titularidade do namespace exigir verificação, vincule sua organização do GitHub ou perfil pessoal conforme instruído pelo Open VSX.

### Passo 2.3: Gerar Access Token
1. Acesse [User Settings > Access Tokens](https://open-vsx.org/user-settings/tokens) no open-vsx.org.
2. Crie um novo token (por exemplo, `gitpr-ovsx-token`).
3. Copie a string do token gerado.

### Passo 2.4: Adicionar o Segredo ao GitHub
1. No repositório do GitHub, navegue até **Settings > Secrets and variables > Actions**.
2. Clique em **New repository secret**.
3. Nome: `OVSX_PAT`
4. Valor: Cole seu Access Token do Open VSX.

---

## 3. Verificação Local e Dry-Run (Opcional)

Antes de disparar o release público, você pode testar a autenticação e o empacotamento localmente:

### Verificar PATs com as CLIs
```bash
cd extensions/vscode

# Testar PAT do Visual Studio Marketplace
npx @vscode/vsce verify-pat natanfiuza -p "<SEU_VSCE_PAT>"

# Testar PAT do Open VSX
npx ovsx verify-pat -p "<SEU_OVSX_PAT>"
```

### Teste Local de Empacotamento
```bash
npm run compile
npm test
npm run package
```
Isso produz `gitpr-0.1.0.vsix` contendo `images/icon.png`, `LICENSE.txt`, bundles compilados e arquivos de manifesto.

---

## 4. Disparando o Release Automatizado

Quando estiver pronto para publicar uma nova release:

1. Certifique-se de que `extensions/vscode/package.json` possui a versão que você deseja lançar (por exemplo, `"version": "0.1.0"`).
2. Faça commit de quaisquer alterações pendentes na `main` ou em sua branch de release.
3. Crie e envie uma tag git anotada correspondente a `ext-v<versão>`:
   ```bash
   git tag ext-v0.1.0
   git push origin ext-v0.1.0
   ```
4. O GitHub Actions executará o workflow **Editor Extension**:
   - Valida que `ext-v0.1.0` corresponde a `0.1.0`.
   - Executa os testes e constrói o VSIX.
   - **Cria o GitHub Release** com `gitpr-0.1.0.vsix` anexado como asset.
   - Publica automaticamente no Visual Studio Marketplace e/ou Open VSX Registry caso os respectivos segredos (`VSCE_PAT`, `OVSX_PAT`) estejam configurados. Caso ainda não estejam configurados, o VSIX permanece disponível no GitHub Releases e a publicação nos marketplaces será ativada assim que os segredos forem adicionados.

---

## 5. Manutenção e Releases Futuras

- **Incremento de versão**: Atualize `"version"` em `extensions/vscode/package.json` e envie a tag correspondente (por exemplo, `ext-v0.1.1`).
- **Expiração de tokens**: Os PATs do Azure DevOps expiram após no máximo 1 ano. Lembre-se de regenerar o `VSCE_PAT` e atualizar o segredo do repositório antes da expiração.
