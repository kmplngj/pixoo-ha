#!/usr/bin/env python3
"""
Fix optimistic entities to use _attr_available instead of available property override.

This script modifies select.py, number.py, and switch.py to:
1. Remove the available property override
2. Add _attr_available = True in __init__

According to HA best practices (from DeepWiki research):
- Set _attr_available = True in __init__ for optimistic entities
- Don't override available property - let base class use _attr_available
"""

import re
from pathlib import Path


def fix_file(filepath: Path, class_patterns: list[str]):
    """Fix a single file by replacing available property with _attr_available."""
    print(f"Processing {filepath.name}...")
    content = filepath.read_text()
    original = content
    
    # Remove available property overrides
    # Pattern: @property\n    def available(self) -> bool:\n        """..."""\n        return True  # ...
    content = re.sub(
        r'    @property\n    def available\(self\) -> bool:\n        """[^"]*"""\n        return True  # [^\n]*\n\n',
        '',
        content
    )
    
    # For each class, add _attr_available = True after super().__init__()
    for class_name in class_patterns:
        # Find the __init__ method for this class
        # Pattern: class ClassName(...):\n...\n    def __init__(...):...\n        super().__init__(...)\n
        pattern = (
            rf'(class {class_name}\([^)]+\):.*?'
            r'def __init__\([^)]+\)[^:]*:.*?'
            r'super\(\).__init__\([^)]+\)\n)'
        )
        
        def add_attr(match):
            init_code = match.group(1)
            # Check if _attr_available already exists
            if '_attr_available' in init_code:
                return init_code
            # Add _attr_available = True after super().__init__()
            return init_code + '        self._attr_available = True\n'
        
        content = re.sub(pattern, add_attr, content, flags=re.DOTALL)
    
    if content != original:
        filepath.write_text(content)
        print(f"  ✓ Fixed {filepath.name}")
        return True
    else:
        print(f"  ℹ No changes needed for {filepath.name}")
        return False


def main():
    base_dir = Path(__file__).parent / "custom_components" / "pixoo"
    
    files_to_fix = {
        "select.py": [
            "PixooChannelSelect",
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
    
    fixed_count = 0
    for filename, classes in files_to_fix.items():
        filepath = base_dir / filename
        if fix_file(filepath, classes):
            fixed_count += 1
    
    print(f"\n✓ Fixed {fixed_count} files")


if __name__ == "__main__":
    main()
