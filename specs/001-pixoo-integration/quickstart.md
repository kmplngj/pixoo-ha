# Quickstart Guide: Pixoo Integration Development

**Feature**: Divoom Pixoo Home Assistant Integration  
**Target Audience**: Developers contributing to the integration  
**Prerequisites**: Python 3.12+, Home Assistant dev environment, Pixoo device (physical or simulator)

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure Overview](#project-structure-overview)
3. [Running Tests](#running-tests)
4. [Manual Testing](#manual-testing)
5. [Common Tasks](#common-tasks)
6. [Troubleshooting](#troubleshooting)

## Development Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/pixoo-ha.git
cd pixoo-ha
git checkout 001-pixoo-integration
```

### 2. Install Home Assistant Dev Environment

**Option A: Using uv (recommended)**

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # or `.venv/bin/activate.fish` for fish shell

# Install HA and dev dependencies
uv pip install homeassistant pytest pytest-homeassistant-custom-component pytest-aiohttp
```

**Option B: Using pip**

```bash
python3.12 -m venv .venv
source .venv/bin/activate

pip install homeassistant pytest pytest-homeassistant-custom-component pytest-aiohttp
```

### 3. Install pixooasync Package

```bash
# Install from PyPI
uv pip install pixooasync

# Or install from local source (if you're developing pixooasync too)
uv pip install -e ../pixooasync
```

### 4. Set Up Development Configuration

Create a development Home Assistant configuration:

```bash
mkdir -p config/custom_components
ln -s $(pwd)/custom_components/pixoo config/custom_components/pixoo
```

### 5. Configure VS Code (Optional)

Install recommended extensions:

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "GitHub.copilot"
  ]
}
```

## Project Structure Overview

### Key Directories

```
pixoo-ha/
├── custom_components/pixoo/    # Integration code
│   ├── __init__.py              # Setup and service registration
│   ├── manifest.json            # Integration metadata
│   ├── config_flow.py           # Config/options flow
│   ├── coordinator.py           # Data coordinators
│   ├── entity.py                # Base entity class
│   └── [platform].py            # Entity platforms
├── tests/                       # Test suite
│   ├── conftest.py              # Test fixtures
│   └── test_*.py                # Test files
├── docs/                        # Documentation
└── specs/                       # Feature specifications
```

### Important Files

| File | Purpose | Edit Frequency |
|------|---------|----------------|
| `manifest.json` | Integration metadata, dependencies | Rarely |
| `__init__.py` | Entry point, service setup | Occasionally |
| `config_flow.py` | Device discovery and config | Once during setup |
| `coordinator.py` | Data polling logic | Once during setup |
| Entity platforms | Entity implementations | Frequently |
| `services.yaml` | Service definitions | When adding services |

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_config_flow.py
```

### Run Specific Test Function

```bash
pytest tests/test_config_flow.py::test_user_flow
```

### Run with Coverage

```bash
pytest --cov=custom_components.pixoo --cov-report=html
open htmlcov/index.html  # View coverage report
```

### Run with Verbose Output

```bash
pytest -vv
```

### Watch Mode (Re-run on File Changes)

```bash
# Install pytest-watch
uv pip install pytest-watch

# Run in watch mode
ptw
```

## Manual Testing

### 1. Start Home Assistant Development Server

```bash
# From repository root
hass -c config --debug
```

Access at: http://localhost:8123

### 2. Add Pixoo Device

**Via SSDP Discovery**:
1. Navigate to Configuration → Integrations
2. Click "+ Add Integration"
3. Search for "Pixoo"
4. Select discovered device
5. Confirm and configure

**Manual Entry**:
1. Configuration → Integrations → "+ Add Integration"
2. Search for "Pixoo"
3. Select "Configure Manually"
4. Enter device IP address (e.g., `192.168.1.100`)
5. Confirm

### 3. Test Entity Platforms

**Light Platform**:
```yaml
# In Developer Tools → Services
service: light.turn_on
target:
  entity_id: light.pixoo_bedroom
data:
  brightness: 128
```

**Number Platform**:
```yaml
service: number.set_value
target:
  entity_id: number.pixoo_bedroom_timer_minutes
data:
  value: 5
```

**Service Calls**:
```yaml
service: pixoo.display_image
data:
  entity_id: light.pixoo_bedroom
  url: "http://example.com/test.jpg"
```

### 4. Check Logs

```bash
# View real-time logs
tail -f config/home-assistant.log | grep pixoo

# Or in HA UI: Configuration → Logs
```

### 5. Test with Physical Device

Find your Pixoo device IP:

```bash
# Option 1: Check router DHCP leases

# Option 2: Use nmap
nmap -p 80 192.168.1.0/24 | grep -B 4 "Divoom"

# Option 3: Use pixooasync discovery (if implemented)
python -c "from pixooasync import discover_devices; print(discover_devices())"
```

Test connectivity:

```bash
# Ping device
ping 192.168.1.100

# Test HTTP endpoint
curl http://192.168.1.100/post
```

## Common Tasks

### Add New Entity

1. **Define entity class** in appropriate platform file (e.g., `sensor.py`):

```python
class PixooWeatherSensor(PixooEntity, SensorEntity):
    """Weather condition sensor."""
    
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_name = "Weather"
        self._attr_unique_id = f"{entry.entry_id}_weather"
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_icon = "mdi:weather-partly-cloudy"
    
    @property
    def native_value(self) -> str | None:
        """Return current weather."""
        return self.coordinator.data.weather_info.condition.value
```

2. **Register entity** in `async_setup_entry()`:

```python
async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Pixoo sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["system_coordinator"]
    
    entities = [
        PixooWeatherSensor(coordinator, entry),
        # ... other sensors
    ]
    
    async_add_entities(entities)
```

3. **Add tests** in `tests/test_sensor.py`:

```python
async def test_weather_sensor(hass, config_entry, mock_coordinator):
    """Test weather sensor."""
    sensor = PixooWeatherSensor(mock_coordinator, config_entry)
    
    assert sensor.name == "Weather"
    assert sensor.native_value == "sunny"
```

### Add New Service

1. **Define service schema** in `__init__.py`:

```python
SERVICE_MY_SERVICE = "my_service"

SERVICE_MY_SERVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
    vol.Required("param"): cv.string,
})
```

2. **Implement service handler**:

```python
async def async_my_service(call: ServiceCall) -> None:
    """Handle my_service call."""
    param = call.data["param"]
    entities = await async_get_entities(hass, call.data[ATTR_ENTITY_ID])
    
    for entity in entities:
        await entity.coordinator.pixoo.my_method(param)
```

3. **Register service** in `async_setup_entry()`:

```python
hass.services.async_register(
    DOMAIN,
    SERVICE_MY_SERVICE,
    async_my_service,
    schema=SERVICE_MY_SERVICE_SCHEMA,
)
```

4. **Add to `services.yaml`**:

```yaml
my_service:
  name: My Service
  description: Does something useful
  fields:
    entity_id:
      name: Entity
      required: true
      selector:
        entity:
          domain: light
          integration: pixoo
    param:
      name: Parameter
      required: true
      selector:
        text:
```

5. **Write tests**:

```python
async def test_my_service(hass, config_entry, mock_pixoo):
    """Test my_service."""
    await hass.services.async_call(
        DOMAIN,
        SERVICE_MY_SERVICE,
        {ATTR_ENTITY_ID: "light.pixoo_test", "param": "value"},
        blocking=True,
    )
    
    mock_pixoo.my_method.assert_called_once_with("value")
```

### Update Coordinator Polling

Edit `coordinator.py`:

```python
class PixooSystemCoordinator(DataUpdateCoordinator):
    """System data coordinator."""
    
    def __init__(self, hass, pixoo, entry):
        super().__init__(
            hass,
            _LOGGER,
            name=f"Pixoo System ({entry.title})",
            update_interval=timedelta(seconds=30),  # Adjust interval here
        )
        self.pixoo = pixoo
    
    async def _async_update_data(self):
        """Fetch data."""
        try:
            # Add new data fetching here
            data = await self.pixoo.get_system_config()
            return data
        except Exception as err:
            raise UpdateFailed(f"Update failed: {err}") from err
```

### Debug Issues

**Enable debug logging**:

Add to `config/configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.pixoo: debug
    pixooasync: debug
```

**Use debugger**:

1. Install debugpy: `uv pip install debugpy`
2. Add breakpoint in code: `import debugpy; debugpy.breakpoint()`
3. Attach VS Code debugger (Port 5678)

**Inspect coordinator data**:

```python
# In Developer Tools → Template
{{ state_attr('sensor.pixoo_bedroom_weather', 'extra_state_attributes') }}

# Or check coordinator data directly
{{ states.sensor.pixoo_bedroom_weather }}
```

## Troubleshooting

### Common Issues

**Issue**: "Integration not found"
- **Solution**: Check `manifest.json` domain matches directory name
- Restart HA after changes to `manifest.json`

**Issue**: "Entity not updating"
- **Solution**: Verify coordinator is running: check `coordinator.last_update_success`
- Check coordinator update interval: `coordinator.update_interval`
- Verify pixooasync method returns expected data

**Issue**: "Service call fails with error"
- **Solution**: Check service schema validation
- Verify entity_id is correct and entity is available
- Check HA logs for detailed error messages

**Issue**: "Device offline/unavailable"
- **Solution**: Ping device to verify network connectivity
- Check device IP hasn't changed (use static DHCP or static IP)
- Verify firewall allows HTTP traffic on port 80

**Issue**: "Tests fail with 'hass not initialized'"
- **Solution**: Ensure fixtures are properly set up in `conftest.py`
- Check test uses `async def` and `await` correctly
- Verify `hass` fixture is passed to test function

### Getting Help

1. **Check Documentation**:
   - `specs/001-pixoo-integration/spec.md` - Feature specification
   - `specs/001-pixoo-integration/data-model.md` - Data models
   - `specs/001-pixoo-integration/contracts/` - Service contracts

2. **Check Examples**:
   - Look at existing entity implementations
   - Reference HA core integrations (esphome, hue, nest)

3. **Ask Questions**:
   - Create GitHub Discussion for design questions
   - Open GitHub Issue for bugs
   - Check Home Assistant Developer Discord

## Development Workflow

### Typical Development Cycle

1. **Read specification**: Understand requirement in `spec.md`
2. **Write test first**: Create failing test in `tests/`
3. **Implement feature**: Write code in `custom_components/pixoo/`
4. **Run tests**: Verify tests pass: `pytest`
5. **Manual test**: Test with real device in HA
6. **Code quality**: Run ruff and mypy:
   ```bash
   ruff check custom_components/pixoo/
   mypy custom_components/pixoo/
   ```
7. **Commit changes**: Use conventional commit messages:
   ```bash
   git commit -m "feat(sensor): add weather sensor"
   ```
8. **Push and create PR**

### Code Quality Checks

```bash
# Format code
ruff format custom_components/pixoo/

# Lint code
ruff check custom_components/pixoo/ --fix

# Type check
mypy custom_components/pixoo/ --strict

# Run all checks
ruff check . && mypy . && pytest
```

## Next Steps

- Read the [Feature Specification](../spec.md)
- Review the [Data Model](../data-model.md)
- Check [Service Contracts](../contracts/)
- Start implementing!

---

**Guide Version**: 1.0  
**Last Updated**: 2025-11-10  
**Status**: ✅ Complete
