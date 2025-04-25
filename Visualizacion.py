import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("internet_quality.csv", parse_dates=["timestamp"])
df.set_index("timestamp", inplace=True)

# Gráfico de latencia
plt.figure()
df["rtt_ms"].plot(title="Latencia (RTT) a 8.8.8.8")
plt.ylabel("ms")
plt.show()

# Gráfico de velocidad
plt.figure()
df[["download_mbps", "upload_mbps"]].plot(title="Ancho de banda")
plt.ylabel("Mbps")
plt.show()

