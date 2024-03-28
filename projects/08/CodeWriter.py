"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
from typing import List

###################
# Common ASM code #
###################

def relation_asm(relation, count, uid):
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
        f"@NEGATIVE_X_{relation}_{count}_{uid}",
        "D;JLT", # If D < 0, we jump to NEGATIVE
        f"@R13",
        "M=0", # If D >= 0, we set the value of the register to 0
        f"@SAVE_SIGN_Y_{relation}_{count}_{uid}",
        "0;JMP", 
        f"(NEGATIVE_X_{relation}_{count}_{uid})", # If D < 0, we set the value of the register to -1
        f"@R13",
        "M=-1",

        # Save the sign of y in D
        f"(SAVE_SIGN_Y_{relation}_{count}_{uid})",
        # First loading y
        "@R15",
        "D=M",
        f"@NEGATIVE_Y_{relation}_{count}_{uid}",
        "D;JLT", # If D < 0, we jump to NEGATIVE
        "D=0", # If D >= 0, we set the value of the register to 0
        f"@COMPARE_SIGNS_{relation}_{count}_{uid}",
        "0;JMP",  # We saved both signs, now we compare them
        f"(NEGATIVE_Y_{relation}_{count}_{uid})", # If D < 0, we set the value of the register to -1
        "D=-1",
        
        # At this point, we have the signs of x in R13 and of y in D
        # We check whether the signs and the same by subtracting them
        f"(COMPARE_SIGNS_{relation}_{count}_{uid})",
        "@R13",
        "D=D-M", # Subtracting the sign of y from the sign of x
        f"@COMPARE_ELEMENTS_{relation}_{count}_{uid}",
        "D;JNE", # If the signs are inequal, we can compare directly

        # Otherwise, they are with equal signs, we need to subtract x and y
        # at this point we don't need the signs saved at R13 and D
        "@R15",
        "D=M", # Loading y into D
        "@R14",
        "D=D-M",

        # Now we compare regularly
        f"(COMPARE_ELEMENTS_{relation}_{count}_{uid})",
        f"@IS_TRUE_{relation}_{count}_{uid}",
        f"D;{relation}",
        "D=0",
        f"@SET_RESULT_{relation}_{count}_{uid}",
        "0;JMP",
        f"(IS_TRUE_{relation}_{count}_{uid})",
        "D=-1",
        f"(SET_RESULT_{relation}_{count}_{uid})",
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

# Generic Hack ASM code for pushing the 
# value within the D register into the stack
GENERIC_PUSH_D_REGISTER_ASM = [
    "@SP",
    "A=M",
    "M=D",
    "@SP",
    "M=M+1"
]

