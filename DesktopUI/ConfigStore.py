import json
from dataclasses import asdict
from pathlib import Path
import os

from Simulation import SimulationConfig

#Save to %LOCALAPPDATA%\Schrodinger1DSim
APP_DATA_DIR = Path(os.environ["LOCALAPPDATA"]) / "Schrodinger1DSim"
CONFIG_FILE = APP_DATA_DIR / "configurations.json"
BENCHMARK_CONFIG_FILE = CONFIG_FILE.with_name("benchmark_configurations.json")

DEFAULT_CONFIG_DIR = Path(__file__).resolve().parent / "DefaultConfigurations"

#Copy configs from DEFAULT_CONFIG_DIR to destination in (CONFIG_FILE, BENCHMARK_CONFIG_FILE)
def InstallDefaultConfigurations():
    APP_DATA_DIR.mkdir(parents = True, exist_ok = True)

    for destination in (CONFIG_FILE, BENCHMARK_CONFIG_FILE):
        #Dont touch configurations already belonging to the user
        if destination.exists():
            continue

        source = DEFAULT_CONFIG_DIR / destination.name

        with source.open("r", encoding = "utf-8-sig") as file:
            configs = json.load(file)

        if not isinstance(configs, dict):
            raise ValueError(f"Default configurations must be a dictionary: {source}")

        contents = json.dumps(configs, indent = 2, allow_nan = False)
        temporary_path = destination.with_suffix(".tmp")
        temporary_path.write_text(contents, encoding = "utf-8")
        temporary_path.replace(destination)

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


def ReadBenchmarkConfigurations():
    if not BENCHMARK_CONFIG_FILE.exists():
        return {}
    with BENCHMARK_CONFIG_FILE.open("r", encoding = "utf-8") as f:
        configs = json.load(f)

    if not isinstance(configs, dict):
        raise ValueError("Could not read dict out of json.\nMissing a name?")
    return configs

def SaveBenchmarkConfiguration(name, run):
    configs = ReadBenchmarkConfigurations()
    configs[name] = run

    #serialize
    contents = json.dumps(configs, indent = 2, allow_nan = False) #Never allow nan

    BENCHMARK_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_file = BENCHMARK_CONFIG_FILE.with_suffix(".tmp")
    temp_file.write_text(contents, encoding="utf-8")
    temp_file.replace(BENCHMARK_CONFIG_FILE)

