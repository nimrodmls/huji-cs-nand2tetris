"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
from typing import List

def relation_asm(relation, count):
    """
    Hack ASM code for (in)equalities
    """
    # y is the topmost value, x is the value below it,
    # An (in)equality is true (-1) if x ~ y, and false otherwise (0)
    # with ~ being either < or >
    return [
        "@SP",
        "M=M-1",
        "A=M",
        "D=M",
        "@R15",
        "M=D", # Save the value of y in R15, next we load X into D
        "@SP",
        "A=M-1",
        "D=M",
        "@R14",
        "M=D", # Save the value of x in R14
        
        # Save the sign of x in R13
        f"@NEGATIVE_X_{relation}_{count}",
        "D;JLT", # If D < 0, we jump to NEGATIVE
        f"@R13",
        "M=0", # If D >= 0, we set the value of the register to 0
        f"@SAVE_SIGN_Y_{relation}_{count}",
        "0;JMP", 
        f"(NEGATIVE_X_{relation}_{count})", # If D < 0, we set the value of the register to -1
        f"@R13",
        "M=-1",

        # Save the sign of y in D
        f"(SAVE_SIGN_Y_{relation}_{count})",
        # First loading y
        "@R15",
        "D=M",
        f"@NEGATIVE_Y_{relation}_{count}",
        "D;JLT", # If D < 0, we jump to NEGATIVE
        "D=0", # If D >= 0, we set the value of the register to 0
        f"@COMPARE_SIGNS_{relation}_{count}",
        "0;JMP",  # We saved both signs, now we compare them
        f"(NEGATIVE_Y_{relation}_{count})", # If D < 0, we set the value of the register to -1
        "D=-1",
        
        # At this point, we have the signs of x in R13 and of y in D
        # We check whether the signs and the same by subtracting them
        f"(COMPARE_SIGNS_{relation}_{count})",
        "@R13",
        "D=D-M", # Subtracting the sign of y from the sign of x
        f"@COMPARE_ELEMENTS_{relation}_{count}",
        "D;JNE", # If the signs are inequal, we can compare directly

        # Otherwise, they are with equal signs, we need to subtract x and y
        # at this point we don't need the signs saved at R13 and D
        "@R15",
        "D=M", # Loading y into D
        "@R14",
        "D=D-M",

        # Now we compare regularly
        f"(COMPARE_ELEMENTS_{relation}_{count})",
        f"@IS_TRUE_{relation}_{count}",
        f"D;{relation}",
        "D=0",
        f"@SET_RESULT_{relation}_{count}",
        "0;JMP",
        f"(IS_TRUE_{relation}_{count})",
        "D=-1",
        f"(SET_RESULT_{relation}_{count})",
        "@SP",
        "A=M-1",
        "M=D",
    ]

def get_dynamic_segment_addr_asm(segment, address):
    """
    Hack ASM code for access to keyworded segments (e.g. local)
    After calling this piece of code, the A register will hold
    the address requested for the memory segment
    """
    return [
        f"@{address}",
        "D=A",
        f"@{segment}",
        "A=D+M"
    ]

