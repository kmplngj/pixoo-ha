# Display Engine Abstraktion – Research & Planung

> **Status**: Research Phase  
> **Erstellt**: 2026-01-04  
> **Autor**: Jan Kampling + Copilot

---

## 1. Aktuelle Architektur (Status Quo)

### 1.1 Was macht die Page Engine?

Die Page Engine in `pixoo-ha` ist ein deklaratives Rendering-System für Pixoo LED-Displays:

```
YAML Page Definition → Jinja2 Templates → Pydantic Validation → Pillow Rendering → Pixoo Device
```

**Kernfähigkeiten:**
- Deklarative Page-Definitionen in YAML
- Home Assistant Template-Integration (Jinja2 für dynamische Werte)
- Komponenten: Text, Rechteck, Linie, Bild, Icon, Fortschrittsbalken, SVG
- Schwellwert-basierte Farbinterpolation (z.B. Batterie grün→gelb→rot)
- Page-Rotation mit konfigurierbaren Intervallen
- Scrolltext für lange Texte

### 1.2 Warum wurde es so gebaut?

| Entscheidung | Begründung |
|--------------|------------|
| **Home Assistant Integration** | Direkter Zugriff auf Entity-States ohne API-Overhead |
| **YAML-Definition** | HA-Nutzer kennen YAML, keine neue Syntax lernen |
| **Jinja2 Templates** | HA-Standard für dynamische Werte, mächtig und bekannt |
| **Pydantic Models** | Typ-Sicherheit, Validierung, gute Fehlermeldungen |
| **Pillow für Rendering** | Bewährte Python-Bibliothek, alle Bildoperationen abgedeckt |
| **pixooasync direkt** | Minimale Latenz, async-first, kein Middleware-Overhead |

### 1.3 Wie ist es technisch aufgebaut?

```
custom_components/pixoo/page_engine/
├── models.py      # Pydantic-Modelle (Page, Component, etc.) – GENERISCH
├── colors.py      # Farbparsing, Threshold-Interpolation – GENERISCH  
├── templates.py   # Jinja2-Rendering mit HA-Context – HA-SPEZIFISCH
├── loader.py      # YAML-Laden, Template-Auflösung – HA-SPEZIFISCH
├── renderer.py    # Komponenten auf Buffer zeichnen – PIXOO-GEKOPPELT
├── rotation.py    # Page-Wechsel-Scheduler – GENERISCH
└── __init__.py    # Public API
```

**Kopplungspunkte im Renderer:**
```python
# ~20 direkte pixooasync-Aufrufe:
pixoo.fill(r, g, b)
pixoo.draw_text(text, xy, color)
pixoo.draw_text_scrolling(text, xy, color, ...)  # Pixoo-spezifisch!
pixoo.draw_rectangle(xy1, xy2, color)
pixoo.draw_line(start, end, color)
pixoo.draw_image(image, xy)
pixoo.push()  # Buffer an Gerät senden

# Pixoo-exklusive Features:
pixoo.set_channel(channel)  # Clock, Visualizer, Cloud – keine Entsprechung
```

---

## 2. Problem: Warum Abstraktion?

### 2.1 Aktuelle Einschränkungen

1. **Vendor Lock-in**: Code funktioniert nur mit Pixoo-Geräten
2. **Keine Vorschau**: Ohne physisches Gerät kein visuelles Feedback
3. **Testbarkeit**: Unit-Tests brauchen Mock-Device
4. **Wiederverwendung**: Andere Displays (WLED Matrix, HUB75, E-Paper) können nicht profitieren

### 2.2 Potenzielle Display-Typen

| Display-Typ | Auflösung | Farbtiefe | Kommunikation | Machbarkeit |
|-------------|-----------|-----------|---------------|-------------|
| **Pixoo (16/32/64)** | Quadratisch | 24-bit RGB | HTTP JSON | ✅ Aktuell |
| **WLED Matrix** | Beliebig | 24-bit RGB | HTTP/MQTT | ✅ Hoch |
| **HUB75 LED Panel** | Beliebig | 24-bit RGB | SPI/Custom | ✅ Hoch |
| **Ulanzi TC001** | 32×8 | 24-bit RGB | HTTP/MQTT | ✅ Hoch |
| **E-Paper (ESPHome)** | Beliebig | 1-bit/3-bit | SPI | ⚠️ Mittel |
| **HDMI Display** | Beliebig | 24-bit RGB | Framebuffer | ⚠️ Mittel |
| **Simulator/Browser** | Beliebig | 24-bit RGB | WebSocket | ✅ Hoch |

