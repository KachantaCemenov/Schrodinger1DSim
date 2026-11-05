import json
from dataclasses import asdict
from pathlib import Path

from Simulation import SimulationConfig


CONFIG_FILE = Path.home() / "Schrodinger1DSim" / "configurations.json"


def ReadConfigurations():
    if not CONFIG_FILE.exists():
        return {}

    with CONFIG_FILE.open("r", encoding="utf-8") as file:
        configs = json.load(file)

    if not isinstance(configs, dict):
        raise ValueError("The saved configuration file must contain named presets.")

    return configs


def SaveConfiguration(name, config):
    configs = ReadConfigurations()
    configs[name] = asdict(config)

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Replace the old file only after the new JSON has been written.
    temp_file = CONFIG_FILE.with_suffix(".tmp")
    with temp_file.open("w", encoding="utf-8") as file:
        json.dump(configs, file, indent=2, allow_nan=False)

    temp_file.replace(CONFIG_FILE)


def LoadConfiguration(name):
    configs = ReadConfigurations()
    if name not in configs:
        raise ValueError(f"No saved configuration named {name!r}.")

    return SimulationConfig(**configs[name])