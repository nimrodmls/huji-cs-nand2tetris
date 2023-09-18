"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
from typing import List

def concat_asm_code(asm: List[str]) -> str:
    """
    Simply concates a series of asm commands (or any string, really)
    into a text format for asm (e.g. every element is in its own line)
    """
    return "\n".join(asm + [""])

RELATIONS_ASM = concat_asm_code(
    ["@SP",
     "M=M-1",
     "A=M",
     "D=M",
     "A=A-1",
     "D=D-M",
     "@IS_TRUE_{relation}_{count}",
     "D;{relation}",
     "D=0",
     "@SET_RESULT_{relation}_{count}",
     "0;JMP",
     "(IS_TRUE_{relation}_{count})",
     "D=1",
     "(SET_RESULT_{relation}_{count})",
     "@SP",
     "A=M-1",
     "M=D"
     ])

# Hack ASM code for access to keyworded segments (e.g. local)
# After calling this piece of code, the A register will hold
# the address requested for the memory segment
GET_DYNAMIC_SEGMENT_ADDR_ASM = concat_asm_code(
    ["@{address}",
    "D=A",
    "@{segment}",
    "A=D+M"
])

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
        return "// add\n" + concat_asm_code(
            ["@SP",
             "M=M-1",
             "A=M",
             "D=M",
             "A=A-1",
             "M=D+M"
            ])

    def vm_sub(self) -> str:
        """
        Returning the Hack Assembly instructions for subtraction of
        2 numbers on the stack. Both input values are popped, and the
        result is pushed, hence the result is on top of the stack.
        """
        # Implementation is identical to addition, only final arithmetic is changed
        return "// sub\n" + concat_asm_code(
            ["@SP",
             "M=M-1",
             "A=M",
             "D=M",
             "A=A-1",
             "M=D-M"
            ])

    def vm_neg(self) -> str:
        """
        Returning the Hack Assembly instructions for negation of 
        a number on the stack.
        """
        # We don't pop/push anything, we just "hotfix" the value on
        # the stack directly
        return "// neg\n" + concat_asm_code(
            ["@SP",
             "A=M-1",
             "M=-M"
            ])

    def vm_eq(self) -> str:
        """
        Returning Hack ASM for equality validation between the topmost 2
        items in the stack
        """
        return "// eq\n" + RELATIONS_ASM.format(relation="JEQ", count=self._eq_counter)

    def vm_gt(self) -> str:
        """
        Returning Hack ASM for (strictly) greater-than between the
        topmost 2 items in the stack
        """
        return "// gt\n" + RELATIONS_ASM.format(relation="JLT", count=self._gt_counter)

    def vm_lt(self) -> str:
        """
        Returning the Hack ASM for (strictly) less-than between the topmost 
        2 items in the stack
        """
        return "// lt\n" + RELATIONS_ASM.format(relation="JGT", count=self._lt_counter)

    def vm_and(self) -> str:
        return "// and\n" + concat_asm_code(
            ["@SP",
             "M=M-1",
             "A=M",
             "D=M",
             "A=A-1",
             "M=D&M"
            ])

    def vm_or(self) -> str:
        return "// or\n" + concat_asm_code(
            ["@SP",
             "M=M-1",
             "A=M",
             "D=M",
             "A=A-1",
             "M=D|M"
            ])

    def vm_not(self) -> str:
        return "// not\n" + concat_asm_code(
            ["@SP",
             "A=M-1",
             "M=!M"
            ])

    # Stack-manipulating commands

    def vm_push(self, segment: str, address: int) -> str:
        """
        Generating Hack ASM code for pushing into the stack
        from the requested segment, at the given address within.
        """
        asm_code = f"// push {segment} {address}\n"

        # First we wish to set the A register to the
        # requested address within the segment, and
        # then we set the D register to have the data
        # we wish to push into the stack
        if segment == CodeWriter.CONSTANT_SEGMENT_NOTATION:
            asm_code += concat_asm_code(
                [f"@{address}",
                 "D=A"])
        else:
            asm_code += CodeWriter._generate_segment_address(segment, address) + "D=M\n"

        # Placing the data we got from the memory segment 
        # (which, as we did in the previous stage, is in the D register)
        # into the stack & incrementing the stack pointer, 
        # a logic which is common to all cases
        asm_code += concat_asm_code(
            ["@SP",
             "A=M",
             "M=D",
             "@SP",
             "M=M+1"])
        return asm_code

    def vm_pop(self, segment: str, address: int) -> str:
        """
        Generating Hack ASM code for popping from the stack
        into the requested segment, at the given address within.
        """
        # First we let A register hold the address to the location
        # which we want to pop into
        asm_code = f"// pop {segment} {address}\n" + \
                   CodeWriter._generate_segment_address(segment, address)
        
        # Here we save the address to the location we want to pop into (in R15)
        # and then we manipulate the SP, save the value in the stack, and
        # write it into the requested location (which was saved in R15)
        asm_code += concat_asm_code(
                    ["D=A",
                     "@R15",
                     "M=D",
                     "@SP",
                     "M=M-1",
                     "A=M",
                     "D=M",
                     "@R15",
                     "A=M",
                     "M=D"])
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
            return GET_DYNAMIC_SEGMENT_ADDR_ASM.format(
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
        return f"@{ram_offset}\n"