---

## 3. Architektur-Optionen

### Option A: Embedded in Home Assistant (Aktueller Ansatz, erweitert)

```
┌─────────────────────────────────────────────────────────────┐
│                    Home Assistant                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              pixoo-ha Integration                    │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │ Page Engine │  │ Display     │  │ Device      │  │    │
│  │  │ (YAML→PIL)  │→ │ Adapters    │→ │ Connections │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  │                         ↓                            │    │
│  │            ┌────────────┼────────────┐               │    │
│  │            ↓            ↓            ↓               │    │
│  │      PixooAdapter  WLEDAdapter  SimulatorAdapter    │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Vorteile:**
- ✅ Direkter HA-Zugriff (States, Templates, Services)
- ✅ Ein Repository, eine Installation
- ✅ Keine externe Abhängigkeit
- ✅ Einfaches Deployment (HACS)

**Nachteile:**
- ❌ Nur für HA-Nutzer verwendbar
- ❌ Rendering läuft im HA-Event-Loop (Performance?)
- ❌ Schwer testbar ohne HA-Instanz

---

### Option B: Standalone Display Server + HA Sender-Integration

```
┌─────────────────────────────────────────────────────────────┐
│                    Display Server (Standalone)               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ REST/WS API │  │ Page Engine │  │ Device Adapters     │  │
│  │ + Web UI    │→ │ (JSON→PIL)  │→ │ Pixoo/WLED/Sim/...  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         ↑ HTTP/WebSocket
         │
┌────────┴────────────────────────────────────────────────────┐
│                    Home Assistant                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         display-sender Integration (minimal)         │    │
│  │  - Entity-State → JSON Page schicken                 │    │
│  │  - Service: display.render_page                      │    │
│  │  - Sensor: Display-Status                            │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Vorteile:**
- ✅ Unabhängig von Home Assistant nutzbar
- ✅ Eigener Prozess = bessere Performance-Isolation
- ✅ Web-UI für Vorschau und Konfiguration möglich
- ✅ Andere Automatisierungssysteme können es nutzen (Node-RED, ioBroker, etc.)
- ✅ Einfachere Unit-Tests (kein HA-Context nötig)

**Nachteile:**
- ❌ Zusätzlicher Service zu deployen/managen
- ❌ Kein direkter Jinja2-Zugriff auf HA-States
- ❌ Netzwerk-Overhead (HA → Server → Display)
- ❌ Zwei Repositories zu pflegen
- ❌ Template-Rendering muss in HA passieren, dann JSON schicken

---

### Option C: Hybrid – Shared Library + HA Integration

```
┌─────────────────────────────────────────────────────────────┐
│                 PyPI Package: display-engine                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  - Page Models (Pydantic)                            │    │
│  │  - Rendering Engine (Pillow)                         │    │
│  │  - Display Adapters (Pixoo, WLED, Simulator)         │    │
│  │  - NO Home Assistant dependency                      │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
         ↑ pip install
         │
┌────────┴────────────────────────────────────────────────────┐
│  pixoo-ha (HA Integration)     │  standalone-server         │
│  - Templates (Jinja2+HA)       │  - REST API                │
│  - YAML Loader                 │  - Web UI                  │
│  - Services                    │  - Scheduler               │
│  - Coordinator                 │                            │
└────────────────────────────────┴────────────────────────────┘
```

**Vorteile:**
- ✅ Kern-Engine ist wiederverwendbar
- ✅ HA-Integration bleibt "first-class"
- ✅ Standalone-Server als separate Option
- ✅ Gute Testbarkeit (Engine ohne HA testbar)
- ✅ Community kann weitere Adapter beitragen

