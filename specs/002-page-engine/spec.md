# Feature Specification: Pixoo Page Engine

**Feature Branch**: `002-page-engine`  
**Created**: 2026-01-01  
**Status**: Draft  
**Input**: User description: "Add Pixoo page engine (components DSL + render_page service + optional rotation + show_message) based on comparison plan and pixoo-homeassistant."

## Clarifications

### Session 2026-01-01

- Q: Wenn `pixoo.render_page` / `pixoo.show_message` auf mehrere Geräte targetet und ein Gerät offline/fehlschlägt: Wie soll der Service reagieren? → A: Best-effort: Alle Geräte versuchen; nur wenn alle fehlschlagen, ist der ServiceCall ein Fehler. Pro-Device Fehler werden geloggt.
- Q: Wo sollen die Page-Definitionen für Rotation primär liegen? → A: Hybrid: Rotation-Konfig in Options (enabled/default_duration + Page-Refs), Pages optional aus YAML-Datei; ad-hoc Pages weiterhin direkt per Service.
- Q: Wenn beim Rendern einer Page eine Komponente fehlschlägt (z. B. Bild-Download 404), wie soll der Service reagieren? → A: Best-effort pro Komponente: Andere Komponenten weiter rendern; ServiceCall ist nur dann Fehler, wenn keine Komponente erfolgreich gerendert werden konnte.
- Q: Wenn nach Template-Rendering eine Komponente out-of-bounds ist (z. B. x=100 auf Pixoo64): Wie soll das System reagieren? → A: Skip+log: Komponente überspringen und Fehler loggen/reporten; andere Komponenten weiter rendern.
- Q: Bei `image.source.url` / `image.source.path`: Soll die Page Engine streng Home Assistant Allowlisting erzwingen? → A: Configurable: Default ist strict allowlist (HA allowlisting MUSS erfüllt sein), optional per Option/Service-Flag auf permissive umstellbar.

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Seite ad-hoc rendern (Priority: P1)

Als Home Assistant Nutzer möchte ich eine einzelne „Page“ (Seitenlayout) auf ein Pixoo-Gerät senden, damit ich ohne Pixel-fiddling in Automations schnell ein kleines Dashboard oder eine Benachrichtigung darstellen kann.

**Why this priority**: Das ist der kleinste, sofort nützliche Kern: Ein einziger Service-Call erzeugt direkt ein sichtbares Ergebnis und bildet die Basis für Rotation, Notifications und Vorlagen.

**Independent Test**: Kann vollständig getestet werden, indem eine Page mit Text/Rechteck/Bild an ein Gerät gesendet wird und das Display erwartbar aktualisiert.

**Acceptance Scenarios**:

1. **Given** ein Pixoo-Gerät ist in Home Assistant eingerichtet, **When** der Nutzer eine Page mit einem Text-Element sendet, **Then** wird der Text innerhalb kurzer Zeit auf dem Display sichtbar.
2. **Given** eine Page enthält mehrere Komponenten (Text + Rechteck + Bild), **When** der Nutzer die Page sendet, **Then** werden alle Komponenten in der vorgesehenen Reihenfolge/Position angezeigt.
3. **Given** die Page enthält Variablen/Templating, **When** die Page gerendert wird, **Then** werden die Inhalte anhand der aktuellen HA-Zustände aufgelöst und angezeigt.

---

### User Story 2 - Seitenliste rotieren lassen (Priority: P2)

Als Home Assistant Nutzer möchte ich mehrere Pages definieren und automatisch rotieren lassen, damit das Pixoo wie ein kleines rotierendes Dashboard funktioniert.

**Why this priority**: Das ist das zentrale „Mehr“ von `pixoo-homeassistant`. Viele User wollen Rotation ohne Automation-Wildwuchs.

**Independent Test**: Kann getestet werden, indem eine definierte Seitenliste gestartet wird und das Gerät innerhalb des konfigurierten Intervalls zuverlässig zwischen mindestens zwei Seiten wechselt.

