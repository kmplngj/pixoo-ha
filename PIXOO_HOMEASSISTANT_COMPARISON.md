# Vergleich: `pixoo-homeassistant` vs `pixoo-ha`

Stand: 2025-12-30

Dieser Text beantwortet: **„Was macht `pixoo-homeassistant` mehr/besser als mein `pixoo-ha`?“** – und umgekehrt. Beide Projekte lösen *leicht unterschiedliche* Probleme.

## Kurzfazit

- **`pixoo-homeassistant`** ist im Kern ein **„Page-/Dashboard-Renderer“**: Du definierst Seiten (Pages) in YAML (inkl. Templates), die Integration rendert diese Seiten zyklisch auf dem Pixoo. Das ist extrem praktisch, wenn du ein **Mini-Dashboard auf dem Display** willst.
- **`pixoo-ha`** ist im Kern eine **„Home-Assistant-native Geräteintegration“**: Viele Entities/Services (inkl. Media-Player-Slideshow, Notify, Drawing-Services), sauber in HA-Patterns gegossen. Das ist ideal, wenn du **Automations, Tools, Medien, iOS-Uploads** etc. robust integrieren willst.

Wenn du die *Page-Engine* von `pixoo-homeassistant` liebst, ist das ein Feature-Gap in `pixoo-ha` (noch). Wenn du hingegen **HA-native Kontrolle + breitere Geräte-/Feature-Abdeckung** willst, spielt `pixoo-ha` seine Stärken aus.

---

## Was `pixoo-homeassistant` „mehr“ macht (gegenüber `pixoo-ha`)

### 1) Eingebaute Page-Engine (Seitenrotation)

`pixoo-homeassistant` hat als zentrales Konzept eine **Liste von Pages** (`pages_data`) in den Options der Config Entry. Diese Seiten werden automatisch nacheinander angezeigt:

- globales „Scan interval“ (Sekunden)
- pro Page optional `duration:` (Template erlaubt)
- pro Page optional `enabled:` (Template erlaubt)
- automatische Planung via HA Background Task (`async_schedule_next_page`)

➡️ Ergebnis: **Du bekommst „Dashboard-Rotation“ out-of-the-box**, ohne eigene Automations.

### 2) „Components“-Page: mehrere Elemente auf einer Seite

Ein echter USP: `page_type: components` (alias `custom`) erlaubt ein **Canvas-Modell**:

- `type: text` (positioniert, Templates, Fonts, Farbe, Align)
- `type: image` (aus `image_path`, `image_url`, `image_data`; optional resize)
- `type: rectangle` (gefüllt oder outline)
- `type: templatable` (Template erzeugt dynamisch weitere Komponenten)

➡️ Das ist ein **High-Level Layout DSL** für 64×64.

In `pixoo-ha` kannst du das prinzipiell mit Drawing-Services + `push_buffer` nachbauen, aber du musst die Logik derzeit **selbst** orchestrieren (Scripts/Automations).

### 3) Vordefinierte „Special Pages“

`pixoo-homeassistant` bringt fertige Seiten mit eigenem Rendering-Code:

- **PV/Solar** (`page_type: PV`)
- **Fuel** (`page_type: fuel`)
- **Progress Bar** (`page_type: progress_bar`)

Die Seiten kombinieren Templates, Icons und Layout, ohne dass du jedes Pixel selbst planen musst.

➡️ Das ist „Batteries included“ für typische Smarthome-Dashboards.

### 4) Service „show_message“ als Push-Override für *beliebige* Page

Der Service `divoom_pixoo.show_message` nimmt `page_data` (eine Page im YAML-Format) und zeigt diese temporär an – danach geht’s zurück zur Rotation.

➡️ Sehr bequem für **Push Notifications** auf Basis *kompletter Seitenlayouts*, nicht nur „Text anzeigen“.

### 5) „Alles in einer Entity“

Technisch hängt die Page-Engine an einem einzigen Sensor-Entity („Current Page“) + Entity Services.

➡️ Aus Nutzersicht: **sehr wenige Entities**, sehr wenig UI-Rauschen.

### 6) Discovery-Flow über Divoom-Cloud Endpoint

`pixoo-homeassistant` nutzt für Discovery (in `config_flow.py`) ein HTTP-Endpoint:

- `https://app.divoom-gz.com/Device/ReturnSameLANDevice`

➡️ Vorteil: funktioniert oft „einfach so“ ohne SSDP.

⚠️ Nachteil: potentiell **Internet-Abhängigkeit**/externer Dienst (je nach Verfügbarkeit/Firewall/Privacy-Anspruch).

---

## Was `pixoo-ha` „mehr“ macht (gegenüber `pixoo-homeassistant`)

### 1) HA-native Integration: viele Plattformen/Entities

`pixoo-ha` ist (bewusst) eine breite HA-Integration:

- **Light** (Power + Brightness)
- **Select/Switch/Number/Sensor/Button** (Tool- & Konfig-Features)
- **Media Player** (Image Gallery/Slideshow)
- **Notify** (komfortable Benachrichtigungen)

➡️ Das passt in HA UI, Dashboards, Automations und Service-Calls „wie man es erwartet“.

### 2) Media Player: Playlist/Slideshow ist ein echtes Extra

`pixoo-homeassistant` hat Page-Rotation, aber keinen HA-typischen Media-Player, der sich wie ein Foto-Frame verhält.

`pixoo-ha` kann:

- `media_player.play_media` mit Playlist JSON
- Shuffle/Repeat
- Next/Previous

➡️ Für „digitaler Bilderrahmen“ ist das sehr stark.

### 3) iOS Shortcuts / Base64 Image Upload

`pixoo-ha` hat `pixoo.display_image_data` (base64). Das ist für iOS Shortcuts/Apps super praktisch, weil du **kein Hosting** brauchst.

### 4) Drawing-Services als API (Buffer Workflow)

`pixoo-homeassistant` nutzt intern `draw_*` + `push()` für seine Pages.

`pixoo-ha` exponiert Drawing als Services (z.B. `pixoo.draw_pixel`, `pixoo.draw_line`, `pixoo.draw_rectangle`, `pixoo.push_buffer`).

➡️ Dadurch kannst du in HA sehr gezielt pixelgenaue Dinge bauen (und das auch skripten/automatisieren).

### 5) Modernes Python/Integration-Engineering (pixooasync)

