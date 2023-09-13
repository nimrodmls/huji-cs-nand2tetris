"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing

RELATIONS_ASM = \
"""@SP
M=M-1
A=M
D=M
A=A-1
D=D-M
@IS_TRUE_{relation}_{count}
D;{relation}
D=0
@SET_RESULT_{relation}_{count}
0;JMP
(IS_TRUE_{relation}_{count})
D=1
(SET_RESULT_{relation}_{count})
@SP
A=M-1
M=D\n"""

# Hack ASM code for access to keyworded segments (e.g. local)
# After calling this piece of code, the A register will hold
# the address requested for the memory segment
GET_ADDRESS_KEYWORDED_SEGMENT_ASM = \
"""@{address}
D=A
@{segment}
A=D+M\n"""

class CodeWriter:
    """Translates VM commands into Hack assembly code."""

    CONSTANT_SEGMENT_NOTATION = "constant"
    TEMP_SEGMENT_OFFSET = 5
    STATIC_SEGMENT_OFFSET = 16
    POINTER_SEGMENT_OFFSET = 3

    # TODO: Rename keyworded to dynamic and nonkeyworded to static

    # Translation from VM language segment keywords to
    # Hack Assembly segment keywords
    KEYWORDED_SEGMENTS = {
        "local": "LCL",
        "argument": "ARG",
        "this": "THIS",
        "that": "THAT"
    }

    # Handlers for all the non-keyworded segments (static addresses)
    NONKEYWORDED_SEGMENTS = {
        "temp": TEMP_SEGMENT_OFFSET,
        "static": STATIC_SEGMENT_OFFSET,
        "pointer": POINTER_SEGMENT_OFFSET
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
        return """// add
        @SP
        M=M-1
        A=M
        D=M
        A=A-1
        M=D+M\n"""

    def vm_sub(self) -> str:
        """
        Returning the Hack Assembly instructions for subtraction of
        2 numbers on the stack. Both input values are popped, and the
        result is pushed, hence the result is on top of the stack.
        """
        # Implementation is identical to addition, only final arithmetic is changed
        return """// sub
        @SP
        M=M-1
        A=M
        D=M
        A=A-1
        M=D-M\n"""

    def vm_neg(self) -> str:
        """
        Returning the Hack Assembly instructions for negation of 
        a number on the stack.
        """
        # We don't pop/push anything, we just "hotfix" the value on
        # the stack directly
        return """// neg
        @SP
        A=M-1
        M=-M\n"""

    def vm_eq(self) -> str:
        """
        """
        # 
        return "// eq\n" + RELATIONS_ASM.format(relation="JEQ", count=self._eq_counter)

    def vm_gt(self) -> str:
        """
        """
        # 
        return "// gt\n" + RELATIONS_ASM.format(relation="JLT", count=self._gt_counter)

    def vm_lt(self) -> str:
        """
        """
        # 
        return "// lt\n" + RELATIONS_ASM.format(relation="JGT", count=self._lt_counter)

    def vm_and(self) -> str:
        return """// and
        @SP
        M=M-1
        A=M
        D=M
        A=A-1
        M=D&M\n"""

    def vm_or(self) -> str:
        return """// and
        @SP
        M=M-1
        A=M
        D=M
        A=A-1
        M=D|M\n"""

    def vm_not(self) -> str:
        return """// neg
        @SP
        A=M-1
        M=!M\n"""

    # Stack-manipulating commands

    def vm_push(self, segment: str, address: int) -> str:
        """
        """
        asm_code = f"// push {segment} {address}\n"

        # First we wish to set the A register to the
        # requested address within the segment, and
        # then we set the D register to have the data
        # we wish to push into the stack
        if segment == CodeWriter.CONSTANT_SEGMENT_NOTATION:
            asm_code += f"""@{address}
            D=A\n"""
        else:
            asm_code += CodeWriter._generate_segment_address(segment, address) + "D=M\n"

        # Placing the data we got from the memory segment into 
        # the stack & incrementing the stack pointer, 
        # a logic which is common to all cases
        asm_code += """@SP
        A=M
        M=D
        @SP
        M=M+1\n"""
        return asm_code

    def vm_pop(self, segment: str, address: int) -> str:
        """
        """
        asm_code = f"// pop {segment} {address}\n" + CodeWriter._generate_segment_address(segment, address)
        #
        asm_code += """D=A
            @R15
            M=D
            @SP
            M=M-1
            A=M
            D=M
            @R15
            A=M
            M=D\n"""
        return asm_code

        
    @staticmethod
    def _generate_segment_address(segment: str, internal_address: int):
        """
        Calling this function will generate Hack ASM code which places
        the address to the requested address within a segment in the register A
        """
        if segment in CodeWriter.KEYWORDED_SEGMENTS:
            return GET_ADDRESS_KEYWORDED_SEGMENT_ASM.format(
                segment=CodeWriter.KEYWORDED_SEGMENTS[segment], address=internal_address)
        else:
            return CodeWriter.handle_segment_by_offset(
                CodeWriter.NONKEYWORDED_SEGMENTS[segment], internal_address)
        
    @staticmethod
    def handle_segment_by_offset(offset: int, address: int):
        """
        """
        ram_offset = offset + address
        return f"@{ram_offset}\n"