**Acceptance Scenarios**:

1. **Given** der Nutzer hat 3 Pages konfiguriert, **When** Rotation aktiviert wird, **Then** werden die Pages nacheinander angezeigt.
2. **Given** eine Page hat eine eigene Dauer, **When** Rotation läuft, **Then** bleibt diese Page für die definierte Zeit sichtbar.
3. **Given** eine Page ist deaktiviert (oder ihre Enable-Bedingung ist aktuell false), **When** Rotation läuft, **Then** wird diese Page übersprungen.
4. **Given** alle Pages sind deaktiviert, **When** Rotation läuft, **Then** werden keine Änderungen am Display erzwungen und der Zustand wird nachvollziehbar angezeigt (z. B. „keine aktiven Pages“).

*Hinweis (Konfiguration)*: Die Rotation-Konfiguration (enabled/default_duration + Page-Refs) liegt in den ConfigEntry Options; Page-Definitionen können optional aus einer YAML-Datei unter `/config/` geladen werden.

---

### User Story 3 - Temporäre Override-Message (Priority: P3)

Als Home Assistant Nutzer möchte ich eine „Message Page“ temporär anzeigen (z. B. Türklingel, Alarm, Paket), und danach automatisch zur vorherigen Rotation zurückkehren.

**Why this priority**: Das ist eine UX-Verbesserung gegenüber „einfach überschreiben“: Die Rotation läuft weiter, ohne dass Automations viel Zustand managen müssen.

**Independent Test**: Kann getestet werden, indem bei laufender Rotation eine Message Page für X Sekunden angezeigt wird und danach automatisch die Rotation fortgesetzt wird.

**Acceptance Scenarios**:

1. **Given** Rotation ist aktiv, **When** eine temporäre Message Page mit Dauer 10s gesendet wird, **Then** wird sie sofort angezeigt und nach 10s läuft Rotation weiter.
2. **Given** mehrere Messages werden kurz nacheinander gesendet, **When** eine neue Message eintrifft, **Then** ersetzt sie die aktuell angezeigte Message sofort („letzte gewinnt“) und ihre Dauer startet neu.
3. **Given** Rotation ist nicht aktiv, **When** eine Message Page gesendet wird, **Then** wird sie angezeigt und es erfolgt kein automatisches „Resume“.

---


### User Story 4 - Vorlagen nutzen (Priority: P4)

Als Home Assistant Nutzer möchte ich fertige Vorlagen (z. B. Solar, Progress-Bar, „Now Playing“) nutzen oder anpassen, damit ich schnell zu einem guten Ergebnis komme ohne alles selbst zu layouten.

**Why this priority**: Vorlagen beschleunigen Adoption, reduzieren Frust und schaffen „Batteries included“ wie bei `pixoo-homeassistant`.

**Independent Test**: Kann getestet werden, indem eine mitgelieferte Vorlage ohne zusätzliche Logik geladen/gerendert werden kann und erwartbare Platzhalter existieren.

**Acceptance Scenarios**:

1. **Given** eine Vorlage ist verfügbar, **When** der Nutzer sie auswählt und rendert, **Then** wird ein sinnvolles Layout angezeigt.
2. **Given** der Nutzer überschreibt Variablen/Parameter der Vorlage, **When** gerendert wird, **Then** reflektiert das Ergebnis die Anpassungen.