`pixoo-ha` basiert auf `pixooasync` (Pydantic, httpx, async-first) und hat (in deinem Repo) umfangreiche Spezifikation/Tests.

`pixoo-homeassistant` enthält einen eigenen `Pixoo`-Client, der stark am klassischen requests-basierten Stil hängt.

➡️ Für Wartbarkeit/Weiterentwicklung/Qualität ist das ein dicker Pluspunkt für `pixoo-ha`.

---

## Architekturvergleich (konzeptionell)

| Thema | `pixoo-homeassistant` | `pixoo-ha` |
|---|---|---|
| Primäres Ziel | Pixoo als **rotierendes Mini-Dashboard** | Pixoo als **voll integriertes HA-Gerät** |
| Haupt-UI | Ein Sensor („Current Page“) + Services | Viele Entities + Services + Media Player |
| Layout/Komposition | YAML Pages + „components“ DSL | Services/Entities; Layout über Automations oder Drawing |
| Page Rotation | eingebaut | nicht als Kernfeature (derzeit) |
| Push Notification | `show_message` (Page-basiert) | `notify.*` + Services (Text/Bild/GIF) |
| Gerätefokus | Pixoo 64 (Branding/Scope) | Pixoo64 + weitere (laut README) |
| Discovery | Divoom LAN API | SSDP (laut README/Spec) |
| Dependencies | „implizit“ (requests/PIL im Code, requirements leer) | explizit (manifest requirements) |

---

## Wann ist welches Projekt „besser“?

### Nimm eher `pixoo-homeassistant`, wenn …

- du ein **Dashboard** willst (mehrere Elemente auf einer Seite)
- du **Pages rotieren** lassen willst ohne Automations-Wildwuchs
- du fertige Seiten wie PV/Fuel/Progressbar nutzen willst
- du möglichst wenige Entities in HA sehen willst

### Nimm eher `pixoo-ha`, wenn …

- du das Gerät **HA-native** steuern willst (Entities, Services, Automations)
- du **Media Player/Slideshow** willst
- du **iOS Shortcuts** (base64) nutzen willst
- du viele Gerätedetails/Features als Entities brauchst
- du Wert auf **modernes Python + Tests + Architektur** legst

---

## Konkretes „Feature-Gap“ aus Sicht von `pixoo-ha`

Das wichtigste „Mehr“ von `pixoo-homeassistant` ist die **Page-Engine + Layout-DSL**.

Wenn du diese UX in `pixoo-ha` willst, wäre ein naheliegender Ausbau:

- neuer Service wie `pixoo.render_page` (oder `pixoo.show_page`) mit einem Schema ähnlich `page_data`
- optional: OptionsFlow/Config mit `pages_data` + „scan_interval“
- Renderer, der `components` in Buffer zeichnet und dann `push_buffer` aufruft

Das wäre sehr gut kompatibel mit dem, was `pixoo-ha` heute schon kann (Drawing + Image + Templates), nur eben „verpackt“.

---

## Hinweis zu Performance/Robustheit (neutral)

- `pixoo-homeassistant` lädt Bilder via `requests.get(...)` (blocking, im Executor), ohne klar dokumentierte Limits (Größe/Timeout/Content-Type). Für normale Nutzung ok, aber bei großen/kaputten URLs kann das schwerer zu kontrollieren sein.
- `pixoo-ha` hat in der Architektur/Guidelines bereits sauberere Patterns (async, Validierung, Limits möglich) und einen stärkeren Fokus auf Testbarkeit.

---

## Empfehlung für deine Doku-Struktur (falls du das ins README ziehen willst)

- 10 Zeilen „Was ist pixoo-ha?“
- Link auf diese Datei
- Optional: „Wenn du Pages/Layouts/Rotation willst → siehe Roadmap/Issue“
---

# Feature-Transfer-Plan: Von `pixoo-homeassistant` nach `pixoo-ha`

Detaillierte Analyse welche Features wie übernommen und dabei optimiert werden können.

## Übersicht der transferierbaren Features

| Feature | Priorität | Aufwand | Optimierungspotenzial |
|---------|-----------|---------|----------------------|
| Page-Engine (Rotation) | 🟢 Hoch | Mittel | Async-first, Pydantic Schemas |
| Components DSL | 🟢 Hoch | Mittel | Type-safe, erweiterte Fonts |
| Special Pages (PV/Fuel/Progress) | 🟡 Mittel | Gering | Template-basiert statt hardcoded |
| show_message Service | 🟢 Hoch | Gering | Mit bestehenden Services integrieren |
| Divoom Cloud Discovery | 🟡 Mittel | Gering | Als Fallback zu SSDP |
| CSS4 Color Names | 🟢 Hoch | Gering | Direkt übernehmen |
| Multi-Font Support | 🟢 Hoch | Gering | Bereits in pixooasync vorhanden |

---

## Phase 1: Quick Wins (1-2 Tage)

### 1.1 CSS4 Color Names übernehmen

**Was**: `pixoo-homeassistant` unterstützt CSS4-Farbnamen (`red`, `blue`, `forestgreen`, etc.).

