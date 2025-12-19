#!/usr/bin/env python3
"""
Final fix for optimistic entity availability.

According to HA CoordinatorEntity implementation, _attr_available is NOT
automatically used. We must override the available property.

This script adds:
    @property
    def available(self) -> bool:
        return self._attr_available

after each __init__ method in optimistic entities.
"""

import re
from pathlib import Path

def add_available_property_after_init(content: str, class_name: str) -> str:
    """Add available property after __init__ if not already present."""
    
    # Pattern: Find class definition and __init__ method
    # We want to add the property right after the __init__ method closes
    pattern = rf'(class {class_name}\([^)]+\):.*?def __init__\([^)]+\)[^:]*:.*?self\._attr_name = "[^"]+"\n)'
    
    property_code = '''
    @property
    def available(self) -> bool:
        """Optimistic entities are always available."""
        return self._attr_available

'''
    
    def replacer(match):
        init_block = match.group(1)
        # Check if available property already exists in this class
        # Look ahead to see if @property\n    def available appears before next class or EOF
        next_part_start = match.end()
        next_300_chars = content[next_part_start:next_part_start+300]
        if '@property\n    def available' in next_300_chars:
            return init_block  # Already has the property
        return init_block + property_code
    
    result = re.sub(pattern, replacer, content, flags=re.DOTALL)
    return result

def main():
    base_dir = Path(__file__).parent / "custom_components" / "pixoo"
    
    # Optimistic entities that need available property
    optimistic_classes = {
        "select.py": [
            "PixooClockFaceSelect",
            "PixooVisualizerSelect",
            "PixooCustomPageSelect",
        ],
        "number.py": [
            "PixooTimerMinutesNumber",
            "PixooTimerSecondsNumber",
            "PixooAlarmHourNumber",
            "PixooAlarmMinuteNumber",
            "PixooScoreboardRedNumber",
            "PixooScoreboardBlueNumber",
        ],
        "switch.py": [
            "PixooTimerSwitch",
            "PixooAlarmSwitch",
            "PixooStopwatchSwitch",
            "PixooScoreboardSwitch",
            "PixooNoiseMeterSwitch",
        ],
    }
    
    for filename, classes in optimistic_classes.items():
        filepath = base_dir / filename
        print(f"Processing {filename}...")
        content = filepath.read_text()
        original = content
        
        for class_name in classes:
            content = add_available_property_after_init(content, class_name)
        
        if content != original:
            filepath.write_text(content)
            print(f"  ✓ Added available properties to {len(classes)} classes")
        else:
            print(f"  ℹ No changes needed (properties already exist)")
    
    print("\n✓ Complete")

if __name__ == "__main__":
    main()
