#!/usr/bin/env python3
"""Fix event_sourcing.py syntax errors."""

import re

with open('smolclaw/cognitive/event_sourcing.py', 'r') as f:
    content = f.read()

# Fix unclosed strings - look for the pattern and close it
lines = content.split('\n')
fixed_lines = []

for i, line in enumerate(lines):
    # Fix unclosed "plan_generated strings
    if 'self.event_type = "plan_generated' in line and not line.strip().endswith('")'):
        fixed_lines.append('        self.event_type = "plan_generated"')
    elif 'PLAN_GENERATED = "plan_generated' in line and not line.strip().endswith('")'):
        fixed_lines.append('    PLAN_GENERATED = "plan_generated"')
    # Fix corrupted fold method
    elif 'def fold(self, initial, reducer):' in line:
        fixed_lines.append('    def fold(self, initial, reducer):')
        # Skip next few corrupted lines
        skip = 0
    else:
        # Skip corrupted lines after fold
        if 'def fold' in ''.join(lines[max(0,i-2):i]) and ('initial: T' in line or 'reducer: Callable' in line or ') -> T:' in line):
            continue
        fixed_lines.append(line)

with open('smolclaw/cognitive/event_sourcing.py', 'w') as f:
    f.write('\n'.join(fixed_lines))

print('✅ Fixed event_sourcing.py')
