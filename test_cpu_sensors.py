
import math
from library.sensors import sensors_python, sensors_stub_static, sensors_stub_random

print("Python sensors:")
print("  CPU Power:", sensors_python.Cpu.power(1))
print("  CPU Voltage:", sensors_python.Cpu.voltage(1))

print("Static sensors:")
print("  CPU Power:", sensors_stub_static.Cpu.power(1))
print("  CPU Voltage:", sensors_stub_static.Cpu.voltage(1))

print("Random sensors:")
print("  CPU Power:", sensors_stub_random.Cpu.power(1))
print("  CPU Voltage:", sensors_stub_random.Cpu.voltage(1))

