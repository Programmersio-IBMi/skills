@echo off
REM Windows wrapper: invokes the named hook script under Git Bash or WSL.
REM Used when Claude Code / Cursor / Copilot CLI cannot launch a POSIX
REM script directly because Windows path expansion would break the
REM ${CLAUDE_PLUGIN_ROOT} substitution.
REM
REM Usage:  run-hook.cmd <hook-name>
REM Example: run-hook.cmd session-start

SETLOCAL

SET "HOOK_DIR=%~dp0"
SET "HOOK_NAME=%~1"

IF "%HOOK_NAME%"=="" (
  ECHO Usage: %~nx0 ^<hook-name^> 1>&2
  EXIT /B 2
)

SET "SCRIPT=%HOOK_DIR%%HOOK_NAME%"

IF NOT EXIST "%SCRIPT%" (
  ECHO Error: hook script not found: %SCRIPT% 1>&2
  EXIT /B 2
)

REM Prefer Git Bash if installed on PATH.
WHERE bash >NUL 2>&1
IF %ERRORLEVEL%==0 (
  bash "%SCRIPT%"
  EXIT /B %ERRORLEVEL%
)

REM Fall back to WSL.
WHERE wsl >NUL 2>&1
IF %ERRORLEVEL%==0 (
  FOR /F "usebackq delims=" %%i IN (`wsl wslpath -u "%SCRIPT%"`) DO SET "WSL_SCRIPT=%%i"
  wsl bash "%WSL_SCRIPT%"
  EXIT /B %ERRORLEVEL%
)

ECHO Error: neither Git Bash nor WSL is available on PATH. 1>&2
ECHO Install Git for Windows (https://git-scm.com/) or enable WSL. 1>&2
EXIT /B 1
