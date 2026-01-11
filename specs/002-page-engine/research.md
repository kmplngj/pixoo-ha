# Research — 002-page-engine (Pixoo Page Engine)

**Date**: 2026-01-01  
**Sources**:
- DeepWiki: `home-assistant/core` (scheduler patterns, templating, services, image safety, icons)
- Project constitution: `.specify/memory/constitution.md`

## Entscheidungen

### Decision 1: Rotation als ConfigEntry-gebundener Hintergrundjob

**Chosen**: Rotation wird als **Background Task** an den ConfigEntry gebunden und beim Unload sauber beendet.

**Rationale** (HA Best Practice):
- Für long-running/background Prozesse empfiehlt HA die Nutzung von `ConfigEntry.async_create_background_task()` (Tasks werden beim Unload automatisch gecancelt).
- Für periodische Ausführung ist `async_track_time_interval()` üblich; der Unsubscribe wird via `entry.async_on_unload()` registriert.
- Für dynamisches Rescheduling (z. B. pro-Page duration) ist auch `async_call_later()` mit manueller Cancellation ein Pattern (Bond/MotionBlinds Pattern).

**Alternative considered**:
- DataUpdateCoordinator: passt schlecht, weil Rotation keine „Datenquelle“ ist, sondern **Aktions-Scheduler** (Display Rendering). Coordinator wäre möglich, aber erhöht Kopplung und kann semantisch verwirrend sein.

**Implication**:
- Rotation State/Timer leben außerhalb von Entities (oder optional in einem Switch/Status-Sensor exponiert), aber sind lifecycle-sicher.

---

### Decision 2: Templating über `Template` / `async_render` + `render_complex`

**Chosen**: Page-Definitionen (oder Teile davon) können Jinja2-Templates enthalten; Rendering erfolgt **async und sicher** mit Home Assistant `Template`-API.

**Rationale** (HA Best Practice):
- HA nutzt `homeassistant.helpers.template.Template` und `async_render()` für sichere, event-loop kompatible Template-Auswertung.
- Für verschachtelte Strukturen (dict/list) ist `render_complex` das etablierte Pattern.
- Fehler werden als `TemplateError` behandelt und sollen nachvollziehbar geloggt/als Service-Fehler reportet werden.

**Alternative considered**:
- Eigenes Jinja setup / direkte Jinja2 Nutzung: nicht HA-native, mehr Risiko, schlechtere Integrationen in HA Context.

**Implication**:
- Templating fühlt sich für Nutzer „HA-typisch“ an (Zugriff auf `states()`, `is_state`, etc.).

---

### Decision 3: Service-Design mit voluptuous Schema + HA Targeting

**Chosen**: Page Engine wird primär über **HA Services** exponiert (z. B. `pixoo.render_page`, `pixoo.show_message`, Rotation start/stop). Inputs werden per voluptuous validiert.

**Rationale** (HA Best Practice):
- Services werden mit `voluptuous`/`config_validation` validiert.
- Entity/Device targeting läuft über HA Target-Mechanismus (`entity_id`, `device_id`, `area_id`, …).
- Fehler: 
  - `ServiceValidationError` für falsche Inputs
  - `HomeAssistantError` für Geräte-/I/O-Probleme

**Alternative considered**:
- Alles als Entities abbilden (z. B. „Current Page“ Sensor): UI/State nice, aber führt zu „UI noise“ und ist nicht zwingend nötig.

**Implication**:
- Services lassen sich leicht in Automations/Scripts nutzen und bleiben HA-native.

---

### Decision 4: Safe Image Fetching (Timeout, Size, Content-Type, allowlist)

**Chosen**: Externe Bilder werden nur mit Schutzmaßnahmen geladen:
- Timeout (z. B. 10–30s)
- Max-Size Limit (z. B. 10MB)
- Content-Type Validierung (`image/*` oder `application/octet-stream`)
- Allowlisting (konfigurierbar):
  - Default **strict**: `hass.config.is_allowed_external_url(url)` / `hass.config.is_allowed_path(path)` MUSS erfüllt sein
  - Optional **permissive**: Allowlisting kann deaktiviert werden (Timeout/Size/Content-Type Checks bleiben aktiv)

