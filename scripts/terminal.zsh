# Source from ~/.zshrc. Resolve this file rather than depending on the terminal's cwd.
typeset -g SW_AGENTS_PANEL_ROOT="${${(%):-%N}:A:h:h}"

codex() {
  # Keep CLI help and automation usable without opening a browser.
  case "${1-}" in
    --help|-h|--version|-V|help|exec|e|login|logout|app-server|completion|features|debug)
      command codex "$@"
      return $?
      ;;
  esac
  python3 "$SW_AGENTS_PANEL_ROOT/scripts/dashboard.py" -- "$@" || true
  command codex "$@"
}
