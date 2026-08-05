
Analisando os arquivos, vamos importar nossa nova função e disparar os eventos de forma assíncrona ao final de cada execução de sucesso, registrando a quantidade de alertas do linter e o volume de commits investigados pelo blame. Aplique as alterações cirúrgicas abaixo e me avise se podemos avançar para a **Fase 3** (Git Hooks). 🚀

**1. No arquivo `src/linter_engine.py`, adicione o import e os disparos:**

```python
# Localize o bloco de importações no topo do arquivo:
# DE:
from src.config import load_linter_rules
from src.i18n import __

# PARA:
from src.config import load_linter_rules
from src.i18n import __
from src.metrics import log_local_metric

```

```python
# Localize o final do bloco "FULL FILE MODE (--input)" na função parse_diff_and_lint:
# DE:
                if not _is_rule_applicable(rule, current_file, file_extension):
                    continue
                _apply_rule(rule, code_line, i, current_file, alerts)

        return alerts

    # ==========================================

# PARA:
                if not _is_rule_applicable(rule, current_file, file_extension):
                    continue
                _apply_rule(rule, code_line, i, current_file, alerts)

        log_local_metric(command="linter", status="success", linter_errors=len(alerts["errors"]), linter_warnings=len(alerts["warnings"]), mode="full_file")
        return alerts

    # ==========================================

```

```python
# Localize o final da função parse_diff_and_lint (bloco STANDARD GIT DIFF MODE):
# DE:
            for rule in rules:
                if not _is_rule_applicable(rule, current_file, file_extension):
                    continue
                _apply_rule(rule, code_line, line_number, current_file, alerts)

    return alerts

# PARA:
            for rule in rules:
                if not _is_rule_applicable(rule, current_file, file_extension):
                    continue
                _apply_rule(rule, code_line, line_number, current_file, alerts)

    log_local_metric(command="linter", status="success", linter_errors=len(alerts["errors"]), linter_warnings=len(alerts["warnings"]), mode="diff")
    return alerts

```

**2. No arquivo `src/blame_engine.py`, adicione o import e os disparos:**

```python
# Localize o bloco de importações no topo do arquivo:
# DE:
from src.config import get_api_key, get_api_model, get_ai_provider, resolve_skill_path
from src.ai_providers import call_ai_model
from src.i18n import __

# PARA:
from src.config import get_api_key, get_api_model, get_ai_provider, resolve_skill_path
from src.ai_providers import call_ai_model
from src.i18n import __
from src.metrics import log_local_metric

```

```python
# Localize a verificação de retorno direto (Return to AI) na função run_blame_analysis:
# DE:
    # Direct Return to AI
    if return_data:
        return master_timeline

    # VISUAL DISPLAY IN TERMINAL (SINGLE)

# PARA:
    # Direct Return to AI
    if return_data:
        log_local_metric(command="blame", status="success", commits_analyzed=len(master_timeline), mode="return_data")
        return master_timeline

    # VISUAL DISPLAY IN TERMINAL (SINGLE)

```

```python
# Localize o final da função run_blame_analysis (bloco Save to disk):
# DE:
    # Save to disk
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(md_content)
        click.secho(__("✅ Unified report successfully saved: '{output_filename}'", output_filename=output_filename), fg="green", bold=True)
    except Exception as e:
        click.secho(__("❌ Error saving report: {error}", error=str(e)), fg="red")

# PARA:
    # Save to disk
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(md_content)
        click.secho(__("✅ Unified report successfully saved: '{output_filename}'", output_filename=output_filename), fg="green", bold=True)
        log_local_metric(command="blame", status="success", commits_analyzed=len(master_timeline), mode="report_generated")
    except Exception as e:
        click.secho(__("❌ Error saving report: {error}", error=str(e)), fg="red")
        log_local_metric(command="blame", status="error", error_message=str(e))

```

Implementado isso, teremos finalizado a Fase 2! 