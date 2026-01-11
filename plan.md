# Page Engine Feature Roadmap

**Status**: In Progress  
**Erstellt**: 2026-01-04  
**Ziel**: Fehlende Features für maximalen Zusatznutzen identifizieren und priorisieren

---

## 🔴 Phase 1: Hohe Priorität

### 1.1 Simulator/Preview ❌ ENTFERNT

Die Simulator-/Preview-Funktionen (Camera-Plattform und Preview-Render-Services) wurden wieder entfernt.

---

### 1.2 Line-Komponente ✅ DONE
**Aufwand**: 0.5 Tage | **Nutzen**: ⭐⭐⭐⭐

Fehlende Primitive für Diagramme, Trennlinien, Dekorationen.

```yaml
- type: line
  start: [0, 32]
  end: [64, 32]
  color: "#FFFFFF"
  thickness: 1  # Optional, default 1
```

**Implementiert**:
- [x] `LineComponent` Model in models.py
- [x] Rendering-Logik in renderer.py (render_page + render_page_to_buffer)
- [x] Threshold-Coloring Support
- [x] Thickness Support (multi-line for thick lines)
- [x] Bounds-Checking für start/end Koordinaten
- [x] 8 Unit-Tests

---

### 1.3 Circle/Ellipse-Komponente ✅ DONE
**Aufwand**: 0.5 Tage | **Nutzen**: ⭐⭐⭐⭐

Für Gauges, Uhren-Elemente, runde Indikatoren.

```yaml
- type: circle
  center: [32, 32]
  radius: 20
  color: "#00FF00"
  filled: false
  thickness: 2  # When filled=false
```

**Implementiert**:
- [x] `CircleComponent` Model
- [x] Pillow `ellipse()` für Rendering (gefüllt und outline)
- [x] Threshold-Coloring Support
- [x] Template-Support für radius, center
- [x] Bounds-Checking für center/radius
- [x] Fallback auf Pixel-by-Pixel wenn kein Pillow-Image verfügbar
- [x] 8 Unit-Tests

---

### 1.4 Arc-Komponente (Fortschrittsring) ✅ DONE
**Aufwand**: 1 Tag | **Nutzen**: ⭐⭐⭐⭐

Runder Batterie-Indikator, Timer-Visualisierung.

```yaml
- type: arc
  center: [32, 32]
  radius: 25
  start_angle: 0
  end_angle: "{{ (states('sensor.battery') | float) * 3.6 }}"
  color: "#00FF00"
  thickness: 3
  filled: false  # false for arc, true for pie slice
  color_thresholds:
    - value: 20
      color: "#FF0000"
    - value: 50
      color: "#FFFF00"
    - value: 100
      color: "#00FF00"
```

**Implementiert**:
- [x] `ArcComponent` Model mit start_angle, end_angle, radius, thickness, filled
- [x] Pillow `arc()` und `pieslice()` für Rendering
- [x] Threshold-Coloring Support
- [x] Template-Support für angles
- [x] Rendering in render_page() und render_page_to_buffer()
- [x] Bounds-Checking
- [x] Unit-Tests

---

### 1.6 Arrow-Komponente (Pfeile mit Richtung) ✅ NEW
**Aufwand**: 0.5 Tage | **Nutzen**: ⭐⭐⭐⭐

Pfeile für Kompass, Windrichtung, Navigation.

```yaml
- type: arrow
  center: [32, 32]
  length: 20
  angle: "{{ state_attr('weather.home', 'wind_bearing') }}"
  color: "#FFFFFF"
  thickness: 2
  head_size: 4  # Arrow head size in pixels
  value: "{{ state_attr('weather.home', 'wind_speed') }}"
  color_thresholds:
    - value: 10
      color: "#00FF00"
    - value: 20
      color: "#FFAA00"
    - value: 30
      color: "#FF0000"
```

**Implementiert**:
- [x] `ArrowComponent` Model mit center, length, angle, thickness, head_size
- [x] Arrow rendering mit Rotation (0° = North, clockwise)
- [x] Arrow head als Triangle
- [x] Threshold-Coloring Support
- [x] Template-Support für angle
- [x] Rendering in render_page() und render_page_to_buffer()
- [x] Bounds-Checking
- [x] Unit-Tests

---

### 1.5 Conditional Else-Zweig
**Aufwand**: 0.5 Tage | **Nutzen**: ⭐⭐⭐⭐

If/else-Logik für alternative Darstellungen.

```yaml
- type: text
  x: 0
  y: 0
  text: "☀️"
  enabled: "{{ states('weather.home') == 'sunny' }}"
  else:
    type: text
    x: 0
    y: 0
    text: "🌧️"
```

**Tasks**:
- [ ] `else` Feld zu `BaseComponent` hinzufügen
- [ ] Renderer-Logik: wenn `enabled=false`, prüfe `else`
- [ ] Rekursive Validierung (else kann wieder else haben?)

---

## 🟡 Phase 2: Mittlere Priorität

### 2.1 Sprite-Sheets/Animation
**Aufwand**: 2 Tage | **Nutzen**: ⭐⭐⭐

Animierte Icons ohne GIF, eigene Pixel-Animationen.

```yaml
- type: sprite
  source:
    url: "https://example.com/spritesheet.png"
  frame_width: 16
  frame_height: 16
  frame_count: 8
  fps: 10
  x: 24
  y: 24
```

**Tasks**:
- [ ] `SpriteComponent` Model
- [ ] Frame-Extraktion aus Spritesheet
- [ ] Timer für Frame-Wechsel