### Edge Cases
- Ungültige Page-Definition (fehlendes `page_type`, falsche Felder, falsche Datentypen)
- Template-Fehler (Jinja-Ausdruck wirft Fehler oder referenziert unbekannte Entities)
- Bildquelle nicht verfügbar (404, Timeout, ungültige Daten)
- Sehr große Bilder oder unerwartete Bildformate
- Rotation: alle Pages disabled / Enable-Bedingungen ergeben durchgehend false
- Rotation + Override kollidieren (Override während Seitenwechsel; mehrere Overrides)
- Multi-Device Targeting: 1 von N Geräten offline
- Device Reconnect: Gerät war offline und kommt wieder online
- Rate-Limits: sehr häufige Aufrufe aus Automations (Spam)
- Rotation Pages YAML-Datei fehlt/ist ungültig (Parsing-Fehler)
- Komponenten nach Templating out-of-bounds (x/y/width/height außerhalb Display) → Komponente wird übersprungen
- Bildquelle nicht erlaubt (External URL / Path nicht allowlisted)

## Requirements *(mandatory)*
### Functional Requirements

- **FR-001**: Das System MUSS eine Page als Eingabe akzeptieren, die einen `page_type` und zugehörige Daten enthält.
- **FR-002**: Nutzer MÜSSEN eine Page über Home Assistant an ein oder mehrere Pixoo-Geräte senden können.
- **FR-003**: Das System MUSS mindestens die Komponenten-Typen **Text**, **Rechteck** (gefüllt/outline) und **Bild** innerhalb einer Komponenten-Page unterstützen.
- **FR-004**: Das System MUSS erlauben, Textinhalt und Farben dynamisch anhand von Home Assistant Zuständen/Templating zu erzeugen.
- **FR-005**: Das System MUSS Mehrzeilen-Text unterstützen (z. B. `\n`) und eine Ausrichtung (links/zentriert/rechts) anbieten.
- **FR-006**: Das System MUSS Bilder aus mindestens einer externen Quelle (URL) anzeigen können; zusätzliche Quellen (lokaler Pfad, Base64) SOLLEN unterstützt werden.
- **FR-006a**: Für `image.source.url` und `image.source.path` MUSS es ein konfigurierbares Allowlist-Verhalten geben: Default ist **strict** (URL nur, wenn `hass.config.is_allowed_external_url(url)` true; Pfad nur, wenn `hass.config.is_allowed_path(path)` true). Optional MUSS es möglich sein, Allowlisting zu deaktivieren (permissive), wobei Timeout/Size-Limit/Content-Type Checks weiterhin gelten.
- **FR-007**: Das System MUSS fehlerhafte Komponenten einer Page robust behandeln (z. B. Rendering der übrigen Komponenten fortsetzen, nachvollziehbare Fehlermeldung).
- **FR-007a**: Wenn eine einzelne Komponente beim Rendern fehlschlägt (z. B. Bildquelle 404), MUSS das System die übrigen Komponenten weiter rendern und den Fehler nachvollziehbar loggen/reporten. Der ServiceCall DARF nur dann als Fehler enden, wenn **keine** Komponente erfolgreich gerendert werden konnte.
- **FR-007b**: Wenn eine Komponente nach Template-Rendering ungültige Koordinaten/Größen hat (out-of-bounds), MUSS das System diese Komponente überspringen und den Fehler nachvollziehbar loggen/reporten; andere Komponenten MÜSSEN weiter gerendert werden.

- **FR-008**: Nutzer MÜSSEN eine Seitenliste (Pages) konfigurieren können.
- **FR-009**: Das System MUSS eine automatische Rotation über eine Seitenliste unterstützen.
- **FR-010**: Das System MUSS pro Page eine Dauer unterstützen (Standard: 15 Sekunden), die pro Page überschreibbar ist.
- **FR-011**: Das System MUSS pro Page eine Aktivierung/Deaktivierung unterstützen (statisch oder anhand einer Bedingung).
- **FR-012**: Das System MUSS definieren, was passiert, wenn alle Pages deaktiviert sind (keine Display-Änderung erzwingen; klarer Status).

