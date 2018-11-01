"""
http://devernay.free.fr/hacks/chip8/C8TECH10.HTM#0.0

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
loaded_bytes = 0
with open('pong.ch8', 'rb') as game_file:
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
sound_timer = 0

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

"""
DISPLAY
The original implementation of the Chip-8 language used a 64x32-pixel monochrome display with this format:

(0,0)	(63,0)
(0,31)	(63,31)

Chip-8 draws graphics on screen through the use of sprites. A sprite is a group of bytes which are a binary representation of the desired picture. Chip-8 sprites may be up to 15 bytes, for a possible sprite size of 8x15.

Programs may also refer to a group of sprites representing the hexadecimal digits 0 through F. These sprites are 5 bytes long, or 8x5 pixels. The data should be stored in the interpreter area of Chip-8 memory (0x000 to 0x1FF). Below is a listing of each character's bytes, in binary and hexadecimal:
"""


"""
INSTRUCTION SET
The original implementation of the Chip-8 language includes 36 different instructions, including math, graphics, and flow control functions.

Super Chip-48 added an additional	10 instructions, for a total of 46.

All instructions are 2 bytes long and are stored most-significant-byte first. In memory, the first byte of each instruction should be located at an even addresses. If a program includes sprite data, it should be padded so any instructions following it will be properly situated in RAM.

This document does not yet contain descriptions of the Super Chip-48 instructions. They are, however, listed below.

In these listings, the following variables are used:

nnn or addr - A 12-bit value, the lowest 12 bits of the instruction
n or nibble - A 4-bit value, the lowest 4 bits of the instruction
x - A 4-bit value, the lower 4 bits of the high byte of the instruction
y - A 4-bit value, the upper 4 bits of the low byte of the instruction
kk or byte - An 8-bit value, the lowest 8 bits of the instruction



