import { invoke } from "@tauri-apps/api/core";

interface ScriptResult {
  stdout: string;
  stderr: string;
  exit_code: number;
}

export function useScriptExec() {
  const executePython = (scriptPath: string, args: string[] = []) =>
    invoke<ScriptResult>("script_execute_python", { scriptPath, args });

  const executeBat = (scriptPath: string, args: string[] = []) =>
    invoke<ScriptResult>("script_execute_bat", { scriptPath, args });

  const executePowershell = (scriptPath: string, args: string[] = []) =>
    invoke<ScriptResult>("script_execute_powershell", { scriptPath, args });

  const executeShell = (command: string) =>
    invoke<ScriptResult>("script_execute_shell", { command });

  return { executePython, executeBat, executePowershell, executeShell };
}
