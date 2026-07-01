import subprocess
import click
import re
import os
from datetime import datetime
from src.core import get_current_branch
from src.config import get_api_key, get_api_model, get_ai_provider
from src.ai_providers import call_ai_model

def execute_git_blame(file_path, start_line, end_line, commit_hash=None):
    """Executa o git blame e retorna uma lista de hashes únicos."""
    cmd = ["git", "blame", f"-L", f"{start_line},{end_line}"]
    if commit_hash:
        cmd.append(commit_hash)
    cmd.extend(["--", file_path])

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True
        )
        hashes = set()
        for line in result.stdout.strip().split('\n'):
            if line:
                match = re.match(r'^([a-fA-F0-9]+)\s', line)
                if match:
                    commit = match.group(1)
                    if not commit.startswith('000000'):
                        hashes.add(commit)
        return list(hashes)
    except subprocess.CalledProcessError as e:
        # Se falhar (ex: arquivo não existia naquele commit antigo), silenciamos e retornamos vazio
        return []

def execute_git_show(commit_hash, file_path):
    """Executa o git show para pegar o diff exato."""
    cmd = ["git", "show", commit_hash, "--", file_path]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return None

def get_commit_info(commit_hash):
    """Busca autor, data e mensagem do commit."""
    cmd = ["git", "show", "-s", "--format=%an|%ad|%s", "--date=short", commit_hash]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
        parts = res.stdout.strip().split('|', 2)
        if len(parts) == 3:
            return {"author": parts[0], "date": parts[1], "message": parts[2]}
    except:
        pass
    return {"author": "Desconhecido", "date": "Desconhecida", "message": "Sem mensagem"}

def analyze_commit_with_ai(commit_hash, file_path):
    """Usa a IA para ler o diff e classificar como ORIGEM ou REFATORACAO."""
    diff = execute_git_show(commit_hash, file_path)
    if not diff:
        return {"status": "ORIGEM", "motivo": "Diff não encontrado (arquivo possivelmente criado aqui)."}

    provider = get_ai_provider()
    api_key = get_api_key(provider)
    if not api_key:
        return {"status": "ORIGEM", "motivo": "Sem chave de API. Assumindo origem."}

    # Usamos o modelo 'simple' (Flash/Lite) para economizar dinheiro no loop
    api_model = get_api_model(provider, task_complexity="simple")

    skill_path = os.path.join(os.getcwd(), ".gitpr.blame.md")
    if os.path.exists(skill_path):
        with open(skill_path, "r", encoding="utf-8") as f:
            sys_inst = f.read()
    else:
        sys_inst = 'Você é um Arquiteto de Software. Analise o diff e determine se é a ORIGEM da regra (lógica nova) ou REFATORAÇÃO. Responda APENAS com JSON: {"status": "ORIGEM", "motivo": "Explique o que foi introduzido"} ou {"status": "REFATORACAO", "motivo": "Explique o que foi alterado"}'

    prompt = (
        f"Analise o diff do commit {commit_hash} e retorne o JSON solicitado.\n\n"
        f"DIFF:\n{diff[:4000]}" # Limitamos a 4000 caracteres para não pesar a requisição
    )

    click.secho(f"  🤖 Consultando a IA ({api_model}) sobre o commit {commit_hash[:8]}...", fg="cyan", dim=True)
    
    result_json = call_ai_model(provider, api_key, api_model, prompt, sys_inst)
    
    if result_json and "status" in result_json:
        return result_json
        
    return {"status": "ORIGEM", "motivo": "IA não retornou formato válido."}