**Nachteile:**
- ⚠️ Zwei Packages zu pflegen (Engine + HA-Integration)
- ⚠️ Versionierung muss synchron bleiben
- ⚠️ Initialer Aufwand für Refactoring

---

## 4. Empfehlung

### Kurz- bis Mittelfristig: Option A (erweitert)

**Begründung:**
1. **80% der Nutzer sind HA-User** – standalone Server ist Nische
2. **Schnellste Iteration** – kein Package-Management-Overhead
3. **Abstraktion intern** – DisplayBuffer-Interface ohne externes Package

**Konkreter Plan:**

```python
# Neues Interface in page_engine/display.py
from abc import ABC, abstractmethod
from PIL import Image

class DisplayBuffer(ABC):
    """Abstract display buffer – device-agnostic rendering target."""
    
    @property
    @abstractmethod
    def width(self) -> int: ...
    
    @property
    @abstractmethod
    def height(self) -> int: ...
    
    @abstractmethod
    def clear(self, color: tuple[int, int, int] = (0, 0, 0)) -> None: ...
    
    @abstractmethod
    def draw_pixel(self, xy: tuple[int, int], color: tuple[int, int, int]) -> None: ...
    
    @abstractmethod
    def draw_line(self, start: tuple[int, int], end: tuple[int, int], color: tuple[int, int, int]) -> None: ...
    
    @abstractmethod
    def draw_rectangle(self, top_left: tuple[int, int], bottom_right: tuple[int, int], color: tuple[int, int, int], filled: bool = True) -> None: ...
    
    @abstractmethod
    def draw_text(self, text: str, xy: tuple[int, int], color: tuple[int, int, int], font: Any = None) -> None: ...
    
    @abstractmethod
    def draw_image(self, image: Image.Image, xy: tuple[int, int]) -> None: ...
    
    @abstractmethod
    async def push(self) -> None:
        """Send buffer content to physical device."""
        ...
    
    def to_image(self) -> Image.Image:
        """Export buffer as PIL Image (for preview/testing)."""
        ...


class PixooDisplayBuffer(DisplayBuffer):
    """Pixoo-specific implementation using pixooasync."""
    
    def __init__(self, pixoo: PixooAsync):
        self._pixoo = pixoo
    
    @property
    def width(self) -> int:
        return self._pixoo.size
    
    # ... delegate all methods to self._pixoo


class PillowDisplayBuffer(DisplayBuffer):
    """Pure Pillow implementation for testing and preview."""
    
    def __init__(self, width: int, height: int):
        self._image = Image.new("RGB", (width, height), (0, 0, 0))
        self._draw = ImageDraw.Draw(self._image)
    
    async def push(self) -> None:
        pass  # No-op for simulator
    
    def to_image(self) -> Image.Image:
        return self._image.copy()
```

### Langfristig: Option C (wenn Nachfrage steigt)

Wenn andere Projekte die Engine nutzen wollen → Extraktion in PyPI Package.

---

## 5. Einschränkungen & Herausforderungen

### 5.1 Gerätespezifische Features

| Feature | Pixoo | WLED | E-Paper | Lösung |
|---------|-------|------|---------|--------|
| Scrolltext | ✅ Native | ❌ | ❌ | Software-Scrolling im Adapter |
| Native Clocks | ✅ | ❌ | ❌ | Als Pixoo-Extension, nicht im Interface |
| Visualizer | ✅ | ✅ (WLED) | ❌ | Gerätespezifische Services |
| Partial Update | ❌ | ❌ | ✅ | Adapter-spezifisch |
| Grayscale/Dither | ❌ | ❌ | ✅ | Automatisch im E-Paper-Adapter |

**Lösung**: Basis-Interface + gerätespezifische Erweiterungen:

```python
class PixooDisplayBuffer(DisplayBuffer):
    """Pixoo with extra capabilities."""
    
    def draw_text_scrolling(self, text: str, xy: tuple[int, int], ...) -> None:
        """Pixoo-native scrolling text."""
        ...
    
    def set_channel(self, channel: str, clock_id: int | None = None) -> None:
        """Switch to native Pixoo channel."""
        ...
```

### 5.2 Template-Rendering

**Problem**: Jinja2-Templates mit HA-States funktionieren nur in HA.

