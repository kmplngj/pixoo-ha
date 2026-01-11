# Data Model — 002-page-engine (Pixoo Page Engine)

**Date**: 2026-01-01

> Ziel: Klare, validierbare Modelle für Pages/Komponenten/Rotation/Override.
> Implementierungsdetails (konkrete Klassen/Module) sind bewusst ausgelassen.

## 1) Page

### 1.1 Gemeinsame Felder (Base)

| Feld | Typ | Pflicht | Beschreibung | Validierung |
|---|---:|:---:|---|---|
| `page_type` | string | ✅ | Discriminator für den Seitentyp | Muss einem bekannten Typ entsprechen |
| `duration` | number/int | ❌ | Anzeigedauer in Sekunden | min 1, default 15 |
| `enabled` | bool oder template-string | ❌ | Ob Page in Rotation aktiv ist | Template muss zu bool rendern; default true |
| `variables` | map<string, any> | ❌ | Variablen für Template Rendering | Keys sind strings |

### 1.2 Page-Typ: `components`

| Feld | Typ | Pflicht | Beschreibung | Validierung |
|---|---:|:---:|---|---|
| `components` | list<Component> | ✅ | Liste visueller Komponenten | nicht leer; max Länge (z. B. 50) |
| `background` | optional color | ❌ | Hintergrundfarbe | siehe Color Modell |

### 1.3 Page-Typ: `template`

> Optionaler Weg, um mitgelieferte Vorlagen zu referenzieren.

| Feld | Typ | Pflicht | Beschreibung | Validierung |
|---|---:|:---:|---|---|
| `template_name` | string | ✅ | Name der Vorlage | muss existieren |
| `template_vars` | map<string, any> | ❌ | Übergabeparameter | template-spezifisch |

### 1.4 Page-Typen: „Device Modus“ Pages (optional)

> Falls später gewünscht: Pages, die eher Device-Modi setzen (Clock/Visualizer/Channel), statt zu zeichnen.

| page_type | Beschreibung |
|---|---|
| `channel` | setzt Kanal (faces/cloud/custom/…) |
| `clock` | setzt Clock Face |
| `visualizer` | setzt Visualizer |

## 2) Component

### 2.1 Gemeinsame Felder

| Feld | Typ | Pflicht | Beschreibung | Validierung |
|---|---:|:---:|---|---|
| `type` | string | ✅ | Discriminator | muss bekannt sein |
| `x` | int | ✅ | X-Koordinate | 0–63 |
| `y` | int | ✅ | Y-Koordinate | 0–63 |
| `z` | int | ❌ | Layer/Reihenfolge | default: Reihenfolge in Liste |

### 2.2 Color Modell

| Input | Beispiel | Notes |
|---|---|---|
| RGB Tuple/List | `[255, 0, 0]` | clamp 0–255 |
| Hex | `#FF00AA` | optional |
| CSS4 name | `forestgreen` | optional (wenn implementiert) |
| Template | `"{{ ... }}"` | muss zu einem validen Color rendern |

### 2.3 Component: `text`

| Feld | Typ | Pflicht | Beschreibung | Validierung |
|---|---:|:---:|---|---|
| `text` | string/template | ✅ | Textinhalt | max Länge (z. B. 256) |
| `color` | color/template | ❌ | Textfarbe | default white |
| `align` | enum | ❌ | left/center/right | default left |
| `font` | enum/string | ❌ | Font Auswahl | default: pico_8 |

### 2.4 Component: `rectangle`

| Feld | Typ | Pflicht | Beschreibung | Validierung |
|---|---:|:---:|---|---|
| `width` | int | ✅ | Breite | 1–64 |
| `height` | int | ✅ | Höhe | 1–64 |
| `color` | color/template | ❌ | Rechteckfarbe | default white |
| `filled` | bool | ❌ | gefüllt oder outline | default true |

### 2.5 Component: `image`

| Feld | Typ | Pflicht | Beschreibung | Validierung |
|---|---:|:---:|---|---|
| `source` | object | ✅ | Bildquelle | genau eine Quelle |
| `source.url` | string/template | ❌ | Bild-URL | allowed_external_url optional |
| `source.path` | string/template | ❌ | lokaler Pfad | is_allowed_path |
| `source.base64` | string | ❌ | base64 image | size limit |
| `resize_mode` | enum | ❌ | fit/fill/none | default fit |

## 3) Rotation

### 3.1 RotationConfig

| Feld | Typ | Pflicht | Beschreibung | Validierung |
|---|---:|:---:|---|---|
| `enabled` | bool | ✅ | Rotation aktiv | — |
| `default_duration` | int | ❌ | Fallback pro Page | min 1, default 15 |
| `pages` | list<PageRef/Page> | ✅ | Seitenliste | nicht leer |

### 3.2 RotationState

| Feld | Typ | Beschreibung |
|---|---:|---|
| `current_index` | int | Aktuelle Page in der Liste |
| `next_run_at` | datetime | nächster Wechsel |
| `last_render_error` | string? | letzter Fehler (optional) |

## 4) Override Message

### 4.1 OverridePolicy

| Feld | Typ | Beschreibung |
|---|---:|---|
| `policy` | enum | `last_wins` (default), optional später FIFO |

### 4.2 OverrideState

| Feld | Typ | Beschreibung |
|---|---:|---|
| `active` | bool | Override aktiv |
| `expires_at` | datetime | Ablaufzeit |
| `page` | Page | aktuell angezeigte Override Page |

## 5) Zustandsübergänge (high-level)

### Rotation

- `STOPPED` → `RUNNING` (wenn enabled)
- `RUNNING` → `STOPPED` (disable/unload)

### Override

- `NO_OVERRIDE` → `OVERRIDE_ACTIVE` (show_message)
- `OVERRIDE_ACTIVE` → `OVERRIDE_ACTIVE` (neue Message; last_wins)
- `OVERRIDE_ACTIVE` → `NO_OVERRIDE` (expiry)

