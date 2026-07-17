import os
import json
import hashlib
import random
import string
from datetime import datetime
from pathlib import Path

def gerar_uuid_base_15():
    """
    Generate a UUID with a base of 15 characters (group 4-5-4)

    Returns:
        str: UUID in the format XXXX-XXXXX-XXXX
    """
    
    def gerar_grupo(tamanho):
        """
        Helper function to generate a group of characters with at least one number

        Args:
            tamanho (int): Size of the group to be generated

        Returns:
            str: Group of characters with at least one number
        """
        letras = string.ascii_letters  # 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        numeros = string.digits        # '0123456789'
        todos_caracteres = letras + numeros
        
        # Ensures that at least one number will be present in the group
        grupo = []
        numero_inserido = False
        
        for i in range(tamanho):
            if i == tamanho - 1 and not numero_inserido:
                # If it is the last character and we have not inserted a number yet
                grupo.append(random.choice(numeros))
            else:
                caractere = random.choice(todos_caracteres)
                if caractere.isdigit():
                    numero_inserido = True
                grupo.append(caractere)
        
        return ''.join(grupo)
    
    # Generate the three groups of characters
    grupo1 = gerar_grupo(4)
    grupo2 = gerar_grupo(5)
    grupo3 = gerar_grupo(4)
    
    # Combine the groups into the desired format
    return f"{grupo1}-{grupo2}-{grupo3}"

class ChatMemoryManager:
    """
    State and Memory Manager for GitPR's Hybrid Chat sessions.
    Keeps the message history and tracks code changes (diff) during the session.
    """
    def __init__(self, repo_name, branch_name, current_diff, git_user, git_email):
        self.repo_name = repo_name
        self.branch_name = branch_name
        self.git_user = git_user
        self.git_email = git_email
        
        self.base_dir = Path.home() / ".gitpr" / "cache" / "chat"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.session_uuid = None
        self.session_dir = None
        self.config_file = None
        self.conversation_file = None
        
        self._initialize_session(current_diff)

    def _generate_md5(self, text):
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def _initialize_session(self, current_diff):
        """Look for an open session for the current branch or create a new one."""
        diff_md5 = self._generate_md5(current_diff)
        latest_session = None
        latest_time = None

        # Look for the most recent session for this repository and branch
        for session_folder in self.base_dir.iterdir():
            if session_folder.is_dir():
                uuid_str = session_folder.name
                cfg_path = session_folder / f"chat-config_{uuid_str}.json"
                
                if cfg_path.exists():
                    try:
                        with open(cfg_path, "r", encoding="utf-8") as f:
                            cfg = json.load(f)
                            
                        if cfg.get("repo") == self.repo_name and cfg.get("branch") == self.branch_name:
                            # Compare the modification time to pick the most recent chat for this branch
                            mtime = cfg_path.stat().st_mtime
                            if latest_time is None or mtime > latest_time:
                                latest_time = mtime
                                latest_session = (uuid_str, session_folder, cfg_path, cfg)
                    except Exception:
                        continue

        if latest_session:
            # Reopen the existing session
            self.session_uuid, self.session_dir, self.config_file, cfg_data = latest_session
            self.conversation_file = self.session_dir / f"conversation_{self.session_uuid}.json"
            
            # Check whether the code (diff) has changed since last time
            diff_history = cfg_data.get("diff_history", [])
            last_diff_md5 = diff_history[-1]["md5"] if diff_history else None
            
            if last_diff_md5 != diff_md5:
                self._append_diff_to_history(cfg_data, current_diff, diff_md5)
        else:
            # No session found for this branch, create a new one from scratch
            self._create_new_session(current_diff, diff_md5)

    def _append_diff_to_history(self, cfg_data, diff_text, diff_md5):
        """Store the new diff in the configuration file."""
        new_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "md5": diff_md5,
            "diff": diff_text
        }
        cfg_data.setdefault("diff_history", []).append(new_entry)
        
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(cfg_data, f, indent=2, ensure_ascii=False)

    def _create_new_session(self, current_diff, diff_md5):
        """Set up a new base-15 UUID folder with the initial JSON files."""
        self.session_uuid = gerar_uuid_base_15()
        self.session_dir = self.base_dir / self.session_uuid
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.session_dir / f"chat-config_{self.session_uuid}.json"
        self.conversation_file = self.session_dir / f"conversation_{self.session_uuid}.json"
        
        initial_config = {
            "session_uuid": self.session_uuid,
            "folder_name": self.session_uuid,
            "repo": self.repo_name,
            "branch": self.branch_name,
            "git_user": self.git_user,
            "git_email": self.git_email,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "diff_history": [
                {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "md5": diff_md5,
                    "diff": current_diff
                }
            ]
        }
        
        # Write the metadata
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(initial_config, f, indent=2, ensure_ascii=False)
            
        # Create the empty chat memory
        with open(self.conversation_file, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)

    def get_history(self):
        """Return the conversation history from the JSON file."""
        if self.conversation_file.exists():
            try:
                with open(self.conversation_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_message(self, role, content):
        """
        Save a new message to the conversation.
        'role' must be 'user', 'assistant' or 'system'.
        """
        history = self.get_history()
        history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        with open(self.conversation_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
            
    def get_latest_diff(self):
        """Retrieve the most recent current diff from the session configuration."""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            return cfg.get("diff_history", [])[-1]["diff"]
        except Exception:
            return ""

    def update_diff_if_changed(self, new_diff):
        """
        Silently check whether the code has changed.
        Used by the F2 key to update the chat context in real time.
        Returns True if the diff was updated, False otherwise.
        """
        new_md5 = self._generate_md5(new_diff)
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                
            diff_history = cfg.get("diff_history", [])
            last_diff_md5 = diff_history[-1]["md5"] if diff_history else None
            
            if last_diff_md5 != new_md5:
                self._append_diff_to_history(cfg, new_diff, new_md5)
                return True
            return False
        except Exception:
            return False