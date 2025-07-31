
#!/usr/bin/env python3

import platform
from library.sensors.sensors_python import Cpu

print("Platform:", platform.system())
print("CPU Model:", Cpu.model())

if platform.system() == "Linux":
    print("\nChecking /proc/cpuinfo for model name:")
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith("model name"):
                    print("  ", line.strip())
                    break
    except Exception as e:
        print("  Error reading /proc/cpuinfo:", e)

