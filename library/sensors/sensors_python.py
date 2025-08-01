# turing-smart-screen-python - a Python system monitor and library for USB-C displays like Turing Smart Screen or XuanFang
# https://github.com/mathoudebine/turing-smart-screen-python/

# Copyright (C) 2021-2023  Matthieu Houdebine (mathoudebine)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# This file will use Python libraries (psutil, GPUtil, etc.) to get hardware sensors
# For all platforms (Linux, Windows, macOS) but not all HW is supported

import math
import platform
import sys
from collections import namedtuple
from enum import IntEnum, auto
from typing import Tuple

# Nvidia GPU
import GPUtil
# CPU & disk sensors
import psutil

import library.sensors.sensors as sensors
from library.log import logger

# AMD GPU on Linux
try:
    import pyamdgpuinfo
except:
    pyamdgpuinfo = None

# AMD GPU on Windows
try:
    import pyadl
except:
    pyadl = None

PNIC_BEFORE = {}


class GpuType(IntEnum):
    UNSUPPORTED = auto()
    AMD = auto()
    NVIDIA = auto()


DETECTED_GPU = GpuType.UNSUPPORTED


def is_cpu_fan(label: str) -> bool:
    # Improved CPU fan detection including common patterns
    cpu_fan_keywords = ["cpu", "proc", "processor", "core"]
    return any(keyword in label.lower() for keyword in cpu_fan_keywords)


# Function inspired of psutil/psutil/_pslinux.py:sensors_fans()
# Adapted to also get fan speed percentage instead of raw value
def sensors_fans():
    """Return hardware fans info (for CPU and other peripherals) as a
    dict including hardware label and current speed.

    Implementation notes:
    - /sys/class/hwmon looks like the most recent interface to
      retrieve this info, and this implementation relies on it
      only (old distros will probably use something else)
    - lm-sensors on Ubuntu 16.04 relies on /sys/class/hwmon
    """
    from psutil._common import bcat, cat
    import collections, glob, os

    FanEntry = collections.namedtuple('FanEntry', ['label', 'current', 'min', 'max', 'percent'])
    fans = collections.OrderedDict()

    for hwmon_dir in glob.glob('/sys/class/hwmon/hwmon*/'):
        try:
            name = cat(os.path.join(hwmon_dir, 'name')).strip()
        except (IOError, OSError):
            # Name file may not exist, skip the entry
            continue

        fan_entries = []
        for fan_input in glob.glob(os.path.join(hwmon_dir, 'fan*_input')):
            fan_label = None
            fan_min = None
            fan_max = None
            fan_percent = None
            
            # Get the fan number from the input file name
            fan_number = fan_input.split('fan')[-1].split('_')[0]
            
            # Try to get the label
            try:
                fan_label_file = os.path.join(hwmon_dir, f'fan{fan_number}_label')
                if os.path.isfile(fan_label_file):
                    fan_label = cat(fan_label_file).strip()
            except (IOError, OSError):
                pass

            # Try to get the minimum speed
            try:
                fan_min_file = os.path.join(hwmon_dir, f'fan{fan_number}_min')
                if os.path.isfile(fan_min_file):
                    fan_min = int(cat(fan_min_file).strip())
            except (IOError, OSError, ValueError):
                pass

            # Try to get the maximum speed
            try:
                fan_max_file = os.path.join(hwmon_dir, f'fan{fan_number}_max')
                if os.path.isfile(fan_max_file):
                    fan_max = int(cat(fan_max_file).strip())
            except (IOError, OSError, ValueError):
                pass

            # Get the current speed
            try:
                fan_current = int(cat(fan_input).strip())
                
                # Calculate percentage if we have min and max values
                if fan_min is not None and fan_max is not None and fan_max != fan_min:
                    fan_percent = min(100.0, max(0.0, ((fan_current - fan_min) / (fan_max - fan_min)) * 100))
                else:
                    # If we don't have min/max, use a default range (0-3000 RPM)
                    fan_percent = min(100.0, max(0.0, (fan_current / 3000.0) * 100))
                
                fan_entry = FanEntry(label=fan_label or '', current=fan_current, min=fan_min, max=fan_max, percent=fan_percent)
                fan_entries.append(fan_entry)
            except (IOError, OSError, ValueError):
                continue

        if fan_entries:
            fans[name] = fan_entries

    return fans


