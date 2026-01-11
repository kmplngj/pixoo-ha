# Service Contracts — 002-page-engine

> Format: HA Service Vertrag (Schema + Semantik). Kein REST/OpenAPI, weil Home Assistant Services nicht HTTP-Endpoints sind.

## 1) `pixoo.render_page`

### Purpose
Rendert eine Page ad-hoc auf ein oder mehrere Pixoo Geräte.

### Targeting
- `target.entity_id`: eine oder mehrere Pixoo Entities (empfohlen: die zentrale Pixoo Light Entity pro Gerät)

### Schema (konzeptionell)

| Feld | Typ | Pflicht | Beschreibung |
|---|---:|:---:|---|
| `target` | HA target | ✅ | Ziel-Entities/Devices |
| `page` | object | ✅ | Page Definition (siehe Data Model) |
| `variables` | object | ❌ | Zusätzliche Variablen für Templates |
| `duration_override` | int | ❌ | Optional: überschreibt `page.duration` für diesen Render |

### Semantik
- Der Service validiert die Page.
- Templates werden gegen HA Context gerendert.
- Die Page wird auf dem Gerät angezeigt.

Zusätzliche Verhaltensgarantien (aus Spec Clarifications):
- **Multi-Device Targeting**: best-effort. Alle Targets werden unabhängig versucht. Der ServiceCall gilt nur dann als Fehler, wenn **alle** Targets fehlschlagen; pro-Device Fehler werden geloggt.
- **Per-Component Rendering**: best-effort. Wenn einzelne Komponenten fehlschlagen (z. B. Bild 404), werden andere Komponenten weiter gerendert. Der ServiceCall gilt nur dann als Fehler, wenn **keine** Komponente erfolgreich gerendert werden konnte.
- **Out-of-bounds nach Templating**: skip+log. Komponenten mit ungültigen Koordinaten/Größen werden übersprungen und geloggt; andere Komponenten werden weiter gerendert.
- **Allowlisting**: Default **strict** für `image.source.url/path` (HA allowlisting muss erfüllt sein). Optional kann ein **permissive** Modus erlaubt werden (Timeout/Size/Content-Type Checks bleiben aktiv).

### Errors
- `ServiceValidationError`: ungültige Page, ungültige Colors, ungültige Targets
- `TemplateError` (oder `ServiceValidationError` mit Template-Info): Rendering fehlgeschlagen
- `HomeAssistantError`: Device I/O Fehler

---

## 2) `pixoo.show_message`

### Purpose
Zeigt eine temporäre Override-Page („Message“) an. Wenn Rotation aktiv ist, wird danach zur Rotation zurückgekehrt.

### Targeting
- `target.entity_id`: ein oder mehrere Pixoo Entities

### Schema (konzeptionell)

| Feld | Typ | Pflicht | Beschreibung |
|---|---:|:---:|---|
| `target` | HA target | ✅ | Ziel-Entities/Devices |
| `page` | object | ✅ | Page Definition |
| `duration` | int | ✅ | Anzeigedauer in Sekunden |
| `variables` | object | ❌ | Zusätzliche Variablen |

### Semantik
- Default Policy: **last_wins**
  - Neue Message ersetzt die aktuelle sofort.
  - Timer startet neu.
- Nach Ablauf:
  - Wenn Rotation vorher aktiv war: Resume.
  - Sonst: keine weitere Aktion.

Zusätzliche Verhaltensgarantien:
- Multi-Device Targeting ist best-effort (wie bei `pixoo.render_page`).
- Rendering ist per-component best-effort (wie bei `pixoo.render_page`).

### Errors
Wie bei `pixoo.render_page`.

---

## 3) (Optional) Rotation Control Services

> Nur falls wir Rotation nicht ausschließlich über OptionsFlow steuern wollen.

### `pixoo.rotation_enable`
- `enabled: bool`

### `pixoo.rotation_next`
- Wechselt sofort zur nächsten aktiven Page.

### `pixoo.rotation_reload_pages`
- Reloadt Pages aus einer referenzierten YAML-Datei.

