import csv
import time
from datetime import datetime
import ping3
from speedtest import Speedtest, ConfigRetrievalError, SpeedtestBestServerFailure
import subprocess
import json

def test_speed_cli():
    """Fallback: invoca speedtest-cli como ejecutable."""
    try:
        out = subprocess.check_output(
            ["speedtest-cli", "--json"],
            stderr=subprocess.DEVNULL,
            timeout=30
        )
        data = json.loads(out)
        down = data.get("download", 0) / 1e6  # a Mbps
        up   = data.get("upload",   0) / 1e6
        return down, up
    except Exception as e:
        print(f"⚠️ Fallback speedtest-cli falló: {e}")
        return None, None

def medir_calidad():
    # 1) Latencia y pérdida con ping3
    host = "8.8.8.8"
    try:
        ping3.EXCEPTIONS = True
        rtt = ping3.ping(host, unit="ms")
        loss = 0 if rtt is not None else 100
    except Exception:
        rtt, loss = None, 100

    # 2) Test de velocidad con la API de speedtest
    down = up = None
    try:
        # fijamos timeout global al crear el objeto (en segundos)
        st = Speedtest(secure=True, timeout=10)
        st.get_servers()            # ya no pasamos timeout aquí
        st.get_best_server()        # puede lanzar SpeedtestBestServerFailure
        down = st.download() / 1e6
        up   = st.upload()   / 1e6
    except (ConfigRetrievalError, SpeedtestBestServerFailure) as e:
        print(f"⚠️ Speedtest API falló: {e}")
        down, up = test_speed_cli()  # tu fallback al CLI
    except Exception as e:
        # atrapa cualquier otro fallo inesperado de la API
        print(f"⚠️ Error inesperado en Speedtest API: {e}")
        down, up = test_speed_cli()

    # 3) Timestamp y escritura en CSV
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fila = [now, rtt, loss, down, up]
    with open("internet_quality.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fila)

    # 4) Log en consola (mostrar — si es None)
    def fmt(x, unit=""):
        return f"{x:.2f}{unit}" if isinstance(x, (int, float)) else "—"
    print(f"[{now}] RTT={fmt(rtt,' ms')} | Loss={loss}% | ↓ {fmt(down,' Mbps')} | ↑ {fmt(up,' Mbps')}")

# --- CSV header si no existe ---
import pandas as pd
try:
    pd.read_csv("internet_quality.csv")
except (FileNotFoundError, pd.errors.EmptyDataError):
    with open("internet_quality.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["timestamp", "rtt_ms", "loss_%", "download_mbps", "upload_mbps"])

# --- Scheduler cada 15 minutos ---
import schedule

schedule.every(0.20).minutes.do(medir_calidad)

if __name__ == "__main__":
    print("Iniciando monitor de calidad de Internet (Ctrl+C para parar)…")
    while True:
        schedule.run_pending()
        time.sleep(1)