"""

"""
also super chip 48 has additional stuff
"""
# opcodes are all 2 bytes
# init bytes variable so the first while loop runs
while True:
    print "PC: %s" % program_counter
    print "SP: %s" % stack_pointer
    bytes = ram[program_counter] + ram[program_counter + 1]
    program_counter += 2
    # human readable hex out:
    # print map(hex, map(ord, bytes))
    # if byte == b'\x6a':
    #     print "got 0x6a"

    # opcode = bytes[0] & int(ord(b'\x0F'))
    print map(hex, bytes)

    first_nibble = bytes[0] >> 4
    second_nibble = bytes[0] & int("F", 16)
    third_nibble = bytes[1] >> 4
    fourth_nibble = bytes[1] & int("F", 16)

    """
    0nnn - SYS addr
    Jump to a machine code routine at nnn.
    This instruction is only used on the old computers on which Chip-8 was originally implemented.
    It is ignored by modern interpreters.
    """

    """
    if bytes[0] == 0 and bytes[1] == int("E0", 16):
        print "00E0 - CLS - Clear the display"
    """

    if bytes[0] == 0 and bytes[1] == int("EE", 16):
        "The interpreter sets the program counter to the address at the top of the stack, then subtracts 1 from the stack pointer"
        print "00EE - RET - Return from a subroutine"
        program_counter = stack[stack_pointer]
        stack_pointer -= 1
        continue

    if first_nibble == int("1", 16):
        "The interpreter sets the program counter to nnn"
        print "1nnn - JP addr - Jump to location nnn"
        first = second_nibble << 4 << 4
        program_counter = first + bytes[1]
        continue

    if first_nibble == int("2", 16):
        "The interpreter increments the stack pointer, then puts the current PC on the top of the stack. The PC is then set to nnn."
        print "2nnn - CALL addr - Call subroutine at nnn"
        stack_pointer += 1
        stack[stack_pointer] = program_counter
        program_counter = (second_nibble << 4 << 4) + bytes[1]
        continue

    if first_nibble == int("3", 16):
        "The interpreter compares register Vx to kk, and if they are equal, increments the program counter by 2"
        print "3xkk - SE Vx, byte - Skip next instruction if Vx = kk"
        if register_v[second_nibble] == bytes[1]:
            program_counter += 2
        continue

    if first_nibble == int("4", 16):
        print "4xkk - SNE Vx, byte - Skip next instruction if Vx != kk"
        "The interpreter compares register Vx to kk, and if they are not equal, increments the program counter by 2"
        if register_v[second_nibble] != bytes[1]:
            program_counter += 2
        continue

    if first_nibble == int("5", 16):
        "The interpreter compares register Vx to register Vy, and if they are equal, increments the program counter by 2."
        print "5xy0 - SE Vx, Vy - Skip next instruction if Vx = Vy"
        if register_v[second_nibble] == register_v[third_nibble]:
            program_counter += 2
        continue

    if first_nibble == int("6", 16):
        print "6xkk - LD Vx, byte - Set Vx = kk"
        reg = second_nibble
        register_v[reg] = bytes[1]
        "The interpreter puts the value kk into register Vx."
        continue

    if first_nibble == int("7", 16):
        print "7xkk - ADD Vx, byte - Set Vx = Vx + kk"
        reg = second_nibble
        register_v[reg] += bytes[1]
        "Adds the value kk to the value of register Vx, then stores the result in Vx."
        continue

    if first_nibble == int("8", 16) and fourth_nibble == 0:
        "Stores the value of register Vy in register Vx"
        print "8xy0 - LD Vx, Vy - Set Vx = Vy"
        register_v[second_nibble] = register_v[third_nibble]

    """
    8xy1 - OR Vx, Vy
    Set Vx = Vx OR Vy.

    Performs a bitwise OR on the values of Vx and Vy, then stores the result in Vx. A bitwise OR compares the corrseponding bits from two values, and if either bit is 1, then the same bit in the result is also 1. Otherwise, it is 0.


    8xy2 - AND Vx, Vy
    Set Vx = Vx AND Vy.

    Performs a bitwise AND on the values of Vx and Vy, then stores the result in Vx. A bitwise AND compares the corrseponding bits from two values, and if both bits are 1, then the same bit in the result is also 1. Otherwise, it is 0.


    8xy3 - XOR Vx, Vy
    Set Vx = Vx XOR Vy.

    Performs a bitwise exclusive OR on the values of Vx and Vy, then stores the result in Vx. An exclusive OR compares the corrseponding bits from two values, and if the bits are not both the same, then the corresponding bit in the result is set to 1. Otherwise, it is 0.


    8xy4 - ADD Vx, Vy
    Set Vx = Vx + Vy, set VF = carry.

    The values of Vx and Vy are added together. If the result is greater than 8 bits (i.e., > 255,) VF is set to 1, otherwise 0. Only the lowest 8 bits of the result are kept, and stored in Vx.


    8xy5 - SUB Vx, Vy
    Set Vx = Vx - Vy, set VF = NOT borrow.

    If Vx > Vy, then VF is set to 1, otherwise 0. Then Vy is subtracted from Vx, and the results stored in Vx.


    8xy6 - SHR Vx {, Vy}
    Set Vx = Vx SHR 1.

    If the least-significant bit of Vx is 1, then VF is set to 1, otherwise 0. Then Vx is divided by 2.


    8xy7 - SUBN Vx, Vy
    Set Vx = Vy - Vx, set VF = NOT borrow.

    If Vy > Vx, then VF is set to 1, otherwise 0. Then Vx is subtracted from Vy, and the results stored in Vx.


    8xyE - SHL Vx {, Vy}
    Set Vx = Vx SHL 1.

    If the most-significant bit of Vx is 1, then VF is set to 1, otherwise to 0. Then Vx is multiplied by 2.
    """

    if first_nibble == int("9", 16):
        print "9xy0 - SNE Vx, Vy - Skip next instruction if Vx != Vy"
        "The values of Vx and Vy are compared, and if they are not equal, the program counter is increased by 2."
        if register_v[second_nibble] != register_v[third_nibble]:
            program_counter += 2
        continue

    if first_nibble == int("A", 16):
        print "Annn - LD I, addr - Set I = nnn"
        "The value of register I is set to nnn."
        first = second_nibble << 4 << 4
        register_i = first + bytes[1]
        print "register_i = %s" % register_i
        continue

    if first_nibble == int("B", 16):
        print "Bnnn - JP V0, addr - Jump to location nnn + V0"
        program_counter = (second_nibble << 4 << 4) + bytes[1] + register_v[0]
        "The program counter is set to nnn plus the value of V0."
        continue

    """
    Cxkk - RND Vx, byte
    Set Vx = random byte AND kk.
    The interpreter generates a random number from 0 to 255, which is then ANDed with the value kk. The results are stored in Vx. See instruction 8xy2 for more information on AND.


    Dxyn - DRW Vx, Vy, nibble
    Display n-byte sprite starting at memory location I at (Vx, Vy), set VF = collision.
    The interpreter reads n bytes from memory, starting at the address stored in I. These bytes are then displayed as sprites on screen at coordinates (Vx, Vy). Sprites are XORed onto the existing screen. If this causes any pixels to be erased, VF is set to 1, otherwise it is set to 0. If the sprite is positioned so part of it is outside the coordinates of the display, it wraps around to the opposite side of the screen. See instruction 8xy3 for more information on XOR, and section 2.4, Display, for more information on the Chip-8 screen and sprites.


    Ex9E - SKP Vx
    Skip next instruction if key with the value of Vx is pressed.
    Checks the keyboard, and if the key corresponding to the value of Vx is currently in the down position, PC is increased by 2.


    ExA1 - SKNP Vx
    Skip next instruction if key with the value of Vx is not pressed.
    Checks the keyboard, and if the key corresponding to the value of Vx is currently in the up position, PC is increased by 2.


    Fx07 - LD Vx, DT
    Set Vx = delay timer value.
    The value of DT is placed into Vx.


    Fx0A - LD Vx, K
    Wait for a key press, store the value of the key in Vx.
    All execution stops until a key is pressed, then the value of that key is stored in Vx.


    Fx15 - LD DT, Vx
    Set delay timer = Vx.
    DT is set equal to the value of Vx.


    Fx18 - LD ST, Vx
    Set sound timer = Vx.
    ST is set equal to the value of Vx.

    """

    if first_nibble == int("B", 16):
        "The values of I and Vx are added, and the results are stored in I"
        print "Fx1E - ADD I, Vx - Set I = I + Vx"
        register_i = register_i + register_v[second_nibble]
        continue

    """
    Fx29 - LD F, Vx
    Set I = location of sprite for digit Vx.

    The value of I is set to the location for the hexadecimal sprite corresponding to the value of Vx. See section 2.4, Display, for more information on the Chip-8 hexadecimal font.


    Fx33 - LD B, Vx
    Store BCD representation of Vx in memory locations I, I+1, and I+2.

    The interpreter takes the decimal value of Vx, and places the hundreds digit in memory at location in I, the tens digit at location I+1, and the ones digit at location I+2.


    Fx55 - LD [I], Vx
    Store registers V0 through Vx in memory starting at location I.

    The interpreter copies the values of registers V0 through Vx into memory, starting at the address in I.


    Fx65 - LD Vx, [I]
    Read registers V0 through Vx from memory starting at location I.

    The interpreter reads values from memory starting at location I into registers V0 through Vx.
    ram[register_i]
    register_v[]
    loop second_nibble times

    """

# end of the program loop

# 6a02
# 3f0c



"""
# Some bytes to play with
byte1 = int('11110000', 2)  # 240
byte2 = int('00001111', 2)  # 15
byte3 = int('01010101', 2)  # 85

# Ones Complement (Flip the bits)
print(~byte1)

# AND
print(byte1 & byte2)

# OR
print(byte1 | byte2)

# XOR
print(byte1 ^ byte3)

# Shifting right will lose the right-most bit
print(byte2 >> 3)

# Shifting left will add a 0 bit on the right side
print(byte2 << 1)

# See if a single bit is set
bit_mask = int('00000001', 2)  # Bit 1
print(bit_mask & byte1)  # Is bit set in byte1?
print(bit_mask & byte2)  # Is bit set in byte2?
"""
