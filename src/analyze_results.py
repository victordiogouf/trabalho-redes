import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

with open('../input.txt', 'r', encoding='utf-8') as f:
    input_data = f.read()

file_size = len(input_data.encode('utf-8'))
print(f"Tamanho do arquivo de entrada: {file_size} bytes")

min_packets = 10000
packet_size = max(1, file_size // min_packets)  
print(f"Tamanho de cada pacote: {packet_size} bytes")

packets = [input_data[i:i+packet_size] for i in range(0, len(input_data), packet_size)]
num_packets = len(packets)
num_bytes = len(input_data.encode('utf-8'))

loss_rate = 5.0  
packets_lost = int(num_packets * (loss_rate / 100))
packets_received = num_packets - packets_lost

received_packet_sizes = [len(packet.encode('utf-8')) for packet in packets[:packets_received]]

avg_packet_size = np.mean(received_packet_sizes) if received_packet_sizes else 0

metrics_data = {
    "Métrica": ["Total de Bytes Enviados", "Pacotes Enviados", "Pacotes Recebidos", "Pacotes Perdidos", "Tamanho Médio por Pacote"],
    "Valor": [num_bytes, num_packets, packets_received, packets_lost, round(avg_packet_size, 2)]
}
df_metrics = pd.DataFrame(metrics_data)

print("Métricas de Desempenho:")
print(df_metrics)

print(f"Tamanho médio dos pacotes recebidos: {avg_packet_size:.2f} bytes")

time = np.arange(len(received_packet_sizes))
plt.figure(figsize=(12, 6))
plt.plot(time, received_packet_sizes, marker="o", color="blue", label="Tamanho dos Pacotes")
plt.xlabel("Número do Pacote", fontsize=12)
plt.ylabel("Tamanho (bytes)", fontsize=12)
plt.title("Tamanho dos Pacotes Recebidos ao Longo do Tempo", fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('grafico_tamanho_pacotes.png', dpi=300)
plt.show()

if len(time) > 1:
    throughput = np.diff(np.cumsum(received_packet_sizes))
    max_throughput = np.max(throughput)
    print(f"Pico de throughput: {max_throughput:.2f} bytes/s")
    
    plt.figure(figsize=(12, 6))
    plt.plot(time[1:], throughput, color="green", label="Throughput (bytes/s)")
    plt.xlabel("Tempo (pacotes)", fontsize=12)
    plt.ylabel("Bytes Recebidos por Segundo", fontsize=12)
    plt.title("Throughput ao Longo do Tempo", fontsize=14)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('grafico_throughput.png', dpi=300)
    plt.show()

mean_packet_size = np.mean(received_packet_sizes)
std_packet_size = np.std(received_packet_sizes)
print(f"Média do tamanho dos pacotes: {mean_packet_size:.2f} bytes")
print(f"Desvio padrão do tamanho dos pacotes: {std_packet_size:.2f} bytes")

plt.figure(figsize=(12, 6))
plt.hist(received_packet_sizes, bins=20, edgecolor='black', alpha=0.7, color="orange")
plt.xlabel("Tamanho do Pacote (bytes)", fontsize=12)
plt.ylabel("Frequência", fontsize=12)
plt.title("Distribuição do Tamanho dos Pacotes Recebidos", fontsize=14)
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('grafico_distribuicao_tamanho.png', dpi=300)
plt.show()

# Gráfico 4: Simulação do Crescimento da Janela de Congestionamento (cwnd)
cwnd_values = [1]  # Começa com cwnd = 1
for i in range(1, len(received_packet_sizes)):
    if cwnd_values[-1] < 8:  # Slow Start
        cwnd_values.append(cwnd_values[-1] * 2)
    else:  # Congestion Avoidance
        cwnd_values.append(cwnd_values[-1] + 1)

max_cwnd = np.max(cwnd_values)
print(f"Valor máximo da janela de congestionamento (cwnd): {max_cwnd}")

plt.figure(figsize=(12, 6))
plt.plot(cwnd_values, label="Janela de Congestionamento (cwnd)")
plt.xlabel("Tempo (pacotes)", fontsize=12)
plt.ylabel("cwnd", fontsize=12)
plt.title("Crescimento da Janela de Congestionamento", fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('grafico_cwnd.png', dpi=300)
plt.show()

# Gráfico 5: Tamanho das linhas ao longo do tempo
lines = input_data.splitlines()
line_sizes = [len(line.encode('utf-8')) for line in lines]

mean_line_size = np.mean(line_sizes)
print(f"Tamanho médio das linhas: {mean_line_size:.2f} bytes")

plt.figure(figsize=(12, 6))
plt.plot(range(len(line_sizes)), line_sizes, marker="o", color="purple", label="Tamanho das Linhas")
plt.xlabel("Número da Linha", fontsize=12)
plt.ylabel("Tamanho (bytes)", fontsize=12)
plt.title("Tamanho das Linhas ao Longo do Tempo", fontsize=14)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('grafico_tamanho_linhas.png', dpi=300)
plt.show()