---

### 2.2 Mehrere Fonts
**Aufwand**: 1 Tag | **Nutzen**: ⭐⭐⭐

Pixel-Fonts für verschiedene Größen.

```yaml
- type: text
  font: "pico8"  # 3x5 Pixel
  # oder
  font: "gicko"  # 5x7 Pixel
```

**Tasks**:
- [ ] Font-Dateien einbinden (Bitmap-Fonts)
- [ ] Font-Rendering mit Pillow `ImageFont`
- [ ] Fallback auf Default-Font

---

### 2.3 Komponenten-Gruppen
**Aufwand**: 1 Tag | **Nutzen**: ⭐⭐⭐

Gruppierte Elemente als Block verschieben.

```yaml
- type: group
  x: 10
  y: 10
  components:
    - type: rectangle
      x: 0  # Relativ zur Gruppe
      y: 0
      width: 30
      height: 20
    - type: text
      x: 2
      y: 5
      text: "Hello"
```

**Tasks**:
- [ ] `GroupComponent` Model
- [ ] Koordinaten-Offset im Renderer
- [ ] Rekursive Bounds-Prüfung

---

### 2.4 Live-Reload YAML
**Aufwand**: 0.5 Tage | **Nutzen**: ⭐⭐⭐

Automatisches Neuladen bei Dateiänderung.

**Tasks**:
- [ ] File-Watcher für `pages_yaml_path`
- [ ] Debounce (nicht bei jedem Speichern)
- [ ] Logging bei Reload

---

### 2.5 Z-Index explizit
**Aufwand**: 0.5 Tage | **Nutzen**: ⭐⭐

Explizite Layering-Kontrolle.

```yaml
- type: rectangle
  z: 10  # Höher = weiter vorne
  ...
- type: text
  z: 20
  ...
```

**Tasks**:
- [ ] `z` Feld bereits vorhanden, aber nicht genutzt
- [ ] Sortierung vor Rendering

---

## 🟢 Phase 3: Nice-to-have

### 3.1 QR-Code-Komponente
**Aufwand**: 0.5 Tage | **Nutzen**: ⭐⭐

```yaml
- type: qrcode
  x: 16
  y: 16
  size: 32
  data: "https://example.com"
```

**Tasks**:
- [ ] `qrcode` Library (Pure Python)
- [ ] `QRCodeComponent` Model

---

### 3.2 Countdown-Timer-Komponente
**Aufwand**: 1 Tag | **Nutzen**: ⭐⭐

```yaml
- type: countdown
  x: 10
  y: 20
  target: "{{ states.input_datetime.timer.state }}"
  format: "mm:ss"
```

**Tasks**:
- [ ] `CountdownComponent` Model
- [ ] Auto-Update jede Sekunde

---

### 3.3 Weather-Icons dynamisch
**Aufwand**: 0.5 Tage | **Nutzen**: ⭐⭐

```yaml
- type: weather_icon
  x: 0
  y: 0
  size: 16
  entity_id: weather.home
```

**Tasks**:
- [ ] Mapping: HA weather condition → MDI Icon
- [ ] Automatische Farbwahl (Sonne=gelb, Regen=blau)

---

### 3.4 Clock-Overlay
**Aufwand**: 0.5 Tage | **Nutzen**: ⭐⭐

```yaml
page_type: components
clock_overlay:
  position: top_right  # oder [x, y]
  format: "%H:%M"
  color: "#FFFFFF"
```

---

## Tracking

| Feature | Phase | Status | Assigned | PR |
|---------|-------|--------|----------|-----|
| Simulator/Preview | 1 | ✅ Done | Copilot | - |
| Line | 1 | ✅ Done | Copilot | - |
| Circle | 1 | ✅ Done | Copilot | - |
| Arc | 1 | ✅ Done | Copilot | - |
| Arrow | 1 | ✅ Done | Copilot | - |
| Conditional Else | 1 | ⬜ Backlog | - | - |
| Sprite-Sheets | 2 | ⬜ Backlog | - | - |
| Multiple Fonts | 2 | ⬜ Backlog | - | - |
| Component Groups | 2 | ⬜ Backlog | - | - |
| Live-Reload | 2 | ⬜ Backlog | - | - |
| Z-Index | 2 | ⬜ Backlog | - | - |
| QR-Code | 3 | ⬜ Backlog | - | - |
| Countdown | 3 | ⬜ Backlog | - | - |
| Weather Icons | 3 | ⬜ Backlog | - | - |
| Clock Overlay | 3 | ⬜ Backlog | - | - |

---

## Bereits vorhanden ✅

- Text (mit Scrolling, Alignment)
- Rectangle (gefüllt/outline)
- Image (URL/Path/Base64)
- Icon (MDI mit Threshold-Coloring)
- ProgressBar (horizontal/vertikal, Thresholds)
- Graph (Entity-History, Line/Bar/Area)
- Line (start/end, thickness, Threshold-Coloring)
- Circle (center/radius, filled/outline, Threshold-Coloring)
- Arc (center/radius, start_angle/end_angle, filled/outline, Threshold-Coloring)
- Arrow (center/length/angle, thickness, head_size, Threshold-Coloring)
- Rotation (Duration, Enable-Conditions)
- Override-Messages (Auto-Resume)
- Template-Pages (Wiederverwendbare Layouts)
- Channel-Pages (Native Pixoo Clocks/Visualizer)
```
