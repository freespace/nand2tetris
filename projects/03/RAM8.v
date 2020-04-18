`default_nettype none

module RAM8(
  output wire[15:0] out,
  input wire clk,
  input wire load,
  input wire[2:0] addr,
  input wire[15:0] in);

  wire[7:0] load_reg;

  DMux8Way dmux_load(load_reg[0],
                     load_reg[1],
                     load_reg[2],
                     load_reg[3],
                     load_reg[4],
                     load_reg[5],
                     load_reg[6],
                     load_reg[7],
                     addr,
                     load);

  wire[15:0] ram_out[7:0];

  Register ram0(ram_out[0],
                clk,
                load_reg[0],
                in);
  Register ram1(ram_out[1],
                clk,
                load_reg[1],
                in);
  Register ram2(ram_out[2],
                clk,
                load_reg[2],
                in);
  Register ram3(ram_out[3],
                clk,
                load_reg[3],
                in);
  Register ram4(ram_out[4],
                clk,
                load_reg[4],
                in);
  Register ram5(ram_out[5],
                clk,
                load_reg[5],
                in);
  Register ram6(ram_out[6],
                clk,
                load_reg[6],
                in);
  Register ram7(ram_out[7],
                clk,
                load_reg[7],
                in);

  Mux8Way16 mux_out(out,
                    addr,
                    ram_out[0],
                    ram_out[1],
                    ram_out[2],
                    ram_out[3],
                    ram_out[4],
                    ram_out[5],
                    ram_out[6],
                    ram_out[7]);

endmodule

