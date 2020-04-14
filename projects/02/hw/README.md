This project realises the ALU on a icebreaker FPGA board and provides access to
the ALU state registers by serially shifting out the ALU state using an ad-hoc
protocol which works as follows:

Serial Shift Out
================

Data is shifted out using 3 control signals: S_CLK, S_DATA and S_RESET.

S_CLK provides the clock signal to synchronise S_DATA with. S_DATA should
be read on the rising edge.

S_RESET is asserted for 1 clock cycle when entire ALU state has been shifted
out. When the reader sees this it should reset it's data to 0. This provides
a kind of frame-synchronisation.

Serial Shift In
===============

Data is shifted into the ALU state registers using 3 control signals: S_CLK,
S_DATA_IN, S_DATA_AVAILABLE.

The S_CLK signal is as described before. S_DATA_IN will be read on the rising
edge of S_CLK. This means the sender should update S_DATA_IN on the falling
edge. S_DATA_AVAILABLE should be asserted when the sender has data to send. If
not asserted then S_DATA_IN is ignored completely.
