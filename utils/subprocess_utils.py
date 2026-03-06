#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MintyForge - Secure Subprocess Utilities
-----------------------------------------
Secure subprocess wrappers that avoid shell=True and command injection risks.
Provides safe alternatives for common system commands.
"""

import sys
import subprocess
from typing import List, Optional
from pathlib import Path


class CommandResult:
    """Result of a command execution."""
    def __init__(self, returncode: int, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.success = returncode == 0
    
    def __bool__(self):
        return self.success


def run_command(
    cmd: List[str],
    check: bool = False,
    capture_output: bool = False,
    cwd: Optional[Path] = None,
    timeout: Optional[int] = None,
    env: Optional[dict] = None
) -> CommandResult:
    """
    Execute a command safely without shell=True.
    
    Args:
        cmd: Command as list of strings (safe)
        check: Raise exception on non-zero exit
        capture_output: Capture stdout/stderr
        cwd: Working directory
        timeout: Command timeout in seconds
        env: Environment variables
    
    Returns:
        CommandResult object with returncode, stdout, stderr
    
    Example:
        result = run_command(["apt", "update"])
        if result.success:
            print("Success!")
    """
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=capture_output,
            text=True,
            cwd=str(cwd) if cwd else None,
            timeout=timeout,
            env=env
        )
        return CommandResult(
            result.returncode,
            result.stdout if capture_output else "",
            result.stderr if capture_output else ""
        )
    except subprocess.CalledProcessError as e:
        return CommandResult(e.returncode, e.stdout or "", e.stderr or "")
    except subprocess.TimeoutExpired:
        return CommandResult(-1, "", "Command timed out")
    except FileNotFoundError as e:
        return CommandResult(-1, "", f"Command not found: {e}")


def run_sudo_command(
    cmd: List[str],
    check: bool = False,
    capture_output: bool = False,
    timeout: Optional[int] = None
) -> CommandResult:
    """
    Execute a command with sudo safely.
    
    Args:
        cmd: Command as list (WITHOUT sudo prefix)
        check: Raise on error
        capture_output: Capture output
        timeout: Command timeout
    
    Returns:
        CommandResult object
    
    Example:
        result = run_sudo_command(["apt", "install", "-y", "curl"])
    """
    # Use sudo -n to avoid password prompt (fail if password needed)
    sudo_cmd = ["sudo", "-n"] + cmd
    return run_command(sudo_cmd, check=check, capture_output=capture_output, timeout=timeout)


def check_package_installed(package_name: str) -> bool:
    """
    Check if a Debian package is installed (safe alternative to dpkg | grep).
    
    Args:
        package_name: Package name to check
    
    Returns:
        True if installed, False otherwise
    
    Example:
        if check_package_installed("curl"):
            print("curl is installed")
    """
    result = run_command(
        ["dpkg-query", "-W", "-f=${Status}", package_name],
        capture_output=True
    )
    return "install ok installed" in result.stdout


def check_command_exists(command: str) -> bool:
    """
    Check if a command exists in PATH (safe alternative to command -v).
    
    Args:
        command: Command name to check
    
    Returns:
        True if command exists, False otherwise
    
    Example:
        if check_command_exists("python3"):
            print("Python 3 is available")
    """
    result = run_command(["which", command], capture_output=True)
    return result.success


def apt_install(packages: List[str], assume_yes: bool = True) -> CommandResult:
    """
    Install APT packages safely.
    
    Args:
        packages: List of package names
        assume_yes: Use -y flag
    
    Returns:
        CommandResult object
    
    Example:
        result = apt_install(["curl", "wget", "git"])
    """
    cmd = ["apt", "install"]
    if assume_yes:
        cmd.append("-y")
    cmd.extend(packages)
    
    return run_sudo_command(cmd)


def apt_remove(packages: List[str], purge: bool = False, assume_yes: bool = True) -> CommandResult:
    """
    Remove APT packages safely.
    
    Args:
        packages: List of package names
        purge: Use purge instead of remove
        assume_yes: Use -y flag
    
    Returns:
        CommandResult object
    
    Example:
        result = apt_remove(["firefox"], purge=True)
    """
    cmd = ["apt", "purge" if purge else "remove"]
    if assume_yes:
        cmd.append("-y")
    cmd.extend(packages)
    
    return run_sudo_command(cmd)


def apt_update() -> CommandResult:
    """Update APT package lists safely."""
    return run_sudo_command(["apt", "update"])


def apt_upgrade(assume_yes: bool = True) -> CommandResult:
    """Upgrade APT packages safely."""
    cmd = ["apt", "upgrade"]
    if assume_yes:
        cmd.append("-y")
    return run_sudo_command(cmd)


def flatpak_install(app_id: str, remote: str = "flathub", assume_yes: bool = True) -> CommandResult:
    """
    Install a Flatpak application safely.
    
    Args:
        app_id: Flatpak application ID
        remote: Flatpak remote (default: flathub)
        assume_yes: Use -y flag
    
    Returns:
        CommandResult object
    
    Example:
        result = flatpak_install("org.mozilla.firefox")
    """
    cmd = ["flatpak", "install"]
    if assume_yes:
        cmd.append("-y")
    cmd.extend([remote, app_id])
    
    return run_command(cmd)


def flatpak_list() -> List[str]:
    """
    List installed Flatpak applications.
    
    Returns:
        List of installed app IDs
    
    Example:
        apps = flatpak_list()
    """
    result = run_command(["flatpak", "list", "--app", "--columns=application"], capture_output=True)
    if result.success:
        return [line.strip() for line in result.stdout.split('\n') if line.strip()]
    return []


def check_flatpak_installed(app_id: str) -> bool:
    """
    Check if a Flatpak application is installed.
    Uses 'flatpak info' for O(1) lookup instead of listing all apps.

    Args:
        app_id: Flatpak application ID

    Returns:
        True if installed, False otherwise
    """
    result = run_command(["flatpak", "info", app_id], capture_output=True)
    return result.success


def git_clone(repo_url: str, target_dir: Path, depth: Optional[int] = None) -> CommandResult:
    """
    Clone a git repository safely.
    
    Args:
        repo_url: Git repository URL
        target_dir: Target directory
        depth: Clone depth (shallow clone)
    
    Returns:
        CommandResult object
    
    Example:
        result = git_clone("https://github.com/user/repo.git", Path("./repo"))
    """
    cmd = ["git", "clone"]
    if depth:
        cmd.extend(["--depth", str(depth)])
    cmd.extend([repo_url, str(target_dir)])
    
    return run_command(cmd)


def run_bash_script(script_path: Path, args: Optional[List[str]] = None, cwd: Optional[Path] = None) -> CommandResult:
    """
    Execute a bash script safely.
    
    Args:
        script_path: Path to the script
        args: Script arguments
        cwd: Working directory
    
    Returns:
        CommandResult object
    
    Example:
        result = run_bash_script(Path("install.sh"), ["--help"])
    """
    cmd = ["bash", str(script_path)]
    if args:
        cmd.extend(args)
    
    return run_command(cmd, cwd=cwd)


def run_python_script(script_path: Path, args: Optional[List[str]] = None, cwd: Optional[Path] = None) -> CommandResult:
    """
    Execute a Python script safely.
    
    Args:
        script_path: Path to the script
        args: Script arguments
        cwd: Working directory
    
    Returns:
        CommandResult object
    
    Example:
        result = run_python_script(Path("setup.py"), ["install"])
    """
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    return run_command(cmd, cwd=cwd)
