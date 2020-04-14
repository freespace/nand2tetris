#include <Arduino.h>
#include "FastLED.h"

#define ALU_STATE_SIZE  58
#define NUM_LEDS        ALU_STATE_SIZE

#define S_CLK_PIN       2
#define S_DATA_PIN      6
#define S_RESET_PIN     7

#define ZR_IDX          0
#define NG_IDX          1
#define NO_IDX          2
#define F_IDX           3
#define NY_IDX          4
#define ZY_IDX          5
#define NX_IDX          6
#define ZX_IDX          7
#define OUT_IDX         8
#define Y_IDX           24
#define X_IDX           40

CRGB leds[NUM_LEDS];

// doing bit for bit would be more efficient but we have plenty
// of resources and getting this working fast is more important
// to me
volatile uint8_t alu_idx = 0;
volatile uint8_t alu_state[ALU_STATE_SIZE];
volatile bool needs_display = false;

typedef enum {
  STATE_WAIT_DISPLAY,
  STATE_WAIT_RESET,
  STATE_READ_DATA,
} ShiftState;

volatile ShiftState shift_state = STATE_WAIT_RESET;

void setup() {
  FastLED.addLeds<WS2812B, 5, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(32);

  pinMode(S_CLK_PIN, INPUT);
  pinMode(S_DATA_PIN, INPUT);
  pinMode(S_RESET_PIN, INPUT);

  attachInterrupt(digitalPinToInterrupt(S_CLK_PIN), _on_s_clk, RISING);
}

CRGB get_colour(uint8_t idx) {
  switch(idx) {
    case ZR_IDX:
      return CRGB::Green;

    case NG_IDX:
      return CRGB::Red;

    case NO_IDX:
      return CRGB::Yellow;

    case F_IDX:
      return CRGB::Magenta;

    case NY_IDX:
    case NX_IDX:
      return CRGB::LawnGreen;

    case ZY_IDX:
    case ZX_IDX:
      return CRGB::LightBlue;

    default:
      break;
  }

  // if we got here then we have either OUT or X and Y
  if (idx >= OUT_IDX && idx < Y_IDX) {
    return CRGB::Green;
  }

  if (idx >= Y_IDX && idx < X_IDX) {
    return CRGB::Blue;
  }

  // this should be X
  return CRGB::Red;
}

void loop() {
  if (needs_display) {
    for (int idx = 0; idx < ALU_STATE_SIZE; ++idx) {
      if (alu_state[idx]) {
        leds[idx] = get_colour(idx);
      } else {
        leds[idx] = CRGB::Black;
      }

    }

    FastLED.show();
    needs_display = false;
  }
}

void _on_s_clk() {
  switch(shift_state) {
    case STATE_WAIT_DISPLAY:
      if (needs_display == false) {
        shift_state = STATE_WAIT_RESET;
      }
      break;

    case STATE_WAIT_RESET:
      if (digitalRead(S_RESET_PIN)) {
        shift_state = STATE_READ_DATA;
        alu_idx = 0;
      }
      break;

    case STATE_READ_DATA:
      if (digitalRead(S_RESET_PIN)) {
        needs_display = true;
        shift_state = STATE_WAIT_DISPLAY;
      } else {
        if (alu_idx < ALU_STATE_SIZE) {
          alu_state[alu_idx] = digitalRead(S_DATA_PIN);
          alu_idx += 1;
        }
      }
      break;

    default:
      break;
  }
}
