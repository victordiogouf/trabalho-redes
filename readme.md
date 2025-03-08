# Trabalho de Redes

Protocolo confiável de transporte sobre UDP com comunicação ponto a ponto full-duplex com as seguintes características:
- Entrega ordenada
- Confirmação acumulativa
- Controle de fluxo
- Controle de congestionamento

## Cabeçalho

O cabeçalho do segmento é composto pela seguinte sequência de bits:

0  - 31: Número de sequência (32 bits)
32 - 63: Número de confirmação (32 bits)
64 - 79: Tamanho da janela de recebimento em bytes (16 bits)
80 - 84: não utilizados (5 bits)
85     : ACK (bit de confirmação de recebimento)
86     : SYN (bit de sincronização)
87     : FIN (bit de finalização)

Totalizando 11 bytes fixos.