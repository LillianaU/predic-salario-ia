import sys
import os
import importlib.metadata
from pathlib import Path

REQUIRED_PYTHON_VERSION = (3, 8)
REQUIRED_PACKAGES = {
    "streamlit": "1.0.0",
    "pandas": "1.3.0",
    "requests": "2.25.0",
    "python-dotenv": "0.19.0",
    "scikit-learn": "1.0.0",
    "plotly": "5.0.0",
    "joblib": "1.0.0",
    "numpy": "1.21.0",
}

SCRAPER_DIR = Path(__file__).resolve().parent / "src" / "scraper"
ENV_PATH = Path(__file__).resolve().parent / ".env"


def check_python_version():
    current = sys.version_info[:2]
    ok = current >= REQUIRED_PYTHON_VERSION
    label = "OK" if ok else "ERROR"
    print(f"[{label}] Python {current[0]}.{current[1]} (requerido >= {REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]})")
    return ok


def check_packages():
    all_ok = True
    for pkg, min_ver in REQUIRED_PACKAGES.items():
        try:
            ver = importlib.metadata.version(pkg)
            installed = tuple(map(int, ver.split(".")[:3]))
            required = tuple(map(int, min_ver.split(".")[:3]))
            if installed >= required:
                print(f"[OK] {pkg} == {ver}")
            else:
                print(f"[WARN] {pkg} == {ver} (requerido >= {min_ver})")
                all_ok = False
        except importlib.metadata.PackageNotFoundError:
            print(f"[ERROR] {pkg} no instalado")
            all_ok = False
    return all_ok


def check_directories():
    dirs = [
        "data/raw", "data/processed", "models", "logs",
        "src/interfaces", "src/scraper", "src/data",
        "src/models", "src/visualization", "src/utils",
    ]
    all_ok = True
    for d in dirs:
        p = Path(d)
        if p.exists():
            print(f"[OK] Directorio {d}/ existe")
        else:
            print(f"[WARN] Directorio {d}/ no existe")
            all_ok = False
    return all_ok


def check_playwright():
    pw_script = SCRAPER_DIR / "playwright_scraper.py"
    if not pw_script.exists():
        print("[WARN] src/scraper/playwright_scraper.py no encontrado")
        return False

    content = pw_script.read_text(encoding="utf-8")
    has_thread = "threading.Thread" in content
    has_sync = "sync_playwright" in content

    if has_thread and has_sync:
        print("[OK] Playwright configurado con hilo separado (compatibile con Streamlit)")
        return True
    if has_sync and not has_thread:
        print("[WARN] Playwright sin threading — fallara en Streamlit. Ejecuta el fix.")
        return False
    print("[OK] Playwright scraper detectado")
    return True


def check_data():
    training = Path("data/processed/training_data.csv")
    model = Path("models/salary_predictor.pkl")
    has_training = training.exists()
    has_model = model.exists()

    if has_training:
        lines = training.read_text(encoding="utf-8").count("\n")
        print(f"[OK] Dataset: {lines} registros en training_data.csv")
    else:
        print("[WARN] training_data.csv no encontrado — ejecuta scraping primero")

    if has_model:
        size_kb = model.stat().st_size / 1024
        print(f"[OK] Modelo entrenado: {size_kb:.0f} KB")
    else:
        print("[WARN] Modelo no encontrado — se entrenará automáticamente")

    return has_training and has_model


def main():
    print("=" * 60)
    print("  VERIFICACIÓN DE ENTORNO — PredicSalario IA")
    print("=" * 60)
    print()

    checks = [
        ("Python", check_python_version),
        ("Paquetes", check_packages),
        ("Directorios", check_directories),
        ("Playwright", check_playwright),
        ("Datos", check_data),
    ]

    results = []
    for name, fn in checks:
        print(f"\n--- {name} ---")
        results.append(fn())

    print()
    print("=" * 60)
    if all(results):
        print("  [OK] Entorno listo. Ejecuta: streamlit run app.py")
    else:
        print("  [WARN] Revisa los warnings anteriores.")
    print("=" * 60)

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