**Lösungen:**
1. **HA-Only**: Templates bleiben in HA, Engine bekommt fertige Werte
2. **Pre-Render**: HA rendert Templates, schickt JSON mit konkreten Werten
3. **Adapter-Pattern**: Template-Engine als austauschbare Komponente

```python
# Option 2: Pre-rendered pages
class RenderedPage(BaseModel):
    """Page with all templates already resolved."""
    background: tuple[int, int, int]
    components: list[RenderedComponent]  # Keine Templates mehr, nur Werte
```

### 5.3 Farbtiefe-Unterschiede

| Display | Bits | Handling |
|---------|------|----------|
| Pixoo | 24-bit RGB | Direkt |
| WLED | 24-bit RGB | Direkt |
| E-Paper BW | 1-bit | Floyd-Steinberg Dithering |
| E-Paper 3-color | 2-bit | Palette-Mapping |

**Lösung**: Adapter übernimmt Konvertierung:

```python
class EpaperDisplayBuffer(DisplayBuffer):
    def __init__(self, width: int, height: int, palette: list[tuple[int, int, int]]):
        self._palette = palette  # z.B. [(0,0,0), (255,255,255), (255,0,0)]
    
    def _quantize_color(self, color: tuple[int, int, int]) -> tuple[int, int, int]:
        """Map RGB to nearest palette color."""
        ...
```

### 5.4 Update-Frequenz

| Display | Max FPS | Handling |
|---------|---------|----------|
| Pixoo | ~10-30 | Kein Problem |
| WLED | ~30-60 | Kein Problem |
| E-Paper | 0.1-1 | Rate-Limiting im Adapter |

---

## 6. Roadmap

### Phase 1: Interface-Extraktion (1-2 Tage)
- [ ] `DisplayBuffer` ABC definieren
- [ ] `PixooDisplayBuffer` implementieren
- [ ] `PillowDisplayBuffer` für Tests
- [ ] `renderer.py` auf Interface umstellen
- [ ] Bestehende Tests anpassen

### Phase 2: Simulator/Preview (1 Tag)
- [ ] Service: `pixoo.render_preview` → Base64 PNG
- [ ] Optional: WebSocket für Live-Preview

### Phase 3: Weitere Adapter (je 0.5-1 Tag)
- [ ] WLEDDisplayBuffer
- [ ] UlanziDisplayBuffer (TC001)
- [ ] GenericHTTPDisplayBuffer (für Custom-Firmware)

### Phase 4: Evaluierung Standalone (nach Feedback)
- [ ] Nachfrage aus Community bewerten
- [ ] Ggf. PyPI-Package extrahieren

---

## 7. Offene Fragen

1. **Soll der Simulator als HA-Entity existieren?**
   - Pro: Konsistente Bedienung
   - Contra: Overhead für reine Debug-Funktion

2. **Wie mit Scrolltext umgehen?**
   - Pixoo: Native Hardware-Scrolling
   - Andere: Software-Scrolling (mehrere Frames) oder ignorieren?

3. **Multi-Device-Sync?**
   - Szenario: Gleiche Page auf Pixoo + WLED
   - Lösung: Coordinator managed mehrere DisplayBuffers?

4. **Config-Flow für neue Display-Typen?**
   - Aktuell: SSDP-Discovery für Pixoo
   - WLED: mDNS oder manuelle IP
   - Generischer Discovery-Mechanismus?

---

## 8. Fazit

Die Page Engine ist bereits **~70% generisch**. Mit überschaubarem Aufwand (~2-4 Tage) kann ein `DisplayBuffer`-Interface eingeführt werden, das:

1. **Rückwärtskompatibel** bleibt (Pixoo funktioniert wie bisher)
2. **Testbarkeit** verbessert (PillowBuffer für Unit-Tests)
3. **Erweiterbarkeit** ermöglicht (neue Display-Typen als Adapter)
4. **Innerhalb von HA** bleibt (kein externer Server nötig)

Die Standalone-Server-Option (Option B) ist technisch möglich, aber der Mehrwert rechtfertigt den Aufwand aktuell nicht – 80%+ der Nutzer sind HA-User.
