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

###################
# Common ASM code #
###################

# Generic Hack ASM code for each of the (in)equality relations
# given by the VM language
RELATIONS_ASM = concat_asm_code(
    ["@SP",
     "M=M-1",
     "A=M",
     "D=M",
     "A=A-1",
     "D=D-M",
     "@IS_TRUE_{relation}_{uid}_{count}",
     "D;{relation}",
     "D=0",
     "@SET_RESULT_{relation}_{uid}_{count}",
     "0;JMP",
     "(IS_TRUE_{relation}_{uid}_{count})",
     "D=-1",
     "(SET_RESULT_{relation}_{uid}_{count})",
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

# Generic Hack ASM code for pushing the 
# value within the D register into the stack
GENERIC_PUSH_D_REGISTER_ASM = concat_asm_code([
    "@SP",
    "A=M",
    "M=D",
    "@SP",
    "M=M+1"
])

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
        return "// VM Bootstrap\n" + concat_asm_code([
            "@256",
            "D=A",
            "@SP",
            "M=D"
        ]) + self.vm_call("Sys.init", 0)

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
             "D=-M",
             "A=A-1",
             "M=D+M"
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
        asm_code = "// eq\n" + RELATIONS_ASM.format(
            relation="JEQ", uid=self._uid, count=self._eq_counter)
        self._eq_counter += 1
        return asm_code

    def vm_gt(self) -> str:
        """
        Returning Hack ASM for (strictly) greater-than between the
        topmost 2 items in the stack
        """
        asm_code = "// gt\n" + RELATIONS_ASM.format(
            relation="JLT", uid=self._uid, count=self._gt_counter)
        self._gt_counter += 1
        return asm_code

    def vm_lt(self) -> str:
        """
        Returning the Hack ASM for (strictly) less-than between the topmost 
        2 items in the stack
        """
        asm_code = "// lt\n" + RELATIONS_ASM.format(
            relation="JGT", uid=self._uid, count=self._lt_counter)
        self._lt_counter += 1
        return asm_code

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

    ###############################
    # Stack-manipulating commands #
    ###############################

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
            asm_code += self._generate_segment_address(segment, address) + "D=M\n"

        # Placing the data we got from the memory segment 
        # (which, as we did in the previous stage, is in the D register)
        # into the stack & incrementing the stack pointer, 
        # a logic which is common to all cases
        asm_code += GENERIC_PUSH_D_REGISTER_ASM
        return asm_code

    def vm_pop(self, segment: str, address: int) -> str:
        """
        Generating Hack ASM code for popping from the stack
        into the requested segment, at the given address within.
        """
        # First we let A register hold the address to the location
        # which we want to pop into
        asm_code = f"// pop {segment} {address}\n" + \
                   self._generate_segment_address(segment, address)
        
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
 
    ######################
    # Branching Commands #
    ######################

    def vm_label(self, name: str):
        """
        Generating Hack ASM code for labeling the current location in the code
        for jumping to it in a later stage.
        """
        # The code is simply an Hack ASM label
        return f"// label {name}\n" + concat_asm_code([f"({name})"])

    def vm_goto(self, label_name: str):
        """
        """
        asm_code = f"// goto {label_name}\n"
        # Loading the address to the label (assuming it was defined!)
        # and simply jumping to it
        asm_code += concat_asm_code([
            f"@{label_name}",
            "0;JMP"
        ])

        return asm_code

    def vm_if_goto(self, label_name: str):
        """
        """
        asm_code = f"// if-goto {label_name}\n"

        # "Popping" the topmost value of the stack
        # and using it to determine whether a jump should be
        # performed (only upon the topmost value being nonzero)
        asm_code += concat_asm_code([
            "@SP",
            "M=M-1",
            "A=M",
            "D=M",
            f"@{label_name}",
            "D;JNE"
        ])

        return asm_code

    #####################
    # Function Commands #
    #####################

    def vm_function(self, name: str, local_var_count: int):
        """
        """
        asm_code = f"// function {name} {local_var_count}\n"

        func_label = name.upper() # self.add_uid(name.upper())
        asm_code += f"({func_label})\n"

        if 0 < local_var_count:
            asm_code += concat_asm_code([
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
            ])

        return asm_code

    def vm_call(self, func_name: str, argument_count: int):
        """
        """
        asm_code = f"// call {func_name} {argument_count}\n"
        func_label = func_name.upper() # self.add_uid(func_name.upper())
        
        # Generic Hack ASM code for pushing a Dynamic Segment's Address
        # into the stack (as the regular vm_push is using segment names)
        push_dynamic_segment_address_asm = concat_asm_code([
            "@{segment}", 
            "D=M", # Getting the segment address and place it in D register
        ]) + GENERIC_PUSH_D_REGISTER_ASM

        # Now we begin to push everything we need onto the stack
        # First we push the return address 
        # (it is labeled, for example - RET_FOO.BAR_1, 
        # with FOO being the function name, BAR the file name, 
        # and 1 the call count e.g. how many calls preceeded in this file)
        return_label = f"RET_{func_label}_{self._call_count}"
        asm_code += concat_asm_code([
            f"@{return_label}",
            "D=A" # We place the return address in the D register
        ]) + GENERIC_PUSH_D_REGISTER_ASM

        # Pushing all the segment addresses
        asm_code += push_dynamic_segment_address_asm.format(segment="LCL")
        asm_code += push_dynamic_segment_address_asm.format(segment="ARG")
        asm_code += push_dynamic_segment_address_asm.format(segment="THIS")
        asm_code += push_dynamic_segment_address_asm.format(segment="THAT")

        # Setting the new ARG to point on the stack 
        # where we were BEFORE pushing the frame
        asm_code += concat_asm_code([
            "@SP",
            "D=M", # D contains the stack pointer
            "@5",
            "D=D-A", # Now we calculate SP-5 (which is D-5)
            f"@{argument_count}",
            "D=D-A", # Now we calculate SP-5-nArgs
            "@ARG", # Setting ARG as needed
            "M=D",
        ])

        # Setting the local segment ptr to the current stack pointer
        asm_code += concat_asm_code([
            "@SP",
            "D=M",
            "@LCL",
            "M=D",
        ])

        # Jumping to the function unconditionally, and setting the return label
        asm_code += concat_asm_code([
            f"@{func_label}",
            "0;JMP",
            f"({return_label})"
        ])

        # Incrementing the call count in order to allow multiple calls to the same function(s)
        self._call_count += 1

        return asm_code

    def vm_return(self):
        """
        """
        # Generic Hack ASM code for getting data from a certain offset within the call frame,
        # the data is then put into the D register
        get_data_from_frame_asm = concat_asm_code([
            "@R15", # R15 holds the ptr to the END of the frame
            "D=M",
            "@{offset}",
            "A=D-A", # Going to where the previous segment address is stored
            "D=M", # Storing the ptr to the segment in D
        ])

        asm_code = "// return\n"

        # Storing the end of the call frame in R15
        asm_code += concat_asm_code([
            "@LCL",
            "D=M",
            "@R15",
            "M=D"
        ])

        # Storing the return address into R14. If this not done here, then
        # in case no arguments are passed to the function, the return value
        # will overrun the return address, causing returning to invalid location
        asm_code += get_data_from_frame_asm.format(offset=5) + concat_asm_code([
            "@R14",
            "M=D"
        ])

        # Giving the return value to the caller (by "replacing" all the arguments)
        # the caller had given to the function, with the return value
        asm_code += concat_asm_code([
            "@SP",
            "A=M-1",
            "D=M",
            "@ARG",
            "A=M",
            "M=D",
        ])

        # Repositioning the stack pointer to be just after the return value
        # we just set in the code above
        asm_code += concat_asm_code([
            "@ARG",
            "D=M+1",
            "@SP",
            "M=D"
        ])

        # Generic Hack ASM code for restoring a segment address from a call frame
        restore_segment_ptr_from_frame_asm = get_data_from_frame_asm + concat_asm_code([
            "@{segment}",
            "M=D" # This actually restores the segment ptr with D
        ])

        # Restoring all segment addresses from the call frame
        asm_code += restore_segment_ptr_from_frame_asm.format(offset=1, segment="THAT")
        asm_code += restore_segment_ptr_from_frame_asm.format(offset=2, segment="THIS")
        asm_code += restore_segment_ptr_from_frame_asm.format(offset=3, segment="ARG")
        asm_code += restore_segment_ptr_from_frame_asm.format(offset=4, segment="LCL")

        # Jumping to the return address unconditionally
        # NOTE: It is possible to optimize this code, since get_data_from_frame_asm
        #       does D=M and then here we do A=D, can be simplified to A=M,
        #       but it is left this way in the sake of simplicity of this Python code
        asm_code += concat_asm_code([
            "@R14",
            "A=M",
            "0;JMP"
        ])

        return asm_code

    #####################
    # Utility functions #
    #####################

    def add_uid(self, id: str) -> str:
        """
        Simply adding the unique identifier to the given string
        """
        return id + "." + self._uid
    
    def _generate_segment_address(self, segment: str, internal_address: int) -> str:
        """
        Calling this function will generate Hack ASM code which places
        the address to the requested address within a segment in the register A
        """
        # We generate the ASM code for accessing the requested address,
        # note that dynamic and fixed each have different ASM code
        if segment in CodeWriter.DYNAMIC_SEGMENTS_MAPPING:
            return GET_DYNAMIC_SEGMENT_ADDR_ASM.format(
                segment=CodeWriter.DYNAMIC_SEGMENTS_MAPPING[segment], 
                address=internal_address)
        # Static segment is a special case
        elif CodeWriter.STATIC_SEGMENT_NOTATION == segment:
            return concat_asm_code([
                f"@{self._uid}.STATIC_VAR.{internal_address}"
            ])
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
        return f"@{ram_offset}\n"