**Quelle**: [`pixoo64/_colors.py`](https://github.com/gickowtf/pixoo-homeassistant) - 150+ benannte Farben

**Implementation in `pixoo-ha`**:

```python
# custom_components/pixoo/colors.py (neu)
CSS4_COLORS = {
    'aliceblue': (240, 248, 255),
    'red': (255, 0, 0),
    'green': (0, 128, 0),
    # ... alle Farben aus _colors.py
}

def parse_color(color_input: str | list | tuple, default=(255, 255, 255)) -> tuple[int, int, int]:
    """Parse color from CSS4 name, hex string, or RGB tuple."""
    if isinstance(color_input, (list, tuple)) and len(color_input) >= 3:
        return (color_input[0], color_input[1], color_input[2])
    if isinstance(color_input, str):
        color_lower = color_input.lower().strip()
        if color_lower in CSS4_COLORS:
            return CSS4_COLORS[color_lower]
        if color_lower.startswith('#'):
            # Hex parsing
            hex_color = color_lower.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return default
```

**Optimierung gegenüber Original**:
- ✅ Pydantic Validator für Type Safety
- ✅ Hex-Farben (#RRGGBB) UND CSS4-Namen in einem
- ✅ Keine Template-Abhängigkeit für einfache Fälle

---

### 1.2 `render_color()` Helper mit Template-Support

**Was**: `pixoo-homeassistant` rendert Farben als Templates (dynamische Farben basierend auf Zustand).

**Quelle**: [`pixoo64/_colors.py:render_color()`](https://github.com/gickowtf/pixoo-homeassistant)

```python
def render_color(color_value, hass, variables=None, default=(255, 255, 255)):
    """Render color with Jinja2 template support."""
    if color_value is None:
        return default
    
    if isinstance(color_value, str):
        try:
            rendered = Template(color_value, hass).async_render(variables=variables or {})
            return parse_color(rendered, default)
        except TemplateError:
            return parse_color(color_value, default)
    
    return parse_color(color_value, default)
```

**Integration in Services**:
- `display_text` → `color` Parameter mit Template-Support
- `draw_text_at_position` → ebenso
- `draw_rectangle` → ebenso

---

### 1.3 Divoom Cloud Discovery als Fallback

**Was**: `pixoo-homeassistant` nutzt die Divoom Cloud API für Device Discovery.

**Quelle**: [`config_flow.py:get_lan_devices()`](https://github.com/gickowtf/pixoo-homeassistant)

```python
async def async_discover_via_cloud(hass: HomeAssistant) -> list[dict]:
    """Discover Pixoo devices via Divoom Cloud API."""
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://app.divoom-gz.com/Device/ReturnSameLANDevice",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                data = await response.json()
                return [
                    {
                        "ip": device["DevicePrivateIP"],
                        "name": device["DeviceName"],
                        "mac": device.get("DeviceMac", ""),
                    }
                    for device in data.get("DeviceList", [])
                ]
    except Exception:
        return []
```

**Optimierung**:
- ✅ Async mit `aiohttp` statt blocking `requests`
- ✅ Als Fallback wenn SSDP nichts findet
- ✅ Privacy-Warnung in der UI: „Nutzt externe Divoom-Server"

---

## Phase 2: Page-Engine (3-5 Tage)

### 2.1 Datenmodell für Pages

**Neues Pydantic Model** (`custom_components/pixoo/models/page.py`):

```python
from pydantic import BaseModel, Field
from typing import Literal, Union, Optional
from enum import Enum

class FontName(str, Enum):
    PICO_8 = "pico_8"
    GICKO = "gicko"
    FIVE_PIX = "five_pix"
    ELEVEN_PIX = "eleven_pix"
    CLOCK = "clock"

class TextComponent(BaseModel):
    type: Literal["text"] = "text"
    content: str  # Supports Jinja2 templates
    position: tuple[int, int] = (0, 0)
    color: str | tuple[int, int, int] = (255, 255, 255)
    font: FontName = FontName.PICO_8
    align: Literal["left", "center", "right"] = "left"

class ImageComponent(BaseModel):
    type: Literal["image"] = "image"
    position: tuple[int, int] = (0, 0)
    # One of these must be set:
    image_path: Optional[str] = None      # Local file
    image_url: Optional[str] = None       # HTTP URL
    image_data: Optional[str] = None      # Base64
    # Optional sizing:
    width: Optional[int] = None
    height: Optional[int] = None
    resample_mode: Literal["nearest", "box", "bilinear", "lanczos"] = "box"

class RectangleComponent(BaseModel):
    type: Literal["rectangle"] = "rectangle"
    position: tuple[int, int]
    size: tuple[int, int]
    color: str | tuple[int, int, int] = (255, 255, 255)
    filled: bool = True

PageComponent = Union[TextComponent, ImageComponent, RectangleComponent]

class ComponentsPage(BaseModel):
    page_type: Literal["components", "custom"] = "components"
    components: list[PageComponent]
    duration: int = 15  # Sekunden (Template-fähig)
    enabled: bool | str = True  # bool oder Template-String
    variables: dict[str, str] = Field(default_factory=dict)

class ChannelPage(BaseModel):
    page_type: Literal["channel"] = "channel"
    id: int
    duration: int = 15
    enabled: bool | str = True

class ClockPage(BaseModel):
    page_type: Literal["clock"] = "clock"
    id: int
    duration: int = 15
    enabled: bool | str = True

class GifPage(BaseModel):
    page_type: Literal["gif"] = "gif"
    gif_url: str
    duration: int = 15
    enabled: bool | str = True

class VisualizerPage(BaseModel):
    page_type: Literal["visualizer"] = "visualizer"
    id: int
    duration: int = 15
    enabled: bool | str = True

PageData = Union[ComponentsPage, ChannelPage, ClockPage, GifPage, VisualizerPage]
```

**Optimierung gegenüber Original**:
- ✅ **Type Safety**: Pydantic validiert zur Laufzeit
- ✅ **Discriminated Union**: `page_type` wählt automatisch das richtige Model
- ✅ **IDE Support**: Autocomplete für alle Felder
- ✅ **Dokumentation**: Model-Definitionen = API-Dokumentation

---

### 2.2 Page Renderer Service

**Neuer Service**: `pixoo.render_page`

```yaml
# services.yaml
render_page:
  name: Render page
  description: Render a page layout with components (text, images, rectangles) on the Pixoo device.
  target:
    entity:
      domain: light
      integration: pixoo
  fields:
    page_data:
      name: Page Data
      description: Page definition with components. Supports text, image, rectangle, channel, clock, gif, visualizer.
      required: true
      selector:
        object:
    duration:
      name: Duration
      description: Override display duration in seconds. Defaults to page_data.duration or 15.
      required: false
      selector:
        number:
          min: 1
          max: 3600
          unit_of_measurement: seconds
```

**Implementation** (`__init__.py`):

```python
async def handle_render_page(call: ServiceCall) -> None:
    """Handle render_page service call."""
    page_data = call.data["page_data"]
    duration_override = call.data.get("duration")
    entity_ids = call.data.get("entity_id")
    
    # Validate with Pydantic
    try:
        page = parse_page_data(page_data)  # Returns PageData union
    except ValidationError as err:
        raise ServiceValidationError(f"Invalid page_data: {err}")
    
    entries = _resolve_entry_ids(hass, entity_ids)
    
    for entry in entries:
        data = hass.data[DOMAIN][entry.entry_id]
        pixoo: PixooAsync = data["pixoo"]
        service_queue: ServiceQueue = data["service_queue"]
        
        async def _execute():
            await render_page_to_device(hass, pixoo, page, duration_override)
        
        await service_queue.enqueue(_execute())
```

**Renderer** (`renderer.py` - neu):

```python
async def render_page_to_device(
    hass: HomeAssistant,
    pixoo: PixooAsync,
    page: PageData,
    duration_override: int | None = None
) -> None:
    """Render a page to the Pixoo device."""
    
    if isinstance(page, ComponentsPage):
        pixoo.clear()
        
        # Render variables first
        rendered_vars = {}
        for name, template_str in page.variables.items():
            rendered_vars[name] = await render_template(hass, template_str, rendered_vars)
        
        for component in page.components:
            if isinstance(component, TextComponent):
                text = await render_template(hass, component.content, rendered_vars)
                color = await render_color(hass, component.color, rendered_vars)
                font = get_font(component.font)
                pixoo.draw_text(text.upper(), component.position, color, font, component.align)
            
            elif isinstance(component, ImageComponent):
                image = await load_image_component(hass, component, rendered_vars)
                if image:
                    pixoo.draw_image(image, component.position)
            
            elif isinstance(component, RectangleComponent):
                color = await render_color(hass, component.color, rendered_vars)
                if component.filled:
                    pixoo.draw_filled_rectangle(
                        component.position,
                        (component.position[0] + component.size[0] - 1,
                         component.position[1] + component.size[1] - 1),
                        color
                    )
                else:
                    # Draw outline rectangle with lines
                    pass
        
        await pixoo.push()
    
    elif isinstance(page, ChannelPage):
        await pixoo.set_custom_page(page.id)
    
    elif isinstance(page, ClockPage):
        await pixoo.set_clock(page.id)
    
    elif isinstance(page, GifPage):
        await pixoo.play_gif(page.gif_url)
    
    elif isinstance(page, VisualizerPage):
        await pixoo.set_visualizer(page.id)
```

---

### 2.3 Page Rotation Controller (Optional Feature)

**Architektur-Entscheidung**: In `pixoo-ha` als **optionaler Coordinator** statt fest eingebaut.

**Neuer Coordinator** (`coordinator.py`):

```python
class PixooPageRotationCoordinator:
    """Coordinator for automatic page rotation."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        pixoo: PixooAsync,
        pages: list[PageData],
        default_interval: int = 15,
    ):
        self.hass = hass
        self.pixoo = pixoo
        self.pages = pages
        self.default_interval = default_interval
        self._current_index = -1
        self._timer_task: asyncio.Task | None = None
        self._running = False
    
    async def start(self) -> None:
        """Start page rotation."""
        self._running = True
        await self._advance_page()
    
    async def stop(self) -> None:
        """Stop page rotation."""
        self._running = False
        if self._timer_task:
            self._timer_task.cancel()
    
    async def _advance_page(self) -> None:
        """Advance to next enabled page."""
        if not self._running or not self.pages:
            return
        
        # Find next enabled page
        for _ in range(len(self.pages)):
            self._current_index = (self._current_index + 1) % len(self.pages)
            page = self.pages[self._current_index]
            
            if await self._is_page_enabled(page):
                break
        else:
            # All pages disabled
            await self._schedule_next(self.default_interval)
            return
        
        # Render current page
        await render_page_to_device(self.hass, self.pixoo, page)
        
        # Schedule next page
        duration = await self._get_page_duration(page)
        await self._schedule_next(duration)
    
    async def _schedule_next(self, delay: int) -> None:
        """Schedule next page advance."""
        async def _timer():
            await asyncio.sleep(delay)
            await self._advance_page()
        
        self._timer_task = asyncio.create_task(_timer())
```

**Integration via OptionsFlow**:
- Users können `pages_data` + `scan_interval` in den Options konfigurieren
- Rotation startet automatisch wenn konfiguriert
- Switch Entity `switch.pixoo_page_rotation` zum An/Ausschalten

---

## Phase 3: Special Pages als Templates (2-3 Tage)

### 3.1 Template-basierte Special Pages

**Statt hardcoded Renderer** (wie in `pixoo-homeassistant`), als **YAML-Templates** ausliefern:

```yaml
# custom_components/pixoo/templates/solar.yaml
page_type: components
variables:
  power: "{{ states('sensor.solar_power') }}"
  storage: "{{ states('sensor.battery_soc') }}"
  discharge: "{{ states('sensor.battery_discharge') }}"
  consumption: "{{ states('sensor.house_consumption') }}"
  grid: "{{ states('sensor.grid_power') }}"
  time: "{{ now().strftime('%H:%M') }}"
components:
  # Time (top right)
  - type: text
    content: "{{ time }}"
    position: [44, 1]
    color: white
    font: pico_8
  
  # Power section
  - type: image
    image_path: "/config/custom_components/pixoo/assets/sun.png"
    position: [2, 1]
  - type: text
    content: "{{ power }}"
    position: [17, 8]
    color: "{{ 'yellow' if power | float > 0 else 'gray' }}"
    font: gicko
  
  # Battery section
  - type: image
    image_path: "/config/custom_components/pixoo/assets/battery_{{ (storage | float / 20) | int * 20 }}.png"
    position: [2, 17]
  - type: text
    content: "{{ storage }}%"
    position: [17, 25]
    color: white
    font: pico_8
  
  # Discharge (can be + or -)
  - type: text
    content: "{{ discharge }}"
    position: [17, 18]
    color: "{{ 'green' if discharge | float > 0 else 'red' }}"
    font: gicko
  
  # House consumption
  - type: image
    image_path: "/config/custom_components/pixoo/assets/house.png"
    position: [2, 33]
  - type: text
    content: "{{ consumption }}"
    position: [17, 40]
    color: "#007BFF"
    font: gicko
  
  # Grid
  - type: image
    image_path: "/config/custom_components/pixoo/assets/grid.png"
    position: [2, 49]
  - type: text
    content: "{{ grid }}"
    position: [17, 56]
    color: gray
    font: gicko
```

**Vorteile gegenüber Original**:
- ✅ **User-editierbar**: Jeder kann das Template anpassen
- ✅ **Keine Code-Änderungen** für neue Dashboards
- ✅ **Dokumentiert**: YAML ist selbsterklärend
- ✅ **Versioniert**: User können ihre eigenen Templates in `/config/` speichern

---

### 3.2 Progress Bar Template

```yaml
# custom_components/pixoo/templates/progress_bar.yaml
page_type: components
variables:
  header: "{{ header_text }}"
  progress: "{{ progress_value | int }}"
  footer: "{{ footer_text }}"
  time: "{{ now().strftime('%H:%M') }}"
  time_end: "{{ end_time | default('') }}"
components:
  # Background
  - type: rectangle
    position: [0, 0]
    size: [64, 64]
    color: "{{ bg_color | default('#007BFF') }}"
  
  # Header bar
  - type: rectangle
    position: [0, 0]
    size: [64, 7]
    color: "#333333"
  - type: text
    content: "{{ header }}"
    position: [2, 1]
    color: white
    font: five_pix
  
  # Progress bar background
  - type: rectangle
    position: [2, 25]
    size: [60, 9]
    color: "#333333"
  
  # Progress bar fill
  - type: rectangle
    position: [3, 26]
    size: ["{{ (progress * 58 / 100) | int }}", 7]
    color: "{{ progress_bar_color | default('#FF0044') }}"
  
  # Progress text
  - type: text
    content: "{{ progress }}%"
    position: [4, 27]
    color: white
    font: pico_8
  
  # Current time
  - type: text
    content: "{{ time }}"
    position: [15, 10]
    color: "#333333"
    font: clock
  
  # End time
  - type: text
    content: "{{ time_end }}"
    position: [15, 37]
    color: "#979797"
    font: clock
  
  # Footer bar
  - type: rectangle
    position: [0, 57]
    size: [64, 7]
    color: "#333333"
  - type: text
    content: "{{ footer }}"
    position: [2, 58]
    color: white
    font: five_pix
```

---

## Phase 4: show_message Integration (1 Tag)

### 4.1 Service erweitern

**Bestehender notify-Service** + **neuer render_page Service** = kompletter Ersatz für `show_message`.

**Alternative**: Dezidierter Service `pixoo.show_message`:

```yaml
show_message:
  name: Show message
  description: Display a temporary page, then resume rotation (if active).
  target:
    entity:
      domain: light
      integration: pixoo
  fields:
    page_data:
      name: Page Data
      description: Page definition to show temporarily.
      required: true
      selector:
        object:
    duration:
      name: Duration
      description: How long to show the message (seconds).
      required: false
      default: 10
      selector:
        number:
          min: 1
          max: 300
    resume:
      name: Resume rotation
      description: Whether to resume page rotation after the message.
      required: false
      default: true
      selector:
        boolean:
```

**Implementation**:

```python
async def handle_show_message(call: ServiceCall) -> None:
    """Show temporary page, then resume rotation."""
    page_data = call.data["page_data"]
    duration = call.data.get("duration", 10)
    resume = call.data.get("resume", True)
    
    entries = _resolve_entry_ids(hass, call.data.get("entity_id"))
    
    for entry in entries:
        data = hass.data[DOMAIN][entry.entry_id]
        pixoo = data["pixoo"]
        rotation = data.get("page_rotation")  # Optional coordinator
        
        # Pause rotation if active
        if rotation and rotation._running:
            await rotation.stop()
        
        # Render the message page
        page = parse_page_data(page_data)
        await render_page_to_device(hass, pixoo, page)
        
        # Schedule resume
        if resume and rotation:
            async def _resume():
                await asyncio.sleep(duration)
                await rotation.start()
            
            asyncio.create_task(_resume())
```

---

## Zusammenfassung: Implementierungs-Roadmap

### Sprint 1 (Quick Wins) - 1-2 Tage
- [ ] CSS4 Color Names (`colors.py`)
- [ ] `render_color()` mit Template-Support
- [ ] Divoom Cloud Discovery als Fallback in Config Flow
- [ ] Tests für neue Funktionen

### Sprint 2 (Page Engine Core) - 3-5 Tage
- [ ] Pydantic Models für Pages (`models/page.py`)
- [ ] `pixoo.render_page` Service
- [ ] Page Renderer (`renderer.py`)
- [ ] Multi-Font Support (GICKO, FIVE_PIX, ELEVEN_PIX, CLOCK)
- [ ] Tests + Dokumentation

### Sprint 3 (Page Rotation) - 2-3 Tage
- [ ] `PixooPageRotationCoordinator`
- [ ] OptionsFlow für `pages_data` + `scan_interval`
- [ ] `switch.pixoo_page_rotation` Entity
- [ ] Tests + Dokumentation

### Sprint 4 (Templates & Polish) - 2-3 Tage
- [ ] Template-Dateien (solar.yaml, progress_bar.yaml, fuel.yaml)
- [ ] `pixoo.show_message` Service
- [ ] Asset-Dateien (Icons für Solar, Haus, Grid, etc.)
- [ ] Migration-Guide für `pixoo-homeassistant` Users
- [ ] README-Update

---

## Entscheidungen & Trade-offs

### Was wir NICHT übernehmen

| Feature | Grund |
|---------|-------|
| Blocking `requests.get()` | `pixoo-ha` nutzt async httpx/aiohttp |
| `page` in einem Sensor-Entity | `pixoo-ha` hat dedizierte Entities pro Feature |
| Hardcoded Special Pages | Template-basiert ist flexibler |
| Leere `requirements.txt` | `manifest.json` hat explizite Dependencies |

### Was wir BESSER machen

| Original | Optimiert in pixoo-ha |
|----------|----------------------|
| Dict-basierte page_data | Pydantic-validierte Models |
| Sync Rendering im Executor | Async-first mit Buffer-Management |
| Entity Services | Domain-level Services (besser für Automations) |
| Implicit Template rendering | Explicit async template rendering |

---

## Migration für bestehende `pixoo-homeassistant` User

### Mapping: Services

| `pixoo-homeassistant` | `pixoo-ha` |
|-----------------------|------------|
| `divoom_pixoo.show_message` | `pixoo.render_page` oder `pixoo.show_message` |
| `divoom_pixoo.play_buzzer` | `pixoo.play_buzzer` |
| `divoom_pixoo.restart` | *(Button Entity oder neuer Service)* |
| `divoom_pixoo.update_page` | `pixoo.render_page` (expliziter Aufruf) |

### Mapping: Page Types

| `pixoo-homeassistant` | `pixoo-ha` |
|-----------------------|------------|
| `page_type: PV` | Template `solar.yaml` + `pixoo.render_page` |
| `page_type: fuel` | Template `fuel.yaml` + `pixoo.render_page` |
| `page_type: progress_bar` | Template `progress_bar.yaml` + `pixoo.render_page` |
| `page_type: components` | Direkt in `page_data` von `pixoo.render_page` |
| `page_type: channel` | `select.pixoo_custom_page` oder `pixoo.render_page` |
| `page_type: clock` | `select.pixoo_clock` oder `pixoo.render_page` |
| `page_type: gif` | `pixoo.display_gif` |
| `page_type: visualizer` | `select.pixoo_visualizer` oder `pixoo.render_page` |

---

## Offene Fragen

1. **OptionsFlow für Pages**: Soll die Page-Konfiguration in den Integration Options leben (wie `pixoo-homeassistant`) oder als separate YAML-Datei?
   - **Empfehlung**: Beides unterstützen (Options für Quick Setup, YAML für Power User)

2. **Assets (Icons)**: Wo sollen die Bilder liegen?
   - **Empfehlung**: `/config/custom_components/pixoo/assets/` mit Option für User-Custom in `/config/pixoo_assets/`

3. **Multi-Device Rotation**: Soll jedes Gerät eigene Pages haben oder globale Pages für alle?
   - **Empfehlung**: Pro Gerät konfigurierbar (konsistent mit Entity-Design)

4. **Templatable Position/Size**: Sollen auch Positionen/Größen Templates unterstützen?
   - **Empfehlung**: Ja, `pixoo-homeassistant` macht das bereits für Rectangles

---

# Innovative Feature-Ideen für `pixoo-ha`

Features die über `pixoo-homeassistant` hinausgehen und `pixoo-ha` einzigartig machen.

## 🟢 Hohe Priorität (Game Changers)

### 1. Conditional Components (`when:`)

**Idee**: Components die nur gerendert werden wenn eine Bedingung erfüllt ist.

```yaml
components:
  # Warnung nur wenn Fenster offen UND es regnet
  - type: text
    content: "⚠️ FENSTER OFFEN!"
    position: [0, 50]
    color: red
    font: pico_8
    when: "{{ is_state('binary_sensor.fenster', 'on') and is_state('weather.home', 'rainy') }}"
  
  # Normaler Inhalt wenn keine Warnung
  - type: text
    content: "Alles OK ✓"
    position: [0, 50]
    color: green
    when: "{{ not is_state('binary_sensor.fenster', 'on') }}"
```

**Vorteile**:
- ✅ Keine separaten Pages für Warnungen nötig
- ✅ Komplexe Logik direkt im Template
- ✅ Reduziert Automation-Komplexität

**Implementation**: `when` als optionaler Template-String, wird zu boolean gerendert.

---

### 2. Event-Triggered Pages (Interrupt-System)

**Idee**: Bestimmte HA-Events unterbrechen die Rotation und zeigen eine spezielle Page.

```yaml
# In Options oder YAML-Config
event_pages:
  - trigger:
      platform: state
      entity_id: binary_sensor.doorbell
      to: "on"
    page:
      page_type: components
      components:
        - type: image
          image_url: "{{ state_attr('camera.front_door', 'entity_picture') }}"
          position: [0, 0]
          width: 64
          height: 48
        - type: text
          content: "🔔 DOORBELL"
          position: [0, 52]
          color: yellow
    duration: 30
    priority: high  # Unterbricht alles
    buzzer: true    # Optional: Buzzer abspielen
  
  - trigger:
      platform: state
      entity_id: binary_sensor.washing_machine
      to: "off"
    page:
      page_type: components
      components:
        - type: text
          content: "🧺 WÄSCHE FERTIG"
          position: [5, 25]
          color: white
    duration: 60
    priority: normal
```

**Vorteile**:
- ✅ Keine Automations mehr für Standard-Notifications
- ✅ Prioritäten-System (high unterbricht normal)
- ✅ Direkter Buzzer-Support
- ✅ Automatisches Resume nach Ablauf

---

### 3. Mini-Charts & Graphen

**Idee**: Sensor-History als Mini-Graph direkt auf dem Pixoo rendern.

```yaml
components:
  - type: chart
    entity_id: sensor.temperature_outside
    chart_type: line  # line, bar, area
    position: [2, 20]
    size: [60, 30]
    color: "#00BFFF"
    hours: 24  # Letzte 24 Stunden
    min_value: -10
    max_value: 40
    show_current: true  # Aktuellen Wert anzeigen
    show_min_max: true  # Min/Max markieren
```

**Rendering**:
```
    40°─────────────────
       │    ╱╲          
       │   ╱  ╲    ╱╲   
       │  ╱    ╲  ╱  ╲  
       │ ╱      ╲╱    ╲ 
    -10─────────────────
        00:00      23:59
```

**Implementation**:
- HA Recorder API für History-Daten
- Skalierung auf 64x64 Pixel
- Unterstützte Chart-Types: `line`, `bar`, `sparkline`, `gauge`

---

### 4. QR-Code Generator

**Idee**: Dynamische QR-Codes für WiFi-Gäste, URLs, etc.

```yaml
components:
  - type: qrcode
    content: "WIFI:T:WPA;S:GuestNetwork;P:{{ states('input_text.guest_wifi_password') }};;"
    position: [8, 8]
    size: 48  # Quadrat
    color: black
    background: white
  
  - type: text
    content: "Gast-WiFi"
    position: [16, 58]
    color: white
```

**Use Cases**:
- 📶 Gast-WiFi mit rotierendem Passwort
- 🔗 URL zu HA Dashboard
- 📱 Schneller Gerätezugang

**Implementation**: `qrcode` Python Library (klein, pure Python)

---

### 5. Layout-Presets (Grid System)

**Idee**: Vordefinierte Layouts ohne Pixel-Koordinaten.

```yaml
page_type: components
layout: grid_2x2  # Teilt Display in 4 Quadranten

components:
  - type: text
    content: "{{ states('sensor.temp_wohnzimmer') }}°C"
    grid_cell: top_left
    color: white
  
  - type: text
    content: "{{ states('sensor.temp_schlafzimmer') }}°C"
    grid_cell: top_right
    color: white
  
  - type: image
    image_path: "/config/pixoo/icons/humidity.png"
    grid_cell: bottom_left
  
  - type: text
    content: "{{ states('sensor.humidity') }}%"
    grid_cell: bottom_right
    color: cyan
```

**Vordefinierte Layouts**:

| Layout | Beschreibung |
|--------|-------------|
| `grid_2x2` | 4 gleichgroße Quadranten (32x32) |
| `grid_3x3` | 9 Zellen (21x21) |
| `header_content_footer` | 8px Header, 48px Content, 8px Footer |
| `sidebar_left` | 16px Sidebar links, Rest Content |
| `big_number` | Optimiert für große Zahlen mit Label |
| `clock_weather` | Uhr oben, Wetter unten |

---

### 6. Spotify/Media Now Playing

**Idee**: Automatische Albumcover-Anzeige wenn Musik spielt.

```yaml
# Integration mit media_player
event_pages:
  - trigger:
      platform: state
      entity_id: media_player.spotify
      to: "playing"
    page:
      page_type: now_playing
      media_player: media_player.spotify
      layout: cover_info  # cover_only, info_only, cover_info
      scroll_title: true
      show_progress: true
    duration: 0  # Bleibt solange Musik spielt
```

**Rendering**:
```
┌────────────────────┐
│  ┌──────────┐      │
│  │  Album   │ SONG │
│  │  Cover   │ NAME │
│  │  (42x42) │      │
│  └──────────┘Artist│
│  ▓▓▓▓▓▓▓░░░░ 2:34  │
└────────────────────┘
```

**Features**:
- Albumcover automatisch von `entity_picture`
- Scrollender Titel bei langem Text
- Progress Bar
- Pause/Play Icon

---

## 🟡 Mittlere Priorität (Nice to Have)

### 7. Time-Based Page Scheduling

**Idee**: Pages nur zu bestimmten Zeiten zeigen.

```yaml
pages_data:
  - page_type: clock
    id: 39
    schedule:
      start: "22:00"
      end: "07:00"
    # Nur nachts die Uhr zeigen
  
  - page_type: components
    components:
      - type: text
        content: "Guten Morgen!"
    schedule:
      start: "07:00"
      end: "09:00"
      days: [mon, tue, wed, thu, fri]
    # Nur werktags morgens
```

---

### 8. Presence-Aware Display

**Idee**: Display reagiert auf Anwesenheit.

```yaml
# In Options
presence_settings:
  presence_entity: binary_sensor.living_room_presence
  away_action: dim  # dim, off, clock_only
  away_brightness: 10
  return_action: restore
  away_delay: 300  # 5 Minuten warten
```

**Vorteile**:
- 💡 Strom sparen wenn niemand schaut
- 🌙 Automatisch dimmen nachts
- 🏠 Sofort aufwachen bei Bewegung

---

### 9. Notification Queue mit Prioritäten

**Idee**: Intelligente Warteschlange statt sofortigem Überschreiben.

```yaml
# Beim Service-Call
service: pixoo.notify
data:
  message: "Paket angekommen"
  priority: normal  # low, normal, high, critical
  ttl: 300  # Zeit in Sekunden bis zur Anzeige
  queue_behavior: append  # append, replace_same_priority, immediate
  icon: package
```

**Queue-Logik**:
- `critical`: Unterbricht sofort, Buzzer
- `high`: Wird nach aktueller Page gezeigt
- `normal`: Wartet bis Slot frei
- `low`: Nur wenn nichts anderes ansteht

**UI**: Sensor `sensor.pixoo_notification_queue` mit Anzahl wartender Nachrichten.

---

### 10. Blueprint-Bibliothek

**Idee**: Fertige HA Blueprints für typische Pixoo-Anwendungen.

**Blueprints**:
- 📬 `pixoo_mailbox_alert.yaml` - Briefkasten geöffnet → Anzeige
- 🚗 `pixoo_car_charging.yaml` - E-Auto Ladestatus
- 🗑️ `pixoo_garbage_reminder.yaml` - Müllabfuhr-Erinnerung
- 🌡️ `pixoo_climate_warning.yaml` - Frost/Hitze-Warnung
- 📅 `pixoo_calendar_next.yaml` - Nächster Termin
- 🎂 `pixoo_birthday_reminder.yaml` - Geburtstage heute

**Beispiel Blueprint**:
```yaml
blueprint:
  name: Pixoo Türklingel Benachrichtigung
  description: Zeigt Kamerabild wenn Türklingel gedrückt wird
  domain: automation
  input:
    doorbell_sensor:
      name: Türklingel Sensor
      selector:
        entity:
          domain: binary_sensor
    camera_entity:
      name: Türkamera
      selector:
        entity:
          domain: camera
    pixoo_device:
      name: Pixoo Gerät
      selector:
        entity:
          domain: light
          integration: pixoo

trigger:
  - platform: state
    entity_id: !input doorbell_sensor
    to: "on"

action:
  - service: pixoo.show_message
    target:
      entity_id: !input pixoo_device
    data:
      page_data:
        page_type: components
        components:
          - type: image
            image_url: "{{ state_attr(camera_entity, 'entity_picture') }}"
            position: [0, 0]
            width: 64
            height: 50
          - type: text
            content: "🔔 TÜRKLINGEL"
            position: [8, 54]
            color: yellow
      duration: 30
      buzzer: true
```

---

### 11. Scene Integration

**Idee**: HA Scenes können Pixoo-Zustand mit einbeziehen.

```yaml
# scene.yaml
- name: Filmabend
  entities:
    light.wohnzimmer:
      state: on
      brightness: 50
    media_player.tv:
      state: on
    # NEU: Pixoo Integration
    light.pixoo_display:
      state: on
      brightness: 30
      pixoo_page:
        page_type: components
        components:
          - type: text
            content: "🎬 MOVIE TIME"
            position: [10, 28]
            color: "#FFD700"
```

---

### 12. Animation Builder

**Idee**: Eigene Animationen aus Frames erstellen.

```yaml
page_type: animation
frames:
  - components:
      - type: rectangle
        position: [28, 28]
        size: [8, 8]
        color: red
    duration_ms: 200
  
  - components:
      - type: rectangle
        position: [26, 26]
        size: [12, 12]
        color: orange
    duration_ms: 200
  
  - components:
      - type: rectangle
        position: [24, 24]
        size: [16, 16]
        color: yellow
    duration_ms: 200

loop: true
```

**Use Cases**:
- 🚨 Blinkende Warnungen
- 🎄 Festliche Animationen
- ⏳ Loading-Spinner

---

## 🔵 Niedrige Priorität (Future Vision)

### 13. Multi-Zone Layout

**Idee**: Verschiedene Bereiche des Displays unabhängig aktualisieren.

```yaml
zones:
  header:
    position: [0, 0]
    size: [64, 10]
    update_interval: 1  # Jede Sekunde (Uhr)
    components:
      - type: text
        content: "{{ now().strftime('%H:%M:%S') }}"
        position: [16, 1]
  
  main:
    position: [0, 10]
    size: [64, 44]
    update_interval: 60  # Jede Minute
    components:
      - type: text
        content: "{{ states('sensor.temperature') }}°C"
        position: [10, 15]
  
  footer:
    position: [0, 54]
    size: [64, 10]
    # Event-basiert (kein Interval)
    components:
      - type: text
        content: "{{ states('sensor.next_event') }}"
```

**Vorteil**: Uhr aktualisiert sich jede Sekunde ohne das ganze Display neu zu rendern.

---

### 14. Voice Assistant Feedback

**Idee**: Visuelle Bestätigung von Sprachbefehlen.

```yaml
event_pages:
  - trigger:
      platform: event
      event_type: assist_pipeline_run_end
    page:
      page_type: components
      components:
        - type: text
          content: "{{ trigger.event.data.intent_output.speech.plain.speech }}"
          position: [2, 25]
          color: cyan
          font: pico_8
    duration: 5
```

**Integration mit**:
- Home Assistant Assist
- Alexa (via HA Integration)
- Google Home (via HA Integration)

---

### 15. Calendar/Agenda View

**Idee**: Kommende Termine auf dem Pixoo.

```yaml
page_type: calendar
calendar_entity: calendar.family
max_events: 3
layout: compact  # compact, detailed

# Rendered als:
# ┌────────────────────┐
# │ 📅 HEUTE           │
# │ 09:00 Arzt         │
# │ 14:00 Meeting      │
# │ 18:00 Sport        │
# └────────────────────┘
```

---

### 16. Weather Icons Mapping

**Idee**: Automatische Zuordnung von HA Weather-Zuständen zu Pixoo-Icons.

```yaml
weather_icons:
  sunny: "/config/pixoo/weather/sunny.png"
  cloudy: "/config/pixoo/weather/cloudy.png"
  rainy: "/config/pixoo/weather/rainy.png"
  snowy: "/config/pixoo/weather/snowy.png"
  # ... etc

# Usage in Component:
- type: weather_icon
  entity_id: weather.home
  position: [2, 20]
  size: 24
```

**Mitgeliefert**: Icon-Set für alle Standard-Weather-Conditions.

---

### 17. Remote Control Mode

**Idee**: Pixoo als Remote Control für HA.

```yaml
remote_mode:
  enabled: true
  button_mapping:
    # Pixoo hat physische Buttons
    button_left: script.previous_scene
    button_right: script.next_scene
    button_ok: script.toggle_lights
```

**Hinweis**: Abhängig von Pixoo Hardware-Buttons (nicht alle Modelle haben diese).

---

### 18. Community Template Hub

**Idee**: Online-Repository für Templates die User teilen können.

**Konzept**:
- GitHub Repo mit Templates
- In-App Browser zum Durchsuchen
- One-Click Import in eigene Config
- Kategorien: Solar, Wetter, Smart Home, Gaming, Fun

**Beispiel Templates von Community**:
- 🎮 Gaming Stats (Steam, PlayStation)
- 🏠 Hausautomation Dashboard
- 🌡️ Klimaübersicht
- 🚗 Tankpreise
- 📊 Home Assistant Stats

---

## Implementierungs-Prioritäten (Gesamt)

| Phase | Feature | Aufwand | Impact |
|-------|---------|---------|--------|
| **Quick Wins** | CSS4 Colors | 2h | 🟢 |
| **Quick Wins** | Cloud Discovery | 3h | 🟢 |
| **Core** | Page Engine | 2-3 Tage | 🟢🟢🟢 |
| **Core** | Conditional Components | 4h | 🟢🟢 |
| **High Value** | Event-Triggered Pages | 1 Tag | 🟢🟢🟢 |
| **High Value** | Mini-Charts | 1-2 Tage | 🟢🟢 |
| **High Value** | QR-Codes | 4h | 🟢🟢 |
| **High Value** | Layout Presets | 6h | 🟢🟢 |
| **Nice to Have** | Now Playing | 1 Tag | 🟢 |
| **Nice to Have** | Time Scheduling | 4h | 🟢 |
| **Nice to Have** | Presence Aware | 4h | 🟢 |
| **Nice to Have** | Notification Queue | 6h | 🟢 |
| **Nice to Have** | Blueprints | 1 Tag | 🟢🟢 |
| **Future** | Multi-Zone | 2-3 Tage | 🟡 |
| **Future** | Animation Builder | 1-2 Tage | 🟡 |
| **Future** | Calendar View | 1 Tag | 🟡 |
| **Future** | Voice Feedback | 4h | 🟡 |
| **Future** | Community Hub | 1 Woche | 🟡🟡 |

---

## Alleinstellungsmerkmale (USPs) nach Implementation

Mit diesen Features hätte `pixoo-ha` klare Vorteile:

| Feature | pixoo-homeassistant | pixoo-ha (nach Roadmap) |
|---------|---------------------|-------------------------|
| Page Engine | ✅ Basis | ✅ + Conditional, Events, Priorities |
| Charts/Graphen | ❌ | ✅ Sensor History Visualisierung |
| QR-Codes | ❌ | ✅ Dynamisch generiert |
| Layout System | ❌ (nur Koordinaten) | ✅ Grid Presets |
| Event Interrupts | ❌ | ✅ Mit Prioritäten |
| Blueprints | ❌ | ✅ Ready-to-use |
| Now Playing | ❌ | ✅ Spotify/Media Integration |
| Presence Aware | ❌ | ✅ Auto-Dim/Off |
| Multi-Zone | ❌ | ✅ Unabhängige Updates |

**Fazit**: `pixoo-ha` würde zur umfassendsten Pixoo-Integration für Home Assistant werden.
