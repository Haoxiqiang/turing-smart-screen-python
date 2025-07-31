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

# This file will use static data instead of real hardware sensors
# Useful for theme editor
# For all platforms (Linux, Windows, macOS)

from typing import Tuple

import library.sensors.sensors as sensors

# Define here global static values that will be applied to all sensors of the same type
PERCENTAGE_SENSOR_VALUE = 50.0
TEMPERATURE_SENSOR_VALUE = 67.3

# Define other sensors
CPU_FREQ_MHZ = 2400.0
CPU_POWER = 65.0
CPU_VOLTAGE = 1.2
CPU_MODEL = "Intel Core i7-11700K @ 3.60GHz"
DISK_TOTAL_SIZE_GB = 1000
MEMORY_TOTAL_SIZE_GB = 64
GPU_MEM_TOTAL_SIZE_GB = 32
NETWORK_SPEED_BYTES = 1061000000
GPU_FPS = 120
GPU_FREQ_MHZ = 1500.0
GPU_POWER = 350.0
GPU_VOLTAGE = 1.25


class Cpu(sensors.Cpu):
    @staticmethod
    def percentage(interval: float) -> float:
        return PERCENTAGE_SENSOR_VALUE

    @staticmethod
    def frequency() -> float:
        return CPU_FREQ_MHZ

    @staticmethod
    def load() -> Tuple[float, float, float]:  # 1 / 5 / 15min avg (%):
        return PERCENTAGE_SENSOR_VALUE, PERCENTAGE_SENSOR_VALUE, PERCENTAGE_SENSOR_VALUE

    @staticmethod
    def temperature() -> float:
        return TEMPERATURE_SENSOR_VALUE

    @staticmethod
    def fan_percent(fan_name: str = None) -> float:
        return PERCENTAGE_SENSOR_VALUE

    @staticmethod
    def power(interval: float) -> float:
        return CPU_POWER

    @staticmethod
    def voltage(interval: float) -> float:
        return CPU_VOLTAGE

    @staticmethod
    def model() -> str:
        return CPU_MODEL


class Gpu(sensors.Gpu):
    @staticmethod
    def stats() -> Tuple[
        float, float, float, float, float, float, float]:
        # load (%) / used mem (%) / used mem (Mb) / total mem (Mb) / temp (°C) / power (W) / voltage (v)
        return (PERCENTAGE_SENSOR_VALUE,
                PERCENTAGE_SENSOR_VALUE,
                GPU_MEM_TOTAL_SIZE_GB / 100 * PERCENTAGE_SENSOR_VALUE * 1024,
                GPU_MEM_TOTAL_SIZE_GB * 1024,
                TEMPERATURE_SENSOR_VALUE,
                GPU_POWER,
                GPU_VOLTAGE)

    @staticmethod
    def fps() -> int:
        return GPU_FPS

    @staticmethod
    def fan_percent() -> float:
        return PERCENTAGE_SENSOR_VALUE

    @staticmethod
    def frequency() -> float:
        return GPU_FREQ_MHZ

    @staticmethod
    def is_available() -> bool:
        return True


class Memory(sensors.Memory):
    @staticmethod
    def swap_percent() -> float:
        return PERCENTAGE_SENSOR_VALUE

    @staticmethod
    def virtual_percent() -> float:
        return PERCENTAGE_SENSOR_VALUE

    @staticmethod
    def virtual_used() -> int:  # In bytes
        return MEMORY_TOTAL_SIZE_GB * 1024 * 1024 * 1024 / 100 * PERCENTAGE_SENSOR_VALUE

    @staticmethod
    def virtual_free() -> int:  # In bytes
        return MEMORY_TOTAL_SIZE_GB * 1024 * 1024 * 1024 / 100 * (100 - PERCENTAGE_SENSOR_VALUE)


class Disk(sensors.Disk):
    @staticmethod
    def disk_usage_percent() -> float:
        return PERCENTAGE_SENSOR_VALUE

    @staticmethod
    def disk_used() -> int:  # In bytes
        return int(DISK_TOTAL_SIZE_GB * 1024 * 1024 * 1024 / 100 * PERCENTAGE_SENSOR_VALUE)

    @staticmethod
    def disk_free() -> int:  # In bytes
        return int(DISK_TOTAL_SIZE_GB * 1024 * 1024 * 1024 / 100 * (100 - PERCENTAGE_SENSOR_VALUE))


class Net(sensors.Net):
    @staticmethod
    def stats(if_name, interval) -> Tuple[
        int, int, int, int]:  # up rate (B/s), uploaded (B), dl rate (B/s), downloaded (B)
        return NETWORK_SPEED_BYTES, NETWORK_SPEED_BYTES, NETWORK_SPEED_BYTES, NETWORK_SPEED_BYTES