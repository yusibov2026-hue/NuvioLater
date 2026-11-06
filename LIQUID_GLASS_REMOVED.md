# NuvioLater — Отчёт об удалении Liquid Glass

Форк основан на `luqmanfadlli/NuvioMobile-Enhanced` (ветка `enhanced`).
Во всём приложении и в видеоплеере (новом и классическом) отключён и убран эффект **Liquid Glass**.

Всего модифицировано файлов: **4**

- `composeApp/src/commonMain/kotlin/com/nuvio/app/features/settings/ThemeSettingsRepository.kt`: Set preferences elvis fallback (?: true -> ?: false) for Liquid Glass; Set mutableStateOf/MutableStateFlow initial state for Liquid Glass to false
- `composeApp/src/commonMain/kotlin/com/nuvio/app/features/player/PlayerLiquidGlass.kt`: Made Modifier.*Glass(...) extension function a clean no-op (return this)
- `composeApp/src/commonMain/kotlin/com/nuvio/app/core/ui/glass/LiquidGlass.kt`: Set preferences elvis fallback (?: true -> ?: false) for Liquid Glass; Made Modifier.*Glass(...) extension function a clean no-op (return this)
- `composeApp/src/androidHostTest/kotlin/com/nuvio/app/features/settings/SettingsPagesTest.kt`: Set Liquid Glass assignment (= true -> = false)
