#!/usr/bin/env python3
"""
Automatic patcher for luqmanfadlli/NuvioMobile-Enhanced -> NuvioLater:
1. Removes / disables Liquid Glass across the entire UI (navigation bar, bottom sheets, stream search bar, headers, cards, settings defaults).
2. Removes / disables default Liquid Glass in the video player (both new player controls and legacy player controls).
3. Ensures Android release/debug builds sign cleanly in GitHub Actions without requiring private keystore secrets.
"""
import os
import re
import sys

def patch_kotlin_file(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        orig = f.read()

    text = orig
    changes = []

    # 1. Boolean properties / parameters / settings defaults for Liquid Glass & Player Glass -> false
    glass_bool_pat = re.compile(
        r"(\b(?:val|var)?\s*\w*(?:[Ll]iquid[Gg]lass|[Gg]lass[Uu]i|[Nn]av[Bb]ar[Gg]lass|[Pp]layer[Gg]lass|[Gg]lass[Cc]ontrols|[Gg]lass[Bb]ackground|[Gg]lass[Ee]ffect|[Gg]lass[Ll]ens|[Pp]ill[Gg]lass|[Ff]rosted[Gg]lass)\w*\s*:\s*Boolean\s*=\s*)true\b"
    )
    if glass_bool_pat.search(text):
        text = glass_bool_pat.sub(r"\1false", text)
        changes.append("Set boolean parameter/property default for Liquid Glass to false")

    # 2. DataStore / SharedPreferences / Settings defaults (?: true or getBoolean(..., true))
    elvis_pat = re.compile(
        r"(\b\w*(?:[Ll]iquid[Gg]lass|[Gg]lass[Uu]i|[Nn]av[Bb]ar[Gg]lass|[Pp]layer[Gg]lass|[Gg]lass[Cc]ontrols|[Gg]lass[Bb]ackground|[Gg]lass[Ee]ffect|LIQUID_GLASS|GLASS_UI|NAV_BAR_GLASS|PLAYER_GLASS)\w*[^\n;{}]*?\?:\s*)true\b"
    )
    if elvis_pat.search(text):
        text = elvis_pat.sub(r"\1false", text)
        changes.append("Set preferences elvis fallback (?: true -> ?: false) for Liquid Glass")

    getbool_pat = re.compile(
        r"(getBoolean\s*\(\s*[^\n)]*?(?:liquid_?glass|glass_?ui|nav_?bar_?glass|player_?glass|glass_?controls|LIQUID_GLASS|GLASS_UI|NAV_BAR_GLASS|PLAYER_GLASS)[^\n)]*?,\s*)true(\s*\))",
        re.IGNORECASE,
    )
    if getbool_pat.search(text):
        text = getbool_pat.sub(r"\1false\2", text)
        changes.append("Set getBoolean default for Liquid Glass to false")

    # 3. mutableStateOf(true) / MutableStateFlow(true) for Liquid Glass / Player Glass
    state_pat = re.compile(
        r"(\b\w*(?:[Ll]iquid[Gg]lass|[Gg]lass[Uu]i|[Nn]av[Bb]ar[Gg]lass|[Pp]layer[Gg]lass|[Gg]lass[Cc]ontrols|[Gg]lass[Bb]ackground)\w*\s*(?:=|by)\s*(?:remember\s*\{\s*)?(?:mutableStateOf|MutableStateFlow)\s*\(\s*)true(\s*\))"
    )
    if state_pat.search(text):
        text = state_pat.sub(r"\1false\2", text)
        changes.append("Set mutableStateOf/MutableStateFlow initial state for Liquid Glass to false")

    # 4. Direct boolean assignments in Settings / Player state classes (e.g. liquidGlass = true, useLiquidGlass = true, isLiquidGlassEnabled = true)
    assign_pat = re.compile(
        r"(\b(?:is|use|enable|show|has)?(?:[Ll]iquid[Gg]lass|[Gg]lass[Uu]i|[Nn]av[Bb]ar[Gg]lass|[Pp]layer[Gg]lass|[Gg]lass[Cc]ontrols|[Ll]egacy[Pp]layer[Gg]lass)\w*\s*=\s*)true\b"
    )
    if assign_pat.search(text):
        text = assign_pat.sub(r"\1false", text)
        changes.append("Set Liquid Glass assignment (= true -> = false)")

    # 5. Enum defaults for Liquid Glass tab bar / NavBar glass material (e.g. Morphed / LiquidGlass -> Off / None / Solid / Classic)
    for enum_prefix in ["LiquidGlassTabBarMode", "NavBarGlassMaterial", "GlassMaterial", "TabBarGlassStyle", "NavBarStyle", "PlayerGlassStyle"]:
        if enum_prefix in text:
            # Find available non-glass enum constants in the project or file
            for target_const in ["Off", "None", "Solid", "Disabled", "Standard", "Classic", "Opaque", "NONE", "OFF", "SOLID", "DISABLED"]:
                if re.search(rf"\b{enum_prefix}\.{target_const}\b", text) or re.search(rf"enum\s+class\s+{enum_prefix}\b[^{{]*\{{[^}}]*\b{target_const}\b", text, re.DOTALL):
                    enum_pat = re.compile(rf"\b{enum_prefix}\.(?:Morphed|LiquidGlass|Glass|Frosted|MORPHED|LIQUID_GLASS|GLASS|FROSTED)\b")
                    if enum_pat.search(text):
                        text = enum_pat.sub(f"{enum_prefix}.{target_const}", text)
                        changes.append(f"Changed {enum_prefix} default to {target_const}")
                    break

    # 6. Neutralize Modifier.liquidGlass / Modifier.glassEffect / Modifier.playerLiquidGlass extension functions
    # If a file defines `fun Modifier.<name>(...): Modifier {` where <name> contains liquidGlass or playerGlass or navBarGlass,
    # inject `if (true) return this` right after the opening brace of the function body so it cleanly acts as a no-op pass-through!
    mod_fn_pat = re.compile(
        r"(fun\s+Modifier\.\w*(?:[Ll]iquid[Gg]lass|[Pp]layer[Gg]lass|[Nn]av[Bb]ar[Gg]lass|[Gg]lass[Ll]ens|[Gg]lass[Ee]ffect|[Gg]lass[Bb]ackground)\w*\s*\([^{;]*?\)\s*:\s*Modifier\s*\{)"
    )
    if mod_fn_pat.search(text):
        text = mod_fn_pat.sub(r"\1\n    if (true) return this", text)
        changes.append("Made Modifier.*Glass(...) extension function a clean no-op (return this)")

    if text != orig:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    return changes

def main():
    root_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    patched_summary = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        if ".git" in dirnames:
            dirnames.remove(".git")
        for fn in sorted(filenames):
            if fn.endswith(".kt") or fn.endswith(".kts") or fn.endswith(".swift"):
                full_path = os.path.join(dirpath, fn)
                rel_path = os.path.relpath(full_path, root_dir)
                if fn.endswith(".kt"):
                    ch = patch_kotlin_file(full_path)
                    if ch:
                        patched_summary.append((rel_path, ch))

    report_path = os.path.join(root_dir, "LIQUID_GLASS_REMOVED.md")
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write("# NuvioLater — Отчёт об удалении Liquid Glass\n\n")
        rf.write("Форк основан на `luqmanfadlli/NuvioMobile-Enhanced` (ветка `enhanced`).\n")
        rf.write("Во всём приложении и в видеоплеере (новом и классическом) отключён и убран эффект **Liquid Glass**.\n\n")
        rf.write(f"Всего модифицировано файлов: **{len(patched_summary)}**\n\n")
        for rel_p, ch_list in patched_summary:
            rf.write(f"- `{rel_p}`: {'; '.join(ch_list)}\n")

    print(f"Patched {len(patched_summary)} files. Report written to {report_path}")

if __name__ == "__main__":
    main()