def run_blame_analysis(file_path, start_line, end_line, return_data=False):
    """Motor de Loop Temporal que constrói a Timeline consolidada."""
    
    # Se for acionado para retorno de dados (via --issue), silencia os prints
    if not return_data:
        click.secho(f"\n🔍 Iniciando Arqueologia de Código...", fg="cyan", bold=True)
        click.echo(f"📍 Arquivo: {file_path} (Linhas: {start_line} até {end_line})")
    
    initial_commits = execute_git_blame(file_path, start_line, end_line)
    
    if not initial_commits:
        if not return_data: 
            click.secho("⚠️ Nenhum commit rastreável encontrado nestas linhas.", fg="yellow")
        return [] if return_data else None
        
    if not return_data:
        click.secho(f"✅ Encontrado(s) {len(initial_commits)} commit(s) na superfície. Iniciando viagem no tempo...\n", fg="green")
    master_timeline = []
    seen_hashes = set()
    
    # LOOP DE COLETA DE DADOS
    for base_commit in initial_commits:
        current_commit = base_commit
        depth = 0
        max_depth = 4 # Trava de segurança para não rodar infinito em código legado
        
        while depth < max_depth:
            # Se já analisamos este commit em outra trilha, não gasta requisição à toa
            if current_commit in seen_hashes:
                break
                
            seen_hashes.add(current_commit)
            info = get_commit_info(current_commit)
            ai_analysis = analyze_commit_with_ai(current_commit, file_path)
            
            status = str(ai_analysis.get("status", "ORIGEM")).upper()
            motivo = str(ai_analysis.get("motivo", ""))
            
            master_timeline.append({
                "hash": current_commit[:8],
                "info": info,
                "status": status,
                "motivo": motivo,
                "raw_date": info["date"] # Usado para ordenação
            })
            
            if status == "ORIGEM":
                break
                
            # É refatoração, vamos buscar o commit pai no passado
            depth += 1
            parent_hash = f"{current_commit}^"
            parent_commits = execute_git_blame(file_path, start_line, end_line, parent_hash)
            
            if not parent_commits:
                break
            current_commit = parent_commits[0]
            
    # ORDENAÇÃO CRONOLÓGICA (Do mais antigo para o mais novo)
    master_timeline.sort(key=lambda x: x["raw_date"])
    
    # Retorno Direto para a IA
    if return_data:
        return master_timeline
    
    # EXIBIÇÃO VISUAL NO TERMINAL (ÚNICA)
    click.secho(f"\n📜 Histórico Consolidado da Regra (Linhas {start_line}-{end_line}):", fg="magenta", bold=True)
    
    for item in master_timeline:
        cor = "green" if item["status"] == "ORIGEM" else "yellow"
        icone = "👶" if item["status"] == "ORIGEM" else "🔧"
        
        click.secho(f"\n[{item['info']['date']}] {icone} {item['status']}: Por {item['info']['author']} (Commit: {item['hash']})", fg=cor, bold=True)
        click.echo(f"   └─ Mensagem: \"{item['info']['message']}\"")
        if item["motivo"]:
            click.secho(f"   └─ Análise IA: {item['motivo']}", fg="cyan", dim=True)
            
    click.echo("\n" + "-"*60 + "\n")
    
    # GERAÇÃO DO RELATÓRIO MARKDOWN (ÚNICO)
    click.secho("📝 Gerando relatório Markdown unificado com o resumo da IA...", fg="cyan")
    
    branch_name = get_current_branch()
    safe_branch_name = branch_name.replace("/", "-").replace("\\", "-")
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    
    pattern = os.getenv("OUTPUT_FILE_NAME_BLAME", "{branch}_{datetime}_BLAME_REPORT.md")
    output_filename = pattern.format(branch=safe_branch_name, datetime=current_time)
    
    # Monta a Tabela Markdown
    md_content = f"# Linha do tempo da regra investigada\n\n"
    md_content += f"**Arquivo:** `{file_path}` (Linhas {start_line}-{end_line})\n\n"
    md_content += "| Data | Commit | Autor | O quê |\n"
    md_content += "|---|---|---|---|\n"
    
    for item in master_timeline:
        data_fmt = item['info']['date']
        hash_curto = item['hash']
        autor = item['info']['author']
        msg_commit = item['info']['message']
        
        # Pega a explicação da IA ou coloca um fallback seguro
        explicacao_ia = item['motivo'] if item['motivo'] else "Alteração identificada na regra"
        
        # Junta a explicação da IA com a mensagem do commit (Estilo Tabela de Referência)
        motivo_final = f"{explicacao_ia} — *\"{msg_commit}\"*"
        
        md_content += f"| {data_fmt} | `{hash_curto}` | {autor} | {motivo_final} |\n"        
    
    # IA gera o Resumo Analítico Final
    summary_prompt = "Baseado na seguinte linha do tempo de commits de uma regra de negócio, escreva um único parágrafo resumindo a idade da regra, o autor original, o número de refatorações e deduza qual era a intenção original de negócio (o motivo real da regra existir no sistema).\n\n"
    for item in master_timeline:
        summary_prompt += f"[{item['info']['date']}] {item['info']['author']} ({item['hash']}) - {item['status']}: {item['motivo']}\n"

    provider = get_ai_provider()
    api_key = get_api_key(provider)
    api_model = get_api_model(provider, task_complexity="advanced") 
    sys_inst = "Você é um Arquiteto de Software. Gere APENAS um objeto JSON no formato {\"resumo\": \"texto do resumo\"}."

    click.secho(f"  🤖 Consultando a IA ({api_model}) para o Resumo Executivo...", fg="cyan", dim=True)
    summary_json = call_ai_model(provider, api_key, api_model, summary_prompt, sys_inst)
    
    resumo_texto = summary_json.get("resumo", "Resumo não disponível.") if summary_json else "Resumo não disponível."
    
    md_content += f"\n**Resumo:** {resumo_texto}\n"
    
    # Salva no disco
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(md_content)
        click.secho(f"✅ Relatório unificado salvo com sucesso: '{output_filename}'", fg="green", bold=True)
    except Exception as e:
        click.secho(f"❌ Erro ao salvar o relatório: {e}", fg="red")