// This file is part of nand2tetris, as taught in The Hebrew University, and
// was written by Aviv Yaish. It is an extension to the specifications given
// [here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
// as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
// Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).

// The program should swap between the max. and min. elements of an array.
// Assumptions:
// - The array's start address is stored in R14, and R15 contains its length
// - Each array value x is between -16384 < x < 16384
// - The address in R14 is at least >= 2048
// - R14 + R15 <= 16383
//
// Requirements:
// - Changing R14, R15 is not allowed.

@R14
D=M

@currentmax
M=D
@currentmin
M=D
@iter
M=1

(FINDER)

    @iter
    D=M
    @R15
    D=D-M
    @SWAPVALUES
    D;JEQ

    @iter
    D=M
    @R14
    D=D+M
    @currentelement
    M=D

    @currentelement
    A=M
    D=M
    @currentmax
    A=M
    D=D-M
    @FOUNDMAX
    D;JGT
    
    @currentelement
    A=M
    D=M
    @currentmin
    A=M
    D=D-M
    @FOUNDMIN
    D;JLT

(FOUNDMAX)

    @currentelement
    D=M
    @currentmax
    M=D
    @CONTINUEFIND
    0;JMP

(FOUNDMIN)

    @currentelement
    D=M
    @currentmin
    M=D
    // Fallthrough!

(CONTINUEFIND)

    @iter
    M=M+1
    @FINDER
    0;JMP

(SWAPVALUES)
    @currentmax
    A=M
    D=M
    @maxval
    M=D

    @currentmin
    A=M
    D=M
    @minval
    M=D

    @maxval
    D=M
    @currentmin
    A=M
    M=D

    @minval
    D=M
    @currentmax
    A=M
    M=D

(FINLOOP)
    @FINLOOP
    0;JMP
