# Quickstart — 002-page-engine (Pixoo Page Engine)

## Ziel
Diese Anleitung hilft Entwickler:innen, die Page Engine lokal zu testen (Unit Tests) und manuell in Home Assistant zu verifizieren.

## Dev Setup

- Python 3.12+
- Abhängigkeiten wie im Projekt beschrieben (Home Assistant dev + pytest)

## Tests

- Unit Tests ausführen: `pytest`
- Nur Page Engine Tests (wenn vorhanden): `pytest -k page_engine`

## Manuelles Testen in Home Assistant

### 1) Code deployen

In diesem Repo ist der übliche Workflow:
1. Änderungen in Workspace: `custom_components/pixoo/`
2. Sync nach HA: `/Volumes/config/custom_components/pixoo/` (rsync/cp)
3. HA neu starten

### 2) Service Call: render_page

In HA → Entwicklerwerkzeuge → **Dienste**:
- Service: `pixoo.render_page`
- Target: dein Pixoo Gerät (Entity)
- Data: eine minimale Components Page mit Text

Beispiel (minimal, aber vollständig):

- Service: `pixoo.render_page`
- Target:
	- `entity_id: light.pixoo_<dein_geraet>`
- Data:
	- `allowlist_mode: strict`  # default
	- `variables:`
			title: "Hallo"
			color: "#00FF00"
	- `page:`
			page_type: components
			background: "#000000"
			components:
				- type: text
					x: 32
					y: 6
					align: center
					text: "{{ title }}"
					color: "{{ color }}"
				- type: rectangle
					x: 2
					y: 18
					width: 60
					height: 12
					filled: false
					color: "#FFFFFF"
				# Optional: Bild (nur wenn URL/Path allowlisted ist; sonst `allowlist_mode: permissive`)
				- type: image
					x: 0
					y: 32
					source:
						url: "https://picsum.photos/64"

Hinweise:
- `allowlist_mode: strict` nutzt HA Allowlisting (`external_url` / `allowed_path`).
- `allowlist_mode: permissive` deaktiviert Allowlisting (Timeout/Size-Limits/Content-Type Checks bleiben aktiv) – sinnvoll für schnelle Tests.
- Templates werden **strict** gerendert: wenn ein Template-Fehler auftritt, sollte das als Service-Fehler sichtbar sein.

### 2b) Service Call: render_page (mit Built-in Templates)

Die Page Engine unterstützt auch **TemplatePages**, die auf mitgelieferte Vorlagen zeigen.

#### Beispiel: `progress_bar`

- Service: `pixoo.render_page`
- Target:
	- `entity_id: light.pixoo_<dein_geraet>`
- Data:
	- `page:`
			page_type: template
			template_name: progress_bar
			template_vars:
				title: "Ladezustand"
				progress: 0.5
				bar_color: "#00FF00"

#### Beispiel: `now_playing`

Hinweis: Wenn `cover_url` verwendet wird, brauchst du ggf. `allowlist_mode: permissive` (oder du allowlistest die URL in HA).

- Service: `pixoo.render_page`
- Target:
	- `entity_id: light.pixoo_<dein_geraet>`
- Data:
	- `allowlist_mode: permissive`
	- `page:`
			page_type: template
			template_name: now_playing
			template_vars:
				title: "Song"
				artist: "Artist"
				cover_url: "https://picsum.photos/64"

### 3) Service Call: show_message

- Service: `pixoo.show_message`
- Dauer: 10 Sekunden
- Erwartung: Display zeigt Message, danach Resume Rotation (wenn aktiv)

## Troubleshooting

- Template Errors: Logs sollten die fehlerhafte Komponente/Feld nennen.
- Images: Prüfe Timeout/Content-Type/Size-Limits.
- Rotation: Wenn keine Pages aktiv sind, darf keine Endlosschleife oder Log-Spam entstehen.