class Cpu(sensors.Cpu):
    @staticmethod
    def percentage(interval: float) -> float:
        try:
            return psutil.cpu_percent(interval=interval)
        except:
            return math.nan

    @staticmethod
    def frequency() -> float:
        try:
            return psutil.cpu_freq().current
        except:
            return math.nan

    @staticmethod
    def load() -> Tuple[float, float, float]:  # 1 / 5 / 15min avg (%):
        try:
            return psutil.getloadavg()
        except:
            return math.nan, math.nan, math.nan

    @staticmethod
    def temperature() -> float:
        cpu_temp = math.nan
        try:
            sensors_temps = psutil.sensors_temperatures()
            if 'coretemp' in sensors_temps:
                # Intel CPU
                cpu_temp = sensors_temps['coretemp'][0].current
            elif 'k10temp' in sensors_temps:
                # AMD CPU
                cpu_temp = sensors_temps['k10temp'][0].current
            elif 'cpu_thermal' in sensors_temps:
                # ARM CPU
                cpu_temp = sensors_temps['cpu_thermal'][0].current
            elif 'zenpower' in sensors_temps:
                # AMD CPU with zenpower (k10temp is in blacklist)
                cpu_temp = sensors_temps['zenpower'][0].current
        except:
            # psutil.sensors_temperatures not available on Windows / MacOS
            pass
        return cpu_temp

    @staticmethod
    def fan_percent(fan_name: str = None) -> float:
        try:
            fans = sensors_fans()
            if fans:
                # Convert to list to avoid "dictionary changed size during iteration" error
                fan_items = list(fans.items())
                for name, entries in fan_items:
                    for entry in entries:
                        if fan_name is not None and fan_name == "%s/%s" % (name, entry.label):
                            # Manually selected fan
                            return entry.percent
                        elif is_cpu_fan(entry.label) or is_cpu_fan(name):
                            # Auto-detected CPU fan based on label or name
                            return entry.percent
                        elif name == "amdgpu" and entry.label == "":
                            # Special case for AMD GPU - often the main fan is the CPU fan
                            # This is a heuristic that works for many systems
                            return entry.percent
        except:
            pass

        return math.nan

    @staticmethod
    def power(interval: float) -> float:
        # CPU power is not directly available through psutil
        # We can estimate it based on CPU usage and some platform-specific formulas
        try:
            # Get CPU usage percentage
            cpu_percent = psutil.cpu_percent(interval=interval)
            
            # A very rough estimation - in reality, CPU power consumption depends on many factors
            # This is just a simple estimation that returns a value based on CPU usage
            # Real implementation would require platform-specific code or external libraries
            # For a more accurate implementation, we would need to use specific hardware interfaces
            # or external tools like 'powermetrics' on macOS or '/sys/class/powercap' on Linux
            
            # Simple estimation: base power + usage-based power
            # Assume base power of 5W and up to 80W additional power at 100% usage
            base_power = 5.0
            max_additional_power = 80.0
            estimated_power = base_power + (cpu_percent / 100.0) * max_additional_power
            
            return estimated_power
        except:
            return math.nan

    @staticmethod
    def voltage(interval: float) -> float:
        # CPU voltage is not typically exposed through standard system APIs
        # It would require specific hardware interfaces or external tools
        try:
            # Try to get voltage from sensors
            sensors_temps = psutil.sensors_temperatures()
            
            # Some systems might expose voltage through sensors
            # This is system and hardware dependent
            try:
                # Check if we have sensors_misc available
                sensors_misc = None
                try:
                    sensors_misc = psutil.sensors_fans()  # This is just to test if sensors are available
                except:
                    pass
                    
                # Try to get voltage information from sensors
                if hasattr(psutil, 'sensors_temperatures'):
                    voltage_sensors = psutil.sensors_temperatures()
                    # Look for common voltage sensor names
                    for sensor_name, sensor_list in voltage_sensors.items():
                        # Common voltage sensor prefixes
                        if any(prefix in sensor_name.lower() for prefix in ['cpu', 'core', 'vcpu', 'vid']):
                            for sensor in sensor_list:
                                # Look for voltage-related labels
                                if sensor.current is not None and any(
                                    keyword in sensor.label.lower() for keyword in 
                                    ['vcore', 'cpu', 'core', 'vid', 'vtt']
                                ):
                                    # Convert to volts if needed (some sensors report in millivolts)
                                    voltage_value = sensor.current
                                    if voltage_value > 50:  # Probably in millivolts
                                        voltage_value /= 1000.0
                                    return voltage_value
                                    
                # Try to get voltage from /sys/class/hwmon on Linux
                if hasattr(os, 'listdir') and os.path.exists('/sys/class/hwmon'):
                    try:
                        # Look for CPU voltage sensors in hwmon
                        for hwmon_dir in os.listdir('/sys/class/hwmon'):
                            name_file = f'/sys/class/hwmon/{hwmon_dir}/name'
                            if os.path.exists(name_file):
                                with open(name_file, 'r') as f:
                                    name = f.read().strip().lower()
                                    # Check if this is a CPU-related sensor
                                    if any(cpu_name in name for cpu_name in ['cpu', 'core', 'k10', 'coretemp']):
                                        # Look for voltage input files
                                        for file in os.listdir(f'/sys/class/hwmon/{hwmon_dir}'):
                                            if 'in' in file and 'input' in file:
                                                # Try to identify CPU voltage files
                                                label_file = f'/sys/class/hwmon/{hwmon_dir}/{file.replace("input", "label")}'
                                                if os.path.exists(label_file):
                                                    with open(label_file, 'r') as lf:
                                                        label = lf.read().strip().lower()
                                                        if any(vlabel in label for vlabel in ['cpu', 'core', 'vcore', 'vid']):
                                                            # Read the voltage value
                                                            with open(f'/sys/class/hwmon/{hwmon_dir}/{file}', 'r') as vf:
                                                                voltage_value = int(vf.read().strip())
                                                                # Convert from millivolts to volts
                                                                return voltage_value / 1000.0
                                    elif any(v_name in name for v_name in ['it87', 'nct', 'w83', 'f71', 'f75', 'f82']):
                                        # Common voltage sensor chips
                                        for file in os.listdir(f'/sys/class/hwmon/{hwmon_dir}'):
                                            if 'in' in file and 'input' in file:
                                                label_file = f'/sys/class/hwmon/{hwmon_dir}/{file.replace("input", "label")}'
                                                if os.path.exists(label_file):
                                                    with open(label_file, 'r') as lf:
                                                        label = lf.read().strip().lower()
                                                        if any(vlabel in label for vlabel in ['cpu', 'core', 'vcore', 'vid']):
                                                            with open(f'/sys/class/hwmon/{hwmon_dir}/{file}', 'r') as vf:
                                                                voltage_value = int(vf.read().strip())
                                                                return voltage_value / 1000.0
                    except:
                        pass
                        
            except:
                pass
                
            # If we can't get voltage information, return NaN
            return math.nan
        except:
            return math.nan

    @staticmethod
    def model() -> str:
        try:
            # Try to get CPU model from psutil
            cpu_info = psutil.cpu_info() if hasattr(psutil, 'cpu_info') else None
            if cpu_info and 'brand' in cpu_info:
                return cpu_info['brand']
        except:
            pass
            
        try:
            # On Linux, try to get CPU model from /proc/cpuinfo
            if platform.system() == "Linux":
                with open('/proc/cpuinfo', 'r') as f:
                    # Look for the model name in /proc/cpuinfo
                    for line in f:
                        if line.startswith('model name'):
                            # Extract the model name after the colon
                            model_name = line.split(':', 1)[1].strip()
                            if model_name:
                                return model_name
                    
                    # If model name is not found, try to construct it from other fields
                    # This is useful for some ARM processors
                    f.seek(0)  # Reset file pointer to beginning
                    vendor_id = None
                    model = None
                    stepping = None
                    cpu_part = None
                    
                    for line in f:
                        if line.startswith('vendor_id'):
                            vendor_id = line.split(':', 1)[1].strip()
                        elif line.startswith('model'):
                            model = line.split(':', 1)[1].strip()
                        elif line.startswith('stepping'):
                            stepping = line.split(':', 1)[1].strip()
                        elif line.startswith('CPU part'):
                            cpu_part = line.split(':', 1)[1].strip()
                    
                    # Construct a model name if we have the information
                    if vendor_id and model and stepping:
                        return f"{vendor_id} Model {model} Stepping {stepping}"
                    elif cpu_part:
                        return f"ARM CPU Part {cpu_part}"
        except:
            pass
            
        try:
            # On Windows, try to get CPU model from wmic
            if platform.system() == "Windows":
                import subprocess
                result = subprocess.run(["wmic", "cpu", "get", "name"], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    # Find the first non-empty line that is not the header
                    for line in lines:
                        if line.strip() and line.strip().lower() != 'name':
                            return line.strip()
        except:
            pass
            
        try:
            # On macOS, try to get CPU model from sysctl
            if platform.system() == "Darwin":
                import subprocess
                result = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
        except:
            pass
        
        try:
            # Alternative method using platform module
            import platform
            model = platform.processor()
            if model:
                return model
        except:
            pass

        # If we can't get CPU model, return a default string
        return "Unknown CPU Model"


class Gpu(sensors.Gpu):
    @staticmethod
    def stats() -> Tuple[
        float, float, float, float, float, float, float]:
        # load (%) / used mem (%) / used mem (Mb) / total mem (Mb) / temp (°C) / power (W) / voltage (v)
        if DETECTED_GPU == GpuType.AMD:
            return GpuAmd.stats()
        elif DETECTED_GPU == GpuType.NVIDIA:
            return GpuNvidia.stats()
        else:
            return math.nan, math.nan, math.nan, math.nan, math.nan, math.nan, math.nan

    @staticmethod
    def fps() -> int:
        if DETECTED_GPU == GpuType.AMD:
            return GpuAmd.fps()
        elif DETECTED_GPU == GpuType.NVIDIA:
            return GpuNvidia.fps()
        else:
            return -1

    @staticmethod
    def fan_percent() -> float:
        if DETECTED_GPU == GpuType.AMD:
            return GpuAmd.fan_percent()
        elif DETECTED_GPU == GpuType.NVIDIA:
            return GpuNvidia.fan_percent()
        else:
            return math.nan

    @staticmethod
    def frequency() -> float:
        if DETECTED_GPU == GpuType.AMD:
            return GpuAmd.frequency()
        elif DETECTED_GPU == GpuType.NVIDIA:
            return GpuNvidia.frequency()
        else:
            return math.nan

    @staticmethod
    def is_available() -> bool:
        global DETECTED_GPU
        # Always use Nvidia GPU if available
        if GpuNvidia.is_available():
            logger.info("Detected Nvidia GPU(s)")
            DETECTED_GPU = GpuType.NVIDIA
        # Otherwise, use the AMD GPU / APU if available
        elif GpuAmd.is_available():
            logger.info("Detected AMD GPU(s)")
            DETECTED_GPU = GpuType.AMD
        else:
            logger.warning("No supported GPU found")
            DETECTED_GPU = GpuType.UNSUPPORTED
            if sys.version_info >= (3, 11) and (platform.system() == "Linux" or platform.system() == "Darwin"):
                logger.warning("If you have an AMD GPU, you may need to install some  libraries manually: see "
                               "https://github.com/mathoudebine/turing-smart-screen-python/wiki/Troubleshooting#linux--macos-no-supported-gpu-found-with-an-amd-gpu-and-python-311")

        return DETECTED_GPU != GpuType.UNSUPPORTED


class GpuNvidia(sensors.Gpu):
    @staticmethod
    def stats() -> Tuple[
        float, float, float, float, float, float, float]:
        # load (%) / used mem (%) / used mem (Mb) / total mem (Mb) / temp (°C) / power (W) / voltage (v)
        # Unlike other sensors, Nvidia GPU with GPUtil pulls in all the stats at once
        nvidia_gpus = GPUtil.getGPUs()

        try:
            memory_used_all = [item.memoryUsed for item in nvidia_gpus]
            memory_used_mb = sum(memory_used_all) / len(memory_used_all)
        except:
            memory_used_mb = math.nan

        try:
            memory_total_all = [item.memoryTotal for item in nvidia_gpus]
            memory_total_mb = sum(memory_total_all) / len(memory_total_all)
        except:
            memory_total_mb = math.nan

        try:
            memory_percentage = (memory_used_mb / memory_total_mb) * 100
        except:
            memory_percentage = math.nan

        try:
            load_all = [item.load for item in nvidia_gpus]
            load = (sum(load_all) / len(load_all)) * 100
        except:
            load = math.nan

        try:
            temperature_all = [item.temperature for item in nvidia_gpus]
            temperature = sum(temperature_all) / len(temperature_all)
        except:
            temperature = math.nan

        # Try to get power and voltage data (may not be available on all systems)
        try:
            power_all = [item.power for item in nvidia_gpus if item.power is not None]
            power = sum(power_all) / len(power_all) if power_all else math.nan
        except:
            power = math.nan

        try:
            # Voltage is not typically available through GPUtil, set to NaN
            voltage = math.nan
        except:
            voltage = math.nan

        return load, memory_percentage, memory_used_mb, memory_total_mb, temperature, power, voltage

    @staticmethod
    def fps() -> int:
        # Not supported by Python libraries
        return -1

    @staticmethod
    def fan_percent() -> float:
        try:
            fans = sensors_fans()
            if fans:
                # Convert to list to avoid "dictionary changed size during iteration" error
                fan_items = list(fans.items())
                for name, entries in fan_items:
                    for entry in entries:
                        if "gpu" in (entry.label.lower() or name.lower()):
                            return entry.percent
        except:
            pass

        return math.nan

    @staticmethod
    def frequency() -> float:
        # Not supported by Python libraries
        return math.nan

    @staticmethod
    def is_available() -> bool:
        try:
            return len(GPUtil.getGPUs()) > 0
        except:
            return False


class GpuAmd(sensors.Gpu):
    @staticmethod
    def stats() -> Tuple[
        float, float, float, float, float, float, float]:
        # load (%) / used mem (%) / used mem (Mb) / total mem (Mb) / temp (°C) / power (W) / voltage (v)
        if pyamdgpuinfo:
            # Unlike other sensors, AMD GPU with pyamdgpuinfo pulls in all the stats at once
            pyamdgpuinfo.detect_gpus()
            amd_gpu = pyamdgpuinfo.get_gpu(0)

            try:
                memory_used_bytes = amd_gpu.query_vram_usage()
                memory_used = memory_used_bytes / 1024 / 1024
            except:
                memory_used_bytes = math.nan
                memory_used = math.nan

            try:
                memory_total_bytes = amd_gpu.memory_info["vram_size"]
                memory_total = memory_total_bytes / 1024 / 1024
            except:
                memory_total_bytes = math.nan
                memory_total = math.nan

            try:
                memory_percentage = (memory_used_bytes / memory_total_bytes) * 100
            except:
                memory_percentage = math.nan

            try:
                load = amd_gpu.query_load() * 100
            except:
                load = math.nan

            try:
                temperature = amd_gpu.query_temperature()
            except:
                temperature = math.nan

            try:
                graphics_power = amd_gpu.query_power()
            except:
                graphics_power = math.nan

            try:
                graphics_voltage = amd_gpu.query_graphics_voltage()
            except:
                graphics_voltage = math.nan

            return load, memory_percentage, memory_used, memory_total, temperature, graphics_power, graphics_voltage
        elif pyadl:
            amd_gpu = pyadl.ADLManager.getInstance().getDevices()[0]

            try:
                load = amd_gpu.getCurrentUsage()
            except:
                load = math.nan

            try:
                temperature = amd_gpu.getCurrentTemperature()
            except:
                temperature = math.nan

            # GPU memory data not supported by pyadl
            return load, math.nan, math.nan, math.nan, temperature, math.nan, math.nan

    @staticmethod
    def fps() -> int:
        # Not supported by Python libraries
        return -1

    @staticmethod
    def fan_percent() -> float:
        try:
            # Try with psutil fans
            fans = sensors_fans()
            if fans:
                # Convert to list to avoid "dictionary changed size during iteration" error
                fan_items = list(fans.items())
                for name, entries in fan_items:
                    for entry in entries:
                        if "gpu" in (entry.label.lower() or name.lower()):
                            return entry.percent

            # Try with pyadl if psutil did not find GPU fan
            if pyadl:
                return pyadl.ADLManager.getInstance().getDevices()[0].getCurrentFanSpeed(
                    pyadl.ADL_DEVICE_FAN_SPEED_TYPE_PERCENTAGE)
        except:
            pass

        return math.nan

    @staticmethod
    def frequency() -> float:
        try:
            if pyamdgpuinfo:
                pyamdgpuinfo.detect_gpus()
                return pyamdgpuinfo.get_gpu(0).query_sclk() / 1000000
            elif pyadl:
                return pyadl.ADLManager.getInstance().getDevices()[0].getCurrentEngineClock()
            else:
                return math.nan
        except:
            return math.nan

    @staticmethod
    def is_available() -> bool:
        try:
            if pyamdgpuinfo and pyamdgpuinfo.detect_gpus() > 0:
                return True
            elif pyadl and len(pyadl.ADLManager.getInstance().getDevices()) > 0:
                return True
            else:
                return False
        except:
            return False


class Memory(sensors.Memory):
    @staticmethod
    def swap_percent() -> float:
        try:
            return psutil.swap_memory().percent
        except:
            return math.nan

    @staticmethod
    def virtual_percent() -> float:
        try:
            return psutil.virtual_memory().percent
        except:
            return math.nan

    @staticmethod
    def virtual_used() -> int:  # In bytes
        try:
            # Do not use psutil.virtual_memory().used: from https://psutil.readthedocs.io/en/latest/#memory
            # "It is calculated differently depending on the platform and designed for informational purposes only"
            return psutil.virtual_memory().total - psutil.virtual_memory().available
        except:
            return -1

    @staticmethod
    def virtual_free() -> int:  # In bytes
        try:
            # Do not use psutil.virtual_memory().free: from https://psutil.readthedocs.io/en/latest/#memory
            # "note that this doesn’t reflect the actual memory available (use available instead)."
            return psutil.virtual_memory().available
        except:
            return -1


class Disk(sensors.Disk):
    @staticmethod
    def disk_usage_percent() -> float:
        try:
            return psutil.disk_usage("/").percent
        except:
            return math.nan

    @staticmethod
    def disk_used() -> int:  # In bytes
        try:
            return psutil.disk_usage("/").used
        except:
            return -1

    @staticmethod
    def disk_free() -> int:  # In bytes
        try:
            return psutil.disk_usage("/").free
        except:
            return -1


class Net(sensors.Net):
    @staticmethod
    def stats(if_name, interval) -> Tuple[
        int, int, int, int]:  # up rate (B/s), uploaded (B), dl rate (B/s), downloaded (B)
        try:
            # Get current counters
            pnic_after = psutil.net_io_counters(pernic=True)

            upload_rate = 0
            uploaded = 0
            download_rate = 0
            downloaded = 0

            if if_name != "":
                if if_name in pnic_after:
                    try:
                        upload_rate = (pnic_after[if_name].bytes_sent - PNIC_BEFORE[if_name].bytes_sent) / interval
                        uploaded = pnic_after[if_name].bytes_sent
                        download_rate = (pnic_after[if_name].bytes_recv - PNIC_BEFORE[if_name].bytes_recv) / interval
                        downloaded = pnic_after[if_name].bytes_recv
                    except:
                        # Interface might not be in PNIC_BEFORE for now
                        pass

                    PNIC_BEFORE.update({if_name: pnic_after[if_name]})
                else:
                    logger.warning("Network interface '%s' not found. Check names in config.yaml." % if_name)

            return upload_rate, uploaded, download_rate, downloaded
        except:
            return -1, -1, -1, -1