**Rationale** (HA Best Practice):
- Integrationen sollen Timeouts/Size-Limits und Content-Type checks implementieren.
- Für lokale Pfade: `hass.config.is_allowed_path(path)`.

**Alternative considered**:
- Unbounded download (wie viele einfache Beispiele): Risiko für Memory/DoS und schlechte UX.

---

### Decision 4a: Colors als Helper `render_color()` / `parse_color()` (inkl. Template-Support)

**Chosen**: Farben werden über einen zentralen Helper gerendert/geparst, damit Services und Renderer konsistent bleiben:
- Eingaben: RGB list/tuple, Hex `#RRGGBB`, optional CSS4-Name (z. B. `forestgreen`), optional Template-String
- Rendering: Template → string/tuple → Parse → `(r,g,b)` clamp 0–255

**Rationale**:
- `pixoo-homeassistant` unterstützt CSS4-Namen; das ist ein einfacher UX-Gewinn.
- Ein zentraler Helper reduziert Fehlerquellen (einmalig validieren/templaten statt überall).

**Alternative considered**:
- Farben nur als `[r,g,b]` akzeptieren: minimal, aber schlechtere UX/Kompatibilität.

---

### Decision 5: Icons — kein Core-Pattern für Bitmap-Rendering aus `mdi:*`

**Chosen**: Für Page Engine behandeln wir Icons primär als:
- Bildquellen (URL/Path/Base64/Asset-Name), nicht als `mdi:*` → Bitmap.

**Rationale** (HA Best Practice):
- HA Integrationen definieren Icons als `mdi:*` in `icons.json` für Frontend/UI.
- Core bietet kein Standard-Pattern, um `mdi:*` in Bitmap zu konvertieren (Frontend rendert die Icons).

**Alternative considered**:
- Eigene MDI-zu-PNG Pipeline (zusätzliche Dependencies/Netzabrufe/Komplexität).

**Implication**:
- "Native" heißt: Templates/Entities/Services fühlen sich HA-native an; Pixoo bekommt Icons als Bilder (Assets oder URLs).

---

### Decision 6: Wo liegen Page-Definitionen? (NEEDS CLARIFICATION → resolved)

**Chosen**: Hybrid:
- Rotation/Enable/Scan-Config: OptionsFlow/ConfigEntry Options
- Pages selbst: 
  - **für Automations**: direkt im Service Call (ad-hoc)
  - **für Rotation**: in Options als Liste von „Page References“ (Template-Name oder inline minimal), plus optionaler Pfad zu einer YAML-Datei für Power-User

**Rationale**:
- HA Options UI ist für große, verschachtelte Strukturen unhandlich.
- Eine YAML-Datei in `/config/` ist für Power-User editierbar und versionierbar.

**Alternative considered**:
- Alles in Options speichern: schnell, aber UI/UX leidet.
- Eigener UI Editor: großer Aufwand, nicht nötig für MVP.

---

## Mögliche Ergänzungen an `pixooasync` (optional)

Aktuell **keine zwingenden Änderungen** nötig: Drawing Primitives, Text, Image und Buffer Workflow sind vorhanden.

Optionale Verbesserungen (nur wenn in Integration sinnvoll/benötigt):
- Helper: Bild-Resize/Conversion in eine „Pixoo-ready“ Byteform (wenn wiederholt benötigt) → könnte in `pixooasync` zentralisiert werden.
- Robustere Response-Parsing/Fehlercodes für Firmware-inkonsistente Antworten (bereits bekannte Device-Issues bei Animations-APIs).

## Risiken & Mitigations

- **Template Errors**: klar als ServiceValidationError/TemplateError reporten; optional „strict“ rendering.
- **Rotation Spam**: Rate limiting / Queue nutzen; per Page duration nicht unter Minimum (z. B. 1s).
- **Asset Fetch**: enforce timeouts + size limits; failures dürfen Rotation nicht dauerhaft stoppen.