class CodeWriter:
    """Translates VM commands into Hack assembly code."""

    CONSTANT_SEGMENT_NOTATION = "constant"

    # Translating the name of each Dynamic Segment in 
    # VM language to the keyword of its address location
    # in ASM language.
    DYNAMIC_SEGMENTS_MAPPING = {
        "local": "LCL",
        "argument": "ARG",
        "this": "THIS",
        "that": "THAT"
    }

    # Storing the one-to-one mapping of each Fixed Segment
    # to its proper offset within the computer memory.
    FIXED_SEGMENTS_OFFSETS = {
        "temp": 5,
        "static": 16,
        "pointer": 3
    }

    def __init__(self) -> None:
        """
        Initializes the CodeWriter.
        """
        # Counting the amount of (in)equalities, so labels can be set properly
        # in the asm code
        self._eq_counter = 1
        self._lt_counter = 1
        self._gt_counter = 1

    # Arithmetic commands

    def vm_add(self) -> str:
        """
        Returning the Hack Assembly instructions for addition of
        2 numbers on the stack. Both input values are popped, and the
        result is pushed, hence the result is on top of the stack.
        """
        # We manually set the stack pointer to one position less, as we
        # pop two values and push one value
        return [
            "// add",
            "@SP",
            "M=M-1",
            "A=M",
            "D=M",
            "A=A-1",
            "M=D+M"
        ]

    def vm_sub(self) -> str:
        """
        Returning the Hack Assembly instructions for subtraction of
        2 numbers on the stack. Both input values are popped, and the
        result is pushed, hence the result is on top of the stack.
        """
        # Implementation is identical to addition, only final arithmetic is changed
        return [
            "// sub",
            "@SP",
            "M=M-1",
            "A=M",
            "D=-M",
            "A=A-1",
            "M=D+M"
        ]

    def vm_neg(self) -> str:
        """
        Returning the Hack Assembly instructions for negation of 
        a number on the stack.
        """
        # We don't pop/push anything, we just "hotfix" the value on
        # the stack directly
        return [
            "// neg",
            "@SP",
            "A=M-1",
            "M=-M"
        ]
    
    def vm_shiftleft(self) -> str:
        """
        Returning the Hack ASM for left-shifting the topmost item in the stack
        (unary operation)
        """
        return [
            "// shiftleft",
            "@SP",
            "A=M-1",
            "M=M<<"
        ]
    
    def vm_shiftright(self) -> str:
        """
        Returning the Hack ASM for right-shifting the topmost item in the stack
        (unary operation)
        """
        return [
            "// shiftright",
            "@SP",
            "A=M-1",
            "M=M>>"
        ]

    def vm_eq(self) -> str:
        """
        Returning Hack ASM for equality validation between the topmost 2
        items in the stack
        """
        # This is an optimzed version of the relation_asm function
        asm_code = [
            "// eq",
            "@SP",
            "M=M-1",
            "A=M",
            "D=M",
            "A=A-1",
            "D=D-M",
            f"@IS_TRUE_JEQ_{self._eq_counter}",
            f"D;JEQ",
            "D=0",
            f"@SET_RESULT_JEQ_{self._eq_counter}",
            "0;JMP",
            f"(IS_TRUE_JEQ_{self._eq_counter})",
            "D=-1",
            f"(SET_RESULT_JEQ_{self._eq_counter})",
            "@SP",
            "A=M-1",
            "M=D"
        ]
        self._eq_counter += 1
        return asm_code

    def vm_gt(self) -> str:
        """
        Returning Hack ASM for (strictly) greater-than between the
        topmost 2 items in the stack
        """
        asm_code = ["// gt"] + relation_asm(relation="JLT", count=self._gt_counter)
        self._gt_counter += 1
        return asm_code

    def vm_lt(self) -> str:
        """
        Returning the Hack ASM for (strictly) less-than between the topmost 
        2 items in the stack
        """
        asm_code = ["// lt"] + relation_asm(relation="JGT", count=self._lt_counter)
        self._lt_counter += 1
        return asm_code

    def vm_and(self) -> str:
        return [
            "// and",
            "@SP",
            "M=M-1",
            "A=M",
            "D=M",
            "A=A-1",
            "M=D&M"
        ]

    def vm_or(self) -> str:
        return [
            "// or",
            "@SP",
            "M=M-1",
            "A=M",
            "D=M",
            "A=A-1",
            "M=D|M"
        ]

    def vm_not(self) -> str:
        return [
            "// not",
            "@SP",
            "A=M-1",
            "M=!M"
        ]

    # Stack-manipulating commands

    def vm_push(self, segment: str, address: int) -> str:
        """
        Generating Hack ASM code for pushing into the stack
        from the requested segment, at the given address within.
        """
        asm_code = [f"// push {segment} {address}"]

        # First we wish to set the A register to the
        # requested address within the segment, and
        # then we set the D register to have the data
        # we wish to push into the stack
        if segment == CodeWriter.CONSTANT_SEGMENT_NOTATION:
            asm_code += [
                f"@{address}",
                "D=A"
            ]
        else:
            asm_code += CodeWriter._generate_segment_address(segment, address) + ["D=M"]

        # Placing the data we got from the memory segment 
        # (which, as we did in the previous stage, is in the D register)
        # into the stack & incrementing the stack pointer, 
        # a logic which is common to all cases
        asm_code += [
            "@SP",
            "A=M",
            "M=D",
            "@SP",
            "M=M+1"
        ]
        return asm_code

    def vm_pop(self, segment: str, address: int) -> str:
        """
        Generating Hack ASM code for popping from the stack
        into the requested segment, at the given address within.
        """
        # First we let A register hold the address to the location
        # which we want to pop into
        asm_code = [f"// pop {segment} {address}"] + \
                   CodeWriter._generate_segment_address(segment, address)
        
        # Here we save the address to the location we want to pop into (in R15)
        # and then we manipulate the SP, save the value in the stack, and
        # write it into the requested location (which was saved in R15)
        asm_code += [
            "D=A",
            "@R15",
            "M=D",
            "@SP",
            "M=M-1",
            "A=M",
            "D=M",
            "@R15",
            "A=M",
            "M=D"
        ]
        return asm_code
 
    @staticmethod
    def _generate_segment_address(segment: str, internal_address: int):
        """
        Calling this function will generate Hack ASM code which places
        the address to the requested address within a segment in the register A
        """
        # We generate the ASM code for accessing the requested address,
        # note that dynamic and fixed each have different ASM code
        if segment in CodeWriter.DYNAMIC_SEGMENTS_MAPPING:
            return get_dynamic_segment_addr_asm(
                segment=CodeWriter.DYNAMIC_SEGMENTS_MAPPING[segment], address=internal_address)
        else: # Fixed Segments
            return CodeWriter._generate_address_by_offset(
                CodeWriter.FIXED_SEGMENTS_OFFSETS[segment], internal_address)
        
    @staticmethod
    def _generate_address_by_offset(offset: int, address: int):
        """
        Generates the ASM code for accessing the data at the 
        given address, at the specified offset.
        """
        ram_offset = offset + address
        return [f"@{ram_offset}"]