class CodeWriter:
    """Translates VM commands into Hack assembly code."""

    CONSTANT_SEGMENT_NOTATION = "constant"
    STATIC_SEGMENT_NOTATION = "static"

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
        "pointer": 3
    }

    def __init__(self, unique_id: str) -> None:
        """
        Initializes the CodeWriter.
        @param unique_id: Unique Identifier for labeling
        """
        self._uid = unique_id.upper()
        # Counting the amount of (in)equalities, so labels can be set properly
        # in the asm code
        self._eq_counter = 1
        self._lt_counter = 1
        self._gt_counter = 1
        # Counting the amount of calls, so labels can be set properly
        # for each return address of each call
        self._call_count = 1

    def vm_bootstrap(self) -> str:
        """
        """
        return [
            "// VM Bootstrap",
            "@256",
            "D=A",
            "@SP",
            "M=D"
        ] + self.vm_call("Sys.init", 0)

    #######################
    # Arithmetic commands #
    #######################

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
            f"@IS_TRUE_JEQ_{self._eq_counter}_{self._uid}",
            f"D;JEQ",
            "D=0",
            f"@SET_RESULT_JEQ_{self._eq_counter}_{self._uid}",
            "0;JMP",
            f"(IS_TRUE_JEQ_{self._eq_counter}_{self._uid})",
            "D=-1",
            f"(SET_RESULT_JEQ_{self._eq_counter}_{self._uid})",
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
        asm_code = ["// gt"] + relation_asm(relation="JLT", count=self._gt_counter, uid=self._uid)
        self._gt_counter += 1
        return asm_code

    def vm_lt(self) -> str:
        """
        Returning the Hack ASM for (strictly) less-than between the topmost 
        2 items in the stack
        """
        asm_code = ["// lt"] + relation_asm(relation="JGT", count=self._lt_counter, uid=self._uid)
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

    ###############################
    # Stack-manipulating commands #
    ###############################

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
            asm_code += self._generate_segment_address(segment, address) + ["D=M"]

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
                   self._generate_segment_address(segment, address)
        
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
 
    ######################
    # Branching Commands #
    ######################

    def vm_label(self, name: str):
        """
        Generating Hack ASM code for labeling the current location in the code
        for jumping to it in a later stage.
        """
        # The code is simply an Hack ASM label
        return [
            f"// label {name}",
            f"({name}_{self._uid})"
            ]

    def vm_goto(self, label_name: str):
        """
        """
        # Loading the address to the label (assuming it was defined!)
        # and simply jumping to it
        return [
            f"// goto {label_name}",
            f"@{label_name}_{self._uid}",
            "0;JMP"
        ]

    def vm_if_goto(self, label_name: str):
        """
        """
        asm_code = [f"// if-goto {label_name}"]

        # "Popping" the topmost value of the stack
        # and using it to determine whether a jump should be
        # performed (only upon the topmost value being nonzero)
        asm_code += [
            "@SP",
            "M=M-1",
            "A=M",
            "D=M",
            f"@{label_name}_{self._uid}",
            "D;JNE"
        ]

        return asm_code

    #####################
    # Function Commands #
    #####################

    def vm_function(self, name: str, local_var_count: int):
        """
        """
        asm_code = [f"// function {name} {local_var_count}"]

        func_label = name.upper()
        asm_code += [f"({func_label})"]

        if 0 < local_var_count:
            asm_code += [
                f"({func_label})",
                f"@{local_var_count}",
                "D=A",
                "@R15", # We use R15 for the iteration counter of the loop
                f"M=D",
                f"({func_label}_INIT_LOOP)", # Starting an initialization loop
                "@SP", # The next few lines is a push operation of 0
                "A=M",
                "M=0",
                "@SP",
                "M=M+1",
                "@R15", # Now we decrement the loop iteration counter
                "M=M-1",
                "D=M",
                f"@{func_label}_INIT_LOOP",
                "D;JNE" # The loop continues if and only if the iteration counter is not 0
            ]

        return asm_code

    def vm_call(self, func_name: str, argument_count: int):
        """
        """
        asm_code = [f"// call {func_name} {argument_count}"]
        func_label = func_name.upper()
        
        # Generic Hack ASM code for pushing a Dynamic Segment's Address
        # into the stack (as the regular vm_push is using segment names)
        push_dynamic_segment_address_asm = lambda segment: [
            f"@{segment}", 
            "D=M", # Getting the segment address and place it in D register
        ] + GENERIC_PUSH_D_REGISTER_ASM

        # Now we begin to push everything we need onto the stack
        # First we push the return address 
        # (it is labeled, for example - RET_FOO.BAR_1, 
        # with FOO being the function name, BAR the file name, 
        # and 1 the call count e.g. how many calls preceeded in this file)
        return_label = f"RET_{func_label}_{self._call_count}_{self._uid}"
        asm_code += [
            f"@{return_label}",
            "D=A" # We place the return address in the D register
        ] + GENERIC_PUSH_D_REGISTER_ASM

        # Pushing all the segment addresses
        asm_code += push_dynamic_segment_address_asm(segment="LCL")
        asm_code += push_dynamic_segment_address_asm(segment="ARG")
        asm_code += push_dynamic_segment_address_asm(segment="THIS")
        asm_code += push_dynamic_segment_address_asm(segment="THAT")

        # Setting the new ARG to point on the stack 
        # where we were BEFORE pushing the frame
        asm_code += [
            "@SP",
            "D=M", # D contains the stack pointer
            "@5",
            "D=D-A", # Now we calculate SP-5 (which is D-5)
            f"@{argument_count}",
            "D=D-A", # Now we calculate SP-5-nArgs
            "@ARG", # Setting ARG as needed
            "M=D",
        ]

        # Setting the local segment ptr to the current stack pointer
        asm_code += [
            "@SP",
            "D=M",
            "@LCL",
            "M=D",
        ]

        # Jumping to the function unconditionally, and setting the return label
        asm_code += [
            f"@{func_label}",
            "0;JMP",
            f"({return_label})"
        ]

        # Incrementing the call count in order to allow multiple calls to the same function(s)
        self._call_count += 1

        return asm_code

    def vm_return(self):
        """
        """
        # Generic Hack ASM code for getting data from a certain offset within the call frame,
        # the data is then put into the D register
        get_data_from_frame_asm = lambda offset: [
            "@R15", # R15 holds the ptr to the END of the frame
            "D=M",
            f"@{offset}",
            "A=D-A", # Going to where the previous segment address is stored
            "D=M", # Storing the ptr to the segment in D
        ]

        asm_code = ["// return"]

        # Storing the end of the call frame in R15
        asm_code += [
            "@LCL",
            "D=M",
            "@R15",
            "M=D"
        ]

        # Storing the return address into R14. If this not done here, then
        # in case no arguments are passed to the function, the return value
        # will overrun the return address, causing returning to invalid location
        asm_code += get_data_from_frame_asm(offset=5) + [
            "@R14",
            "M=D"
        ]

        # Giving the return value to the caller (by "replacing" all the arguments)
        # the caller had given to the function, with the return value
        asm_code += [
            "@SP",
            "A=M-1",
            "D=M",
            "@ARG",
            "A=M",
            "M=D",
        ]

        # Repositioning the stack pointer to be just after the return value
        # we just set in the code above
        asm_code += [
            "@ARG",
            "D=M+1",
            "@SP",
            "M=D"
        ]

        # Generic Hack ASM code for restoring a segment address from a call frame
        restore_segment_ptr_from_frame_asm = lambda segment, offset: get_data_from_frame_asm(offset) + [
            f"@{segment}",
            "M=D" # This actually restores the segment ptr with D
        ]

        # Restoring all segment addresses from the call frame
        asm_code += restore_segment_ptr_from_frame_asm(offset=1, segment="THAT")
        asm_code += restore_segment_ptr_from_frame_asm(offset=2, segment="THIS")
        asm_code += restore_segment_ptr_from_frame_asm(offset=3, segment="ARG")
        asm_code += restore_segment_ptr_from_frame_asm(offset=4, segment="LCL")

        # Jumping to the return address unconditionally
        # NOTE: It is possible to optimize this code, since get_data_from_frame_asm
        #       does D=M and then here we do A=D, can be simplified to A=M,
        #       but it is left this way in the sake of simplicity of this Python code
        asm_code += [
            "@R14",
            "A=M",
            "0;JMP"
        ]

        return asm_code

    #####################
    # Utility functions #
    #####################

    def _generate_segment_address(self, segment: str, internal_address: int) -> str:
        """
        Calling this function will generate Hack ASM code which places
        the address to the requested address within a segment in the register A
        """
        # We generate the ASM code for accessing the requested address,
        # note that dynamic and fixed each have different ASM code
        if segment in CodeWriter.DYNAMIC_SEGMENTS_MAPPING:
            return get_dynamic_segment_addr_asm(
                segment=CodeWriter.DYNAMIC_SEGMENTS_MAPPING[segment], address=internal_address)
        # Static segment is a special case
        elif CodeWriter.STATIC_SEGMENT_NOTATION == segment:
            return [f"@{self._uid}.STATIC_VAR.{internal_address}"]
        else: # Fixed Segments
            return CodeWriter._generate_address_by_offset(
                CodeWriter.FIXED_SEGMENTS_OFFSETS[segment], internal_address)
        
    @staticmethod
    def _generate_address_by_offset(offset: int, address: int) -> str:
        """
        Generates the ASM code for accessing the data at the 
        given address, at the specified offset.
        """
        ram_offset = offset + address
        return [f"@{ram_offset}"]
