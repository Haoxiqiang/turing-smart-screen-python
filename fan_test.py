
#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from library.sensors.sensors_python import Cpu, Gpu, sensors_fans

print("=== Fan Sensor Information ===")

# Test CPU fan detection
print("\n1. CPU Fan Detection:")
cpu_fan = Cpu.fan_percent()
print(f"   Detected CPU fan speed: {cpu_fan}%")

# Show all available fans
print("\n2. All Available Fans:")
try:
    fans = sensors_fans()
    if fans:
        for name, entries in fans.items():
            print(f"   {name}:")
            for entry in entries:
                print(f"     Label: \"{entry.label}\", Current: {entry.current}, Percent: {entry.percent:.1f}%")
    else:
        print("   No fans detected")
except Exception as e:
    print(f"   Error getting fans: {e}")

# Test GPU detection
print("\n3. GPU Information:")
if Gpu.is_available():
    gpu_fan = Gpu.fan_percent()
    print(f"   Detected GPU fan speed: {gpu_fan}%")
else:
    print("   No supported GPU detected")

