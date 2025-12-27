import subprocess
from pathlib import Path
from typing import List, Optional
from apex_flow.logger import logger
import git

class FeatureControl:
    """
    Wrapper for DVC and Git operations.
    """
    
    @staticmethod
    def dvc_add(path: Path):
        try:
            logger.info("dvc_adding", path=str(path))
            subprocess.run(["dvc", "add", str(path)], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error("dvc_add_failed", error=e.stderr.decode())
            return False

    @staticmethod
    def get_dvc_hash(path: Path) -> Optional[str]:
        dvc_file = path.parent / (path.name + ".dvc")
        if not dvc_file.exists():
            return None
        
        # Parse simple yaml manually or use dvc api (lighter to just parse)
        import yaml
        with open(dvc_file, 'r') as f:
            data = yaml.safe_load(f)
            # DVC schema structure: outs: - md5: ...
            return data.get('outs', [{}])[0].get('md5')

    @staticmethod
    def git_commit_dvc(dvc_file_path: Path, message: str):
        try:
            repo = git.Repo(search_parent_directories=True)
            repo.index.add([str(dvc_file_path)])
            repo.index.commit(message)
            return repo.head.commit.hexsha
        except Exception as e:
            logger.error("git_commit_failed", error=str(e))
            return None

    @staticmethod
    def dvc_push():
        subprocess.run(["dvc", "push"], check=False) # Remote might not be set in dev

    @staticmethod
    def checkout_version(dvc_hash: str, path: Path):
        """
        Rollback specific file to a version hash using dvc checkout.
        This is tricky on file level without git context, but dvc cache has it.
        Command: dvc checkout
        """
        # Usually we checkout by git commit, then dvc checkout.
        pass

vc = FeatureControl()
