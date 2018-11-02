"""
http://devernay.free.fr/hacks/chip8/C8TECH10.HTM#0.0
"""
import os
import random
import signal
import sys
import time

import curses

from sprites import sprites

def signal_handler(sig, frame):
    curses.endwin()
    print('You pressed Ctrl+C!')
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


if 'DEBUG' in os.environ:
    DEBUG = True
else:
    DEBUG = False


bitmasks = [
    int("10000000", 2),
    int("01000000", 2),
    int("00100000", 2),
    int("00010000", 2),
    int("00001000", 2),
    int("00000100", 2),
    int("00000010", 2),
    int("00000001", 2),
]


"""


RAM
4k ram
0x000 (0) to 0xFFF (4095)
The first 512 bytes, from 0x000 to 0x1FF, are where the original interpreter was located, and should not be used by programs.
Most Chip-8 programs start at location 0x200 (512), but some begin at 0x600 (1536). Programs beginning at 0x600 are intended for the ETI 660 computer.

Memory Map:
+---------------+= 0xFFF (4095) End of Chip-8 RAM
|               |
|               |
|               |
|               |
|               |
| 0x200 to 0xFFF|
|     Chip-8    |
| Program / Data|
|     Space     |
|               |
|               |
|               |
+- - - - - - - -+= 0x600 (1536) Start of ETI 660 Chip-8 programs
|               |
|               |
|               |
+---------------+= 0x200 (512) Start of most Chip-8 programs
| 0x000 to 0x1FF|
| Reserved for  |
|  interpreter  |
+---------------+= 0x000 (0) Start of Chip-8 RAM
"""
ram = [0] * 4096

# load sprites in
for i in range(len(sprites)):
    ram[i] = sprites[i]

loaded_bytes = 0
print "Loading..."
with open(sys.argv[1], 'rb') as game_file:
    while True:
        byte = bytearray(game_file.read(1))
        if byte == bytearray():
            print "Finished loading"
            break
        ram[loaded_bytes + 512] = byte
        loaded_bytes += 1

"""
16x 8 bit registers - 0-F
F register should not be used by any programs, cpu uses it
"""
register_v = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

"""
1x 16 bit register "I"
store memory addresses?
usually only 12 bits are needed/used
"""
register_i = 00


"""
The delay timer is active whenever the delay timer register (DT) is non-zero.
This timer does nothing more than subtract 1 from the value of DT at a rate of 60Hz.
When DT reaches 0, it deactivates.

The sound timer is active whenever the sound timer register (ST) is non-zero.
This timer also decrements at a rate of 60Hz, however, as long as ST's value is greater than zero, the Chip-8 buzzer will sound.
When ST reaches zero, the sound timer deactivates.
The sound produced by the Chip-8 interpreter has only one tone.
The frequency of this tone is decided by the author of the interpreter.
"""
delay_timer = 0
delay_timer_updated = 0
sound_timer = 0
sound_timer_updated = 0

"""
There are also some "pseudo-registers" which are not accessable from Chip-8 programs.
The program counter (PC) should be 16-bit, and is used to store the currently executing address.
The stack pointer (SP) can be 8-bit, it is used to point to the topmost level of the stack.
"""
program_counter = 512
stack_pointer = 0

"""
The stack is an array of 16 16-bit values,
used to store the address that the interpreter shoud return to when finished with a subroutine.
Chip-8 allows for up to 16 levels of nested subroutines.
"""
stack = [00, 00, 00, 00, 00, 00, 00, 00, 00, 00, 00, 00, 00, 00, 00, 00, ]

"""
KEYBOARD
The computers which originally used the Chip-8 Language had a 16-key hexadecimal keypad with the following layout:

1	2	3	C
4	5	6	D
7	8	9	E
A	0	B	F

This layout must be mapped into various other configurations to fit the keyboards of today's platforms.
"""
keyboard = [0] * 16
# TODO: actually gather keypresses

display = []
for _ in range(32):
    display.append([0] * 64)

