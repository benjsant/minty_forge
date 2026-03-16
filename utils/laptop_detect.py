"""Detection de PC portable via sysfs (pas de paquet externe requis)."""
from pathlib import Path


def is_laptop():
    """Detecte un laptop par la presence d'une batterie dans /sys/class/power_supply/.
    Retourne (bool, dict) : (est_laptop, infos_batterie)."""
    power_supply = Path("/sys/class/power_supply")
    if not power_supply.exists():
        return False, {}
    for supply in sorted(power_supply.iterdir()):
        type_file = supply / "type"
        if type_file.exists() and type_file.read_text().strip() == "Battery":
            info = {"name": supply.name}
            for key in ("capacity", "status", "cycle_count"):
                f = supply / key
                if f.exists():
                    val = f.read_text().strip()
                    info[key] = int(val) if val.isdigit() else val
            return True, info
    return False, {}
