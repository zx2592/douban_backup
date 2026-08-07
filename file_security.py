import getpass
import os
import subprocess


def restrict_file_permissions(path):
    try:
        if os.name == "nt":
            user = getpass.getuser()
            subprocess.run(
                ["icacls", path, "/inheritance:r"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                ["icacls", path, "/grant:r", f"{user}:(R,W)"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True

        os.chmod(path, 0o600)
        return True
    except (OSError, subprocess.SubprocessError):
        return False