- **FR-013**: Nutzer MÜSSEN eine temporäre Override-Page („show message“) senden können.
- **FR-014**: Das System MUSS eine Dauer für Override-Pages unterstützen und danach in den vorherigen Zustand zurückkehren (wenn Rotation aktiv war).
- **FR-015**: Das System MUSS deterministisches Verhalten definieren, wenn mehrere Overrides in kurzer Zeit eintreffen.
- **FR-015a**: Default-Verhalten MUSS sein: „Letzte gewinnt“ (eine neue Override-Page ersetzt die aktuell angezeigte Override-Page sofort und startet ihre Dauer neu).

- **FR-016**: Das System SOLL mitgelieferte Vorlagen bereitstellen, die typische Smart-Home Use Cases abdecken.
- **FR-017**: Das System MUSS Nutzer beim Konfigurieren von Pages unterstützen (Fehler verständlich erklären, nicht „still“ scheitern).
- **FR-018**: Vorlagen MÜSSEN wie normale Pages renderbar sein (kein Sonder-Handling in Automations notwendig).

- **FR-019**: Bei Multi-Device Targeting MUSS das Verhalten **best-effort** sein: Das System MUSS alle Zielgeräte unabhängig versuchen zu aktualisieren; der ServiceCall DARF nur dann als Fehler enden, wenn **alle** Zielgeräte fehlschlagen. Pro-Device Fehler MÜSSEN nachvollziehbar geloggt werden.

- **FR-020**: Rotation-Konfiguration (enabled/default_duration + Page-Refs) MUSS in ConfigEntry Options gespeichert werden. Page-Definitionen SOLLEN optional aus einer referenzierten YAML-Datei unter `/config/` geladen werden können.

### Key Entities *(include if feature involves data)*

- **Page Definition**: Repräsentiert eine darstellbare Seite (Typ, Dauer, Enable-Bedingung, Inhalte).
- **Component**: Ein Element innerhalb einer Komponenten-Page (Text/Bild/Rechteck, Position, Styling).
- **Rotation Configuration**: Konfiguration einer Seitenliste inkl. globalem Standardintervall.
- **Override Message**: Eine temporäre Page mit Ablaufzeit und definierter Interaktion mit der Rotation.
- **Template/Variable Set**: Variablen/Parameter, die beim Rendern aufgelöst werden.

## Success Criteria *(mandatory)*
### Measurable Outcomes

- **SC-001**: Nutzer können eine Page ohne zusätzliche Automations erstellen und an ein Pixoo senden (mindestens Text + Rechteck) und das Display aktualisiert sich in 95% der Fälle innerhalb von 2 Sekunden im lokalen Netz.
- **SC-002**: Rotation kann mit mindestens 3 Pages über 30 Minuten laufen, ohne dass unerwartete Stopps auftreten (0 ungeplante Stopps).
- **SC-003**: Eine Override-Message kehrt in 100% der Tests nach Ablauf der Dauer zum vorherigen Zustand zurück (Rotation weiter / keine Rotation bleibt stehen).
- **SC-004**: Bei fehlerhaften Inputs (z. B. ungültige Page, fehlendes Bild) liefert das System eine verständliche Fehlermeldung; mindestens 90% der Fehlermeldungen nennen die betroffene Komponente/Feld.
- **SC-004**: Bei fehlerhaften Inputs oder Rendering-Fehlern (z. B. ungültige Page, fehlendes Bild) liefert das System eine verständliche Fehlermeldung; mindestens 90% der Fehlermeldungen nennen die betroffene Komponente/Feld. Einzelne Komponentenfehler dürfen die restliche Page nicht verhindern.
- **SC-005**: Das Feature funktioniert für mindestens 2 Geräte parallel (Multi-Device Targeting), wobei ein Offline-Gerät die Anzeige auf Online-Geräten nicht verhindert (best-effort; ServiceCall schlägt nur fehl, wenn alle Targets fehlschlagen).
- **SC-006**: Mindestens 2 mitgelieferte Vorlagen können ohne zusätzliche Konfiguration gerendert werden (z. B. „Progress Bar“ und „Now Playing“).