# ncurses setup
stdscr = curses.initscr()
curses.noecho() # don't echo input
curses.cbreak() # dont wait for enter on input
begin_x = 0
begin_y = 0
width = 64
height = 32
# window = curses.newwin(height + 1, width, begin_y, begin_x)
# add 1 for output


"""
also super chip 48 has additional stuff
"""
# opcodes are all 2 bytes
# init bytes variable so the first while loop runs
while True:
    # TODO: should run at 500hz apparently
    # time.sleep(int(1)/500)
    time.sleep(0.001)

    # TODO: make sound
    if sound_timer > 0:
        # decreases by 1 at 60hz
        if time.time() - sound_timer_updated >= float(1) / 60:
            sound_timer -= 1
            sound_timer_updated = time.time()

    if delay_timer > 0:
        # decreases by 1 at 60hz
        if time.time() - delay_timer_updated >= float(1) / 60:
            delay_timer -= 1
            delay_timer_updated = time.time()

    bytes = ram[program_counter] + ram[program_counter + 1]
    program_counter += 2

    if DEBUG:
        print map(hex, bytes)

    first_nibble = bytes[0] >> 4
    second_nibble = bytes[0] & int("F", 16)
    third_nibble = bytes[1] >> 4
    fourth_nibble = bytes[1] & int("F", 16)

    if bytes[0] == 0 and bytes[1] == int("E0", 16):
        if DEBUG:
            print "00E0 - CLS - Clear the display"
        for row in range(len(display)):
            for cell in range(len(display[row])):
                display[row][cell] = 0
        stdscr.refresh()
        continue

    if first_nibble == int("1", 16):
        "This instruction is only used on the old computers on which Chip-8 was originally implemented. It is ignored by modern interpreters"
        if DEBUG:
            print "0nnn - SYS addr - Jump to a machine code routine at nnn"
        first = second_nibble << 4 << 4
        program_counter = first + bytes[1]
        continue

    if bytes[0] == 0 and bytes[1] == int("EE", 16):
        "The interpreter sets the program counter to the address at the top of the stack, then subtracts 1 from the stack pointer"
        if DEBUG:
            print "00EE - RET - Return from a subroutine"
        program_counter = stack[stack_pointer]
        stack_pointer -= 1
        continue

    if first_nibble == int("1", 16):
        "The interpreter sets the program counter to nnn"
        if DEBUG:
            print "1nnn - JP addr - Jump to location nnn"
        first = second_nibble << 4 << 4
        program_counter = first + bytes[1]
        continue

    if first_nibble == int("2", 16):
        "The interpreter increments the stack pointer, then puts the current PC on the top of the stack. The PC is then set to nnn."
        if DEBUG:
            print "2nnn - CALL addr - Call subroutine at nnn"
        stack_pointer += 1
        stack[stack_pointer] = program_counter
        program_counter = (second_nibble << 4 << 4) + bytes[1]
        continue

    if first_nibble == int("3", 16):
        "The interpreter compares register Vx to kk, and if they are equal, increments the program counter by 2"
        if DEBUG:
            print "3xkk - SE Vx, byte - Skip next instruction if Vx = kk"
        if register_v[second_nibble] == bytes[1]:
            program_counter += 2
        continue

    if first_nibble == int("4", 16):
        "The interpreter compares register Vx to kk, and if they are not equal, increments the program counter by 2"
        if DEBUG:
            print "4xkk - SNE Vx, byte - Skip next instruction if Vx != kk"
        if register_v[second_nibble] != bytes[1]:
            program_counter += 2
        continue

    if first_nibble == int("5", 16):
        "The interpreter compares register Vx to register Vy, and if they are equal, increments the program counter by 2."
        if DEBUG:
            print "5xy0 - SE Vx, Vy - Skip next instruction if Vx = Vy"
        if register_v[second_nibble] == register_v[third_nibble]:
            program_counter += 2
        continue

    if first_nibble == int("6", 16):
        "The interpreter puts the value kk into register Vx."
        if DEBUG:
            print "6xkk - LD Vx, byte - Set Vx = kk"
        register_v[second_nibble] = bytes[1]
        continue

    if first_nibble == int("7", 16):
        "Adds the value kk to the value of register Vx, then stores the result in Vx."
        if DEBUG:
            print "7xkk - ADD Vx, byte - Set Vx = Vx + kk"
        reg = second_nibble
        register_v[reg] += bytes[1]
        continue

    if first_nibble == int("8", 16):
        if fourth_nibble == 0:
            "Stores the value of register Vy in register Vx"
            if DEBUG:
                print "8xy0 - LD Vx, Vy - Set Vx = Vy"
            register_v[second_nibble] = register_v[third_nibble]
            continue

        if fourth_nibble == 1:
            "Performs a bitwise OR on the values of Vx and Vy, then stores the result in Vx \
            A bitwise OR compares the corrseponding bits from two values, and if either bit is 1, then the same bit in the result is also 1. Otherwise, it is 0"
            if DEBUG:
                print "8xy1 - OR Vx, Vy - Set Vx = Vx OR Vy"
            register_v[second_nibble] = register_v[second_nibble] | register_v[third_nibble]
            continue

        if fourth_nibble == 2:
            "Performs a bitwise AND on the values of Vx and Vy, then stores the result in Vx \
            A bitwise AND compares the corrseponding bits from two values, and if both bits are 1, then the same bit in the result is also 1. Otherwise, it is 0."
            if DEBUG:
                print "8xy2 - AND Vx, Vy - Set Vx = Vx AND Vy"
            register_v[second_nibble] = register_v[second_nibble] & register_v[third_nibble]
            continue

        if fourth_nibble == 3:
            "Performs a bitwise exclusive OR on the values of Vx and Vy, then stores the result in Vx \
            An exclusive OR compares the corrseponding bits from two values, and if the bits are not both the same, then the corresponding bit in the result is set to 1. Otherwise, it is 0."
            if DEBUG:
                print "8xy3 - XOR Vx, Vy - Set Vx = Vx XOR Vy"
            register_v[second_nibble] = register_v[second_nibble] ^ register_v[third_nibble]
            continue

        if fourth_nibble == 4:
            "The values of Vx and Vy are added together. If the result is greater than 8 bits (i.e., > 255,) VF is set to 1, otherwise 0. Only the lowest 8 bits of the result are kept, and stored in Vx."
            if DEBUG:
                print "8xy4 - ADD Vx, Vy - Set Vx = Vx + Vy, set VF = carry"
            register_v[second_nibble] += register_v[third_nibble]
            if register_v[second_nibble] > 255:
                register_v[second_nibble] = 255
                register_v[int("F", 16)] = 1
            else:
                register_v[int("F", 16)] = 0
            continue

        if fourth_nibble == 5:
            "If Vx > Vy, then VF is set to 1, otherwise 0. Then Vy is subtracted from Vx, and the results stored in Vx."
            if DEBUG:
                print "8xy5 - SUB Vx, Vy - Set Vx = Vx - Vy, set VF = NOT borrow"
            if register_v[second_nibble] > register_v[third_nibble]:
                register_v[int("F", 16)] = 1
                register_v[second_nibble] -= register_v[third_nibble]
            else:
                register_v[int("F", 16)] = 0
                register_v[second_nibble] = 256 + register_v[second_nibble] - register_v[third_nibble]
            continue

        if fourth_nibble == 6:
            "If the least-significant bit of Vx is 1, then VF is set to 1, otherwise 0. Then Vx is divided by 2."
            if DEBUG:
                print "8xy6 - SHR Vx {, Vy} - Set Vx = Vx SHR 1"
            register_v[int("f", 16)] = register_v[second_nibble] & 1
            register_v[second_nibble] = register_v[second_nibble] >> 1
            continue

        if fourth_nibble == 7:
            "If Vy > Vx, then VF is set to 1, otherwise 0. Then Vx is subtracted from Vy, and the results stored in Vx."
            if DEBUG:
                print "8xy7 - SUBN Vx, Vy - Set Vx = Vy - Vx, set VF = NOT borrow"
            if register_v[third_nibble] > register_v[second_nibble]:
                register_v[int("f", 16)] = 1
                register_v[second_nibble] = register_v[third_nibble] - register_v[second_nibble]
            else:
                register_v[int("f", 16)] = 0
                register_v[second_nibble] = 256 + register_v[third_nibble] - register_v[second_nibble]
            continue

        if fourth_nibble == int("E", 16):
            "If the most-significant bit of Vx is 1, then VF is set to 1, otherwise to 0. Then Vx is multiplied by 2."
            if DEBUG:
                print "8xyE - SHL Vx {, Vy} - Set Vx = Vx SHL 1"
            register_v[int("F", 16)] = register_v[second_nibble] >> 7
            register_v[second_nibble] = register_v[second_nibble] << 1
            continue

        # end of 8 opcodes

    if first_nibble == int("9", 16):
        "The values of Vx and Vy are compared, and if they are not equal, the program counter is increased by 2."
        if DEBUG:
            print "9xy0 - SNE Vx, Vy - Skip next instruction if Vx != Vy"
        if register_v[second_nibble] != register_v[third_nibble]:
            program_counter += 2
        continue

    if first_nibble == int("A", 16):
        "The value of register I is set to nnn."
        if DEBUG:
            print "Annn - LD I, addr - Set I = nnn"
        first = second_nibble << 4 << 4
        register_i = first + bytes[1]
        if DEBUG:
            print "register_i = %s" % register_i
        continue

    if first_nibble == int("B", 16):
        "The program counter is set to nnn plus the value of V0."
        if DEBUG:
            print "Bnnn - JP V0, addr - Jump to location nnn + V0"
        program_counter = (second_nibble << 4 << 4) + bytes[1] + register_v[0]
        continue

    if first_nibble == int("C", 16):
        "The interpreter generates a random number from 0 to 255, which is then ANDed with the value kk. The results are stored in Vx \
        See instruction 8xy2 for more information on AND"
        if DEBUG:
            print "Cxkk - RND Vx, byte - Set Vx = random byte AND kk"
        register_v[second_nibble] = random.randint(0, 255) & bytes[1]
        continue

    if first_nibble == int("D", 16):
        "The interpreter reads n bytes from memory, starting at the address stored in I \
        These bytes are then displayed as sprites on screen at coordinates (Vx, Vy) \
        Sprites are XORed onto the existing screen. If this causes any pixels to be erased, VF is set to 1, otherwise it is set to 0 \
        If the sprite is positioned so part of it is outside the coordinates of the display, it wraps around to the opposite side of the screen \
        See instruction 8xy3 for more information on XOR, and section 2.4, Display, for more information on the Chip-8 screen and sprites."
        if DEBUG:
            print "Dxyn - DRW Vx, Vy, nibble - Display n-byte sprite starting at memory location I at (Vx, Vy), set VF = collision"
        x = register_v[second_nibble]
        y = register_v[third_nibble]

        the_bytes = ram[register_i:register_i + fourth_nibble]

        for read_byte in the_bytes:
            if type(read_byte) == bytearray:
                read_byte = ord(read_byte)
            else:
                read_byte = read_byte

            # do each bit at a time
            for mask_bit in range(8):
                try:
                    display[y][x + mask_bit] = display[y][x + mask_bit] ^ (read_byte & bitmasks[mask_bit])
                except Exception as e:
                    pass
            y += 1

        for y in range(len(display)):
            for x in range(len(display[y])):
                if display[y][x] > 0:
                    output = "0"
                else:
                    output = " "
                stdscr.addstr(y, x, output, curses.COLOR_WHITE)

        stdscr.refresh()
        continue

    if first_nibble == int("E", 16):

        if bytes[1] == int("9E", 16):
            "Checks the keyboard, and if the key corresponding to the value of Vx is currently in the down position, PC is increased by 2"
            if DEBUG:
                print "Ex9E - SKP Vx - Skip next instruction if key with the value of Vx is pressed"
            if keyboard[register_v[second_nibble]] == 1:
                program_counter += 2
            continue

        if bytes[1] == int("A1", 16):
            "Checks the keyboard, and if the key corresponding to the value of Vx is currently in the up position, PC is increased by 2"
            if DEBUG:
                print "ExA1 - SKNP Vx - Skip next instruction if key with the value of Vx is not pressed"
            if keyboard[register_v[second_nibble]] == 0:
                program_counter += 2
                continue

    if first_nibble == int("F", 16):

        if bytes[1] == int("07", 16):
            "The value of DT is placed into Vx"
            if DEBUG:
                print "Fx07 - LD Vx, DT - Set Vx = delay timer value"
            register_v[second_nibble] = delay_timer
            continue

        """
        Fx0A - LD Vx, K
        Wait for a key press, store the value of the key in Vx.
        All execution stops until a key is pressed, then the value of that key is stored in Vx.
        """

        if bytes[1] == int("15", 16):
            "DT is set equal to the value of Vx"
            if DEBUG:
                print "Fx15 - LD DT, Vx - Set delay timer = Vx"
            delay_timer = register_v[second_nibble]
            delay_timer_updated = time.time()
            continue

        if bytes[1] == int("18", 16):
            "ST is set equal to the value of Vx"
            if DEBUG:
                print "Fx18 - LD ST, Vx - Set sound timer = Vx"
            sound_timer = register_v[second_nibble]
            sound_timer_updated = time.time()
            continue

        if bytes[1] == int("1E", 16):
            "The values of I and Vx are added, and the results are stored in I"
            if DEBUG:
                print "Fx1E - ADD I, Vx - Set I = I + Vx"
            if type(register_v[second_nibble]) == bytearray:
                register_i = register_v[second_nibble][0]
            else:
                register_i += register_v[second_nibble]
            continue

        if bytes[1] == int("29", 16):
            "The value of I is set to the location for the hexadecimal sprite corresponding to the value of Vx. See section 2.4, Display, for more information on the Chip-8 hexadecimal font"
            if DEBUG:
                print "Fx29 - LD F, Vx - Set I = location of sprite for digit Vx"
            register_i = second_nibble * 5
            continue

        if bytes[1] == int("33", 16):
            "The interpreter takes the decimal value of Vx, and places the hundreds digit in memory at location in I, the tens digit at location I+1, and the ones digit at location I+2"
            if DEBUG:
                print "Fx33 - LD B, Vx - Store BCD representation of Vx in memory locations I, I+1, and I+2"
            bcd_value = '{:03d}'.format(register_v[second_nibble])
            ram[register_i] = int(bcd_value[0])
            ram[register_i + 1] = int(bcd_value[1])
            ram[register_i + 2] = int(bcd_value[2])
            continue

        if bytes[1] == int("55", 16):
            "The interpreter copies the values of registers V0 through Vx into memory, starting at the address in I"
            if DEBUG:
                print "Fx55 - LD [I], Vx - Store registers V0 through Vx in memory starting at location I"
            for i in range(second_nibble + 1):
                ram[register_i + i] = register_v[i]
            continue

        if bytes[1] == int("65", 16):
            "The interpreter reads values from memory starting at location I into registers V0 through Vx"
            if DEBUG:
                print "Fx65 - LD Vx, [I] - Read registers V0 through Vx from memory starting at location I"
            for i in range(second_nibble + 1):
                register_v[i] = ram[register_i + i]
            continue
        # end of F opcodes

    stdscr.addstr(32, 0, "TODO: %s" % (map(hex, bytes)))

# end of the program loop

# TODO: use 0xF (no quotes or anything) instead of int("F", 16)
