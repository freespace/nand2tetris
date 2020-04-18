`default_nettype none

module RAM64(
  output wire[15:0] out,
  input wire clk,
  input wire load,
  input wire[5:0] addr,
  input wire[15:0] in);

  wire[2:0] addr_h, addr_l;
  assign {addr_h, addr_l} = addr;

  wire[7:0] load_ram;
  DMux8Way dmux_load(load_ram[0],
                     load_ram[1],
                     load_ram[2],
                     load_ram[3],
                     load_ram[4],
                     load_ram[5],
                     load_ram[6],
                     load_ram[7],
                     addr_h,
                     load);

  wire[15:0] ram_out[7:0];

  RAM8 ram0(ram_out[0],
            clk,
            load_ram[0],
            addr_l,
            in);
  RAM8 ram1(ram_out[1],
            clk,
            load_ram[1],
            addr_l,
            in);
  RAM8 ram2(ram_out[2],
            clk,
            load_ram[2],
            addr_l,
            in);
  RAM8 ram3(ram_out[3],
            clk,
            load_ram[3],
            addr_l,
            in);
  RAM8 ram4(ram_out[4],
            clk,
            load_ram[4],
            addr_l,
            in);
  RAM8 ram5(ram_out[5],
            clk,
            load_ram[5],
            addr_l,
            in);
  RAM8 ram6(ram_out[6],
            clk,
            load_ram[6],
            addr_l,
            in);
  RAM8 ram7(ram_out[7],
            clk,
            load_ram[7],
            addr_l,
            in);

  Mux8Way16 mux_out(out,
                    addr_h,
                    ram_out[0],
                    ram_out[1],
                    ram_out[2],
                    ram_out[3],
                    ram_out[4],
                    ram_out[5],
                    ram_out[6],
                    ram_out[7]);
endmodule
