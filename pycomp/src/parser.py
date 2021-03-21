#!/usr/bin/env python3

# idea:
# consider parsing bottom up
# could make things easier like function call:
# x.y.z(asdf)
# x->y->z(asdf)

# TODO:
# some operators
# add Null and NullType
# void type
# cast, sizeof
# allow double declaration, only single definition (var, function)
# if, while, scope blocks
# various number types
#
# for expression typechecking:
#  can require immediacy (no dependencies)
#  if is immediate: can call eval on it: returns some "leaf" AST object that can replace the currently "recursive" AST object
#  use numpy for static evaluations
#
# general typechecking done in typecheck
# but expressions etc have to be checked during code gen
# there we have to do all the automatic casting anyway
# 
# Code Generation:
#   CodeCtx
#   - linear blocks for: functions, globals
#   - facility to read from name, write to name (probably more complex)
#   - facility to evaluate expressions:
#     - return immediate or <some var ref?>
#   - facility to open functions, scopes, if, while, ...
#   - How to deal with var-ref?
#     - just place at distance of bp/sp.
#     - really sloppy, even intermediates go to stack, need lots of stack space - but no register optimization needed.
#     - general idea: push bp, bp=sp (now aligned). Move all args to stack. Also push callee-saved regs. Keep last result in eax, but can push if need a second branch
#     - basically we are having a stack machine.
#     - Ok, return is either value, or a reg., and a type info
#     - local variables are at offset from bp (also args)
#     
#     - new idea: expressions can return immediate, or rax/eax.
#     - if an op takes multiple sub-expressions: might have to temp store rax/eax in a temp local var (like spilling)
#     - return: just write value to rax/eax, restore sp/bp, ret
#     - struct on stack: check alignment, alloc/dealloc - probably make variables know how much they allocated!
#     - function call: map args to reg (rdi/xmm0...) and if needed to memory. Get offset with alignment for new sp, place in memory args.
#     - scope: has stack of variables -> can dealloc at end.
#     - caller-saved: eax,ecx,edx - can use them to manouver in an expression part
#
#
# preprocessor:
# - import (header) files
#   -> recursive error reporting!
# - DEFINE abc = abcde
#   -> chaon of tokens?
# - token should internally refer to lex and parent token
# - then we can use DEFINE, import etc
# - when name is parsed: check if in DEFINE dictionary:
#   -> append copy of all tokens in DEFINE list
#   -> could even do function style later on
#
# could also be nice:
# add syntactic sugar: x[y] -> *(x+y)
# add stack array?

# Figure out types of everything:
# 1) list of all structs
# 2) type of struct members: check for cycles!
# 3) type of functions
# 4) type of globals
# 5) check expressions of globals (maybe very shallow???)
# 6) move though function body:
#       check name availability
#       check type compatibility
#       check if const violated

# then can start thinking about asm-generation

import sys
import os
from collections import deque
import lexer
import math
import numpy as np # for c style value calculations

class Parser():
    """Parses tokens into ParseTree pt
    
    Method: sequential application of scanning rules.
    
    Node of pt: (isToken, payload)
    if token:       payload = Token
    else (pt node): payload = (consumed tokens, list of list of Nodes)
    
    Idea: rules are applied on a list of Nodes

    Note: in a second step we turn the pt into an ast
    """
    def __init__(self):
        self.rules = []
    
    def parse_apply_rule(self, rule, pt):
        """traversal impl for parse"""
        # Traversal bottom up (post order)
        
        isToken, payload = pt
        if not isToken:
            tokens, listoflists = payload
            # recurse
            listoflists = [[self.parse_apply_rule(rule, i) for i in l] for l in listoflists]
            # post order
            listoflists = [rule(l) for l in listoflists]
            
            # reconstruct pt node
            return (False,(tokens, listoflists))
        else:
            return pt # just return token

    def parse(self,tokens):
        """
        Input: tokens from lexer
        Output: pt
        """
        lst = [(True,t) for t in tokens]
        pt = (False, ([], [lst]))
        for rule in self.rules:
            # Traverse old pt, generate a new one
            pt = self.parse_apply_rule(rule, pt)
        return pt

    def set_rules(self,rules):
        """
        rules: list of rules
        rule is a function: rule(nodes) -> new node list
        """
        self.rules = rules

    def print_parse_tree(self, pt, depth=0,step=3):
        """purely for debugging purposes"""
        isToken, payload = pt
        if isToken:
            tk = payload
            print(" "*depth + f"<{tk.name:10}> {tk.value}")
        else:
            tokens,listoflists = payload
            for t in tokens:
                print(" "*depth + f"[{t.name:10}] {t.value}")
            i = 0
            for l in listoflists:
                print(" "*depth + f"#{i}")
                i+=1
                for el in l:
                    self.print_parse_tree(el,depth=depth+step)


class BasicParser(Parser):
    """
    Parser that is initialized with rules to parse
    token list into parse tree pt
    - recursive brackets (){}[]
    - comma/semicolon sequences
    - operator separation sequences
    """
    def __init__(self):
        super().__init__()

        ### set up rules

        def rule_brackets(nodes):
            q = deque() # stores (begin-token, new_nodes)
            cur_nodes = []
            cur_token = None
            
            bracket_map = {
                    ")":"(",
                    "]":"[",
                    "}":"{",
                    }

            for pt in nodes:
                isToken,payload = pt
                if isToken:
                    tk = payload
                    if tk.name == "bracket":
                        if tk.value in bracket_map:
                            # close bracket
                            # check if there is an opening bracket:
                            if cur_token is None:
                                print("ParseError: missing opening bracket.")
                                tk.mark()
                                quit()
                            
                            # check if matches cur_token
                            expect = bracket_map[tk.value]
                            cur_token_val = cur_token.value

                            if cur_token_val == expect:
                                # create a new bracket pt node:
                                new_node = (False,([cur_token,tk],[cur_nodes]))
                                # pop from stack
                                cur_token, cur_nodes = q.pop()

                                # insert new node
                                cur_nodes.append(new_node)
                            else:
                                print("ParseError: closing bracket did not match with opening bracket.")
                                cur_token.mark()
                                token.mark()
                                quit()

                        else:
                            # open bracket
                            # push cur to stack
                            q.append((cur_token,cur_nodes))
                            cur_token = tk
                            cur_nodes = []
                    else:
                        cur_nodes.append(pt)
                else:
                    cur_nodes.append(pt)

            # check if all brackets were matched:
            if not cur_token is None:
                print("ParseError: opening bracket without closing bracket.")
                cur_token.mark()
                quit()

            return cur_nodes
        
        def rule_delimiter_factory(token_list):
            """generates a rule that splits lists whereever a token is matched
            token_list = list of (tname,tval)
            if no such token is found the nodelist will be untouched.
            else, we list all n tokens and all n+1 sublists.
            """
            token_dict = {t:0 for t in token_list}

            def rule(nodes):
                # check for occurances:
                occ = 0
                for pt in nodes:
                    isToken,payload = pt
                    if isToken:
                        tk = payload
                        key = (tk.name,tk.value)
                        if key in token_dict:
                            occ += 1

                if occ == 0:
                    return nodes

                # split the list
                tokens = []
                listoflists = []
                cur_nodes = []
                for pt in nodes:
                    isToken,payload = pt
                    if isToken:
                        tk = payload
                        key = (tk.name,tk.value)
                        if key in token_dict:
                            tokens.append(payload)
                            listoflists.append(cur_nodes)
                            cur_nodes = []
                        else:
                            cur_nodes.append(pt)
                    else:
                        cur_nodes.append(pt)
                # append the n+1 st list
                listoflists.append(cur_nodes)

                new_node = (False,(tokens,listoflists))
                return [new_node]


            return rule

        rules = [ 
            rule_brackets,
            rule_delimiter_factory([("semicolon",";")]),
            rule_delimiter_factory([("comma",",")]),
            ]
        
        # list of operators (lowest precedence first):
        list_of_operators = [
                # assign
                ["=","+=","-=","/=","*="],
                # logic
                ["||"],
                ["&&"],
                # bitwise
                ["|"],
                ["^"],
                ["&"],
                # equal
                ["==","!="],
                # cmp
                ["<", ">", "<=", ">="],
                # bitwise shift
                ["<<",">>"],
                # arith
                ["+","-"],
                ["*","/","%"],
                # unary not
                ["!","~"],
                # inc, dec
                ["++","--"],
                # pointer
                ["->","."],
                ]

        for l in list_of_operators:
            rules.append(rule_delimiter_factory([("operator",i) for i in l]))

        self.set_rules(rules)

# #######################################
# ######## PT-Parser section ############
# #######################################

class ASTObject():
    """AST object template, used for PTParse.
    Must implement all member functions below
    """

    def __init__(self, pt):
        """
        pt: what it was generated from
        """
        assert(False and "cannot instantiate")

    def print_ast(self,depth=0,step=3):
        """recursive print the ast"""
        print(" "*depth + f"<print_ast Error: Not implemented! {type(self)}>")
    
    def token(self):
        """return token that points at this object"""
        print(f"type: {type(self)}")
        assert(False and "token() not implemented")
    
    def typecheck(self):
        """
        Used by ASTObjectBase only:
        determines types
        checks for automatic conversions
        checks if types consistent
        """
        print(type(self))
        assert(False and "typecheck not implemented")
    
class TypeCTX:
    """
    Keeps information about types
    But also available constants/initial variable values
    """
    def __init__(self):
        # look up type name for ASTObjectType
        self.typeforname = {}
        self.sizeforname = {}
        self.alignmentforname = {}
        self.structmemberoffset = {}

        # add all number types:
        for name,size in ASTObjectTypeNumber_types.items():
            ast = ASTObjectTypeNumber(None,name)
            self.typeforname[name] = ast
            self.sizeforname[name] = size
            self.alignmentforname[name] = size
    
    def type_size(self,asttype):
        """byte size of an ast type"""
        if asttype.isPointer():
            return 8
        else:
            return self.sizeforname[asttype.name]
    def type_alignment(self,asttype):
        """alignment in bytes, of an ast type"""
        if asttype.isPointer():
            return 8
        else:
            return self.alignmentforname[asttype.name]
            
    def check_function_signatures(self,functions):
        """type check dict of functions (their signatures)
        call this after register_structs
        """
        for name,func in functions.items():
            func.checkSignature(self)
            
    def check_globals(self,varconsts):
        """type check dict of globals (varconst)
        call this after register_structs
        """
        for name,var in varconsts.items():
            var.checkType(self)

    def register_structs(self,structs):
        """Register and type check dict of structs"""
        needed = {}
        needed_cnt = {}
        for name,struct in structs.items():
            ast = ASTObjectTypeStruct(None,struct.token())
            self.typeforname[name] = ast
            self.structmemberoffset[name] = {}
            needed[name] = {}
            needed_cnt[name] = 0
        
        # build dependency structure
        for name,struct in structs.items():
            for exp in struct.body:
                # exp is ASTObjectExpressionDeclaration
                if exp.type.isStruct():
                    sname = exp.type.name
                    if sname not in needed:
                        print("TypeError: struct type not found.")
                        exp.type.token().mark()
                        quit()
                    needed[sname][name] = 1
                    needed_cnt[name] += 1
                if exp.type.isFunction():
                    print("TypeError: struct member cannot be function type. Did you want a function pointer?")
                    exp.token().mark()
                    quit()

        # resolve those without dependencies
        process_q = deque([name for name,cnt in needed_cnt.items() if cnt==0])

        while process_q:
            name = process_q.pop()
            
            # can resolve struct name:
            struct = structs[name]
            offset = 0
            alignment = 0 # size of smallest component
            for exp in struct.body:
                # exp is ASTObjectExpressionDeclaration
                # check if type is valid
                exp.type.checkValid(self)
                if exp.type.isVoid():
                    print("TypeError: struct field cannot have type void.")
                    exp.token().mark()
                    quit()
                
                # calculate alignment
                size = self.type_size(exp.type)
                alig = self.type_alignment(exp.type)
                alignment = max(alignment, alig)
                offset = alig * math.ceil(offset / alig)
                self.structmemberoffset[name][exp.name] = offset
                offset += size
            offset = alignment * math.ceil(offset / alignment)
            self.sizeforname[name] = offset
            self.alignmentforname[name] = alignment

            for sname in needed[name]:
                needed_cnt[sname] -= 1
                if needed_cnt[sname] <= 0:
                    process_q.append(sname)

        # check if any have remained: circularity!
        remainder = [name for name,cnt in needed_cnt.items() if cnt!=0]
        if len(remainder)>0:
            name = remainder[0]
            ast = self.typeforname[name]
            print("TypeError: type has cyclic dependencies.")
            ast.token().mark()
            quit()

class CodeCTXFunction:
    """
    Code context inside function

    stack style:
    -open/close variable (space on stack with a name)
    """
    def __init__(self,name,fid,codectx,indent = " "*3):
        self.name = name
        self.codectx = codectx
        self.fid = fid # number id for function, local to file, unique in file

        # stack management:
        self.bp_diff = 0 # sp vs bp
        # we assume it is always 8-aligned (only use pushq/popq)

        self.nametooffset = {} # var name -> diff to bp
        self.nametosize = {}   # var name -> size in bytes
        self.nametotype = {}   # var name -> variable type
        self.nametomutable = {}# var name -> mutable?
        self.namestack = deque() # deque to verify var alloc/dealloc
        
        # scopes: stack of list of local variables
        self.scopes = deque()
        self.scopes.append([]) # outermost scope

        # code dump
        self.code = [] # lines of asm code
        self.indent = indent
    
    def check_name(self,name):
        if name in self.nametooffset:
            print("CodeError: variable collision '{name}'")
            assert(False)

    def alloc_var_from_reg(self, vname, reg, vtype, vmutable):
        """Allocates variable location on stack, put value from reg in it."""
        self.check_name(vname)
        self.bp_diff += 8
        self.nametooffset[vname] = self.bp_diff
        self.nametosize[vname] = 8
        self.nametotype[vname] = vtype
        self.nametomutable[vname] = vmutable
        self.namestack.append(vname)
        
        # add var name to scope
        self.scopes[-1].append(vname)

        if reg.startswith("xmm"):
            self.code.append(f"{self.indent}addq $-8,%rsp # var {vname} alloc")

            self.code.append(f"{self.indent}movsd %{reg}, -{self.bp_diff}(%rbp)# var {vname}=%{reg}")
        else:
            self.code.append(f"{self.indent}pushq %{reg} # var {vname}=%{reg}")

    def alloc_var_with_type(self,vname, vtype, vmutable):
        """Allocate variable on stack with size bytes"""
        size = (vtype.sizeof()+7)//8 * 8
        self.check_name(vname)
        self.bp_diff += size
        self.nametooffset[vname] = self.bp_diff
        self.nametosize[vname] = size
        self.nametotype[vname] = vtype
        self.nametomutable[vname] = vmutable
        self.namestack.append(vname)
        
        # add var name to scope
        self.scopes[-1].append(vname)
        
        self.code.append(f"{self.indent}addq $-{size},%rsp # var {vname} alloc")

    def dealloc_var(self,vname):
        assert(self.namestack.pop() == vname)
        self.bp_diff-=self.nametosize[vname]
        del self.nametooffset[vname]
        size = self.nametosize[vname]
        del self.nametosize[vname]
        del self.nametotype[vname]
        del self.nametomutable[vname]
        self.code.append(f"{self.indent}addq ${size},%rsp # ~var {vname}")
    def var_to_reg(self,vname,reg):
        """write variable value to reg"""
        assert(vname in self.nametooffset)
        offset = self.nametooffset[vname]
        self.code.append(f"{self.indent}movq -{offset}(%rbp),%{reg} # %{reg}={vname}")

    def reg_to_var(self,vname,reg):
        """write reg to variable location"""
        assert(vname in self.nametooffset)
        offset = self.nametooffset[vname]
        self.code.append(f"{self.indent}movq %{reg}, -{offset}(%rbp) # {vname}=%{reg}")
    
    def var_access_str(self,vname):
        """get access string for variable: offset(%rbp)"""
        assert(vname in self.nametooffset)
        offset = self.nametooffset[vname]
        return f"-{offset}(%rbp)"

    def put_code_line(self,line):
        """You can put any code here, but please:
        Do not change rbp,rsp.
        And make sure to stick to cdecl convention
        """
        self.code.append(f"{self.indent}{line}")
    
    def open_scope(self):
        self.put_code_line(f"# new scope")
        self.scopes.append([])

    def close_scope(self):
        self.put_code_line(f"# end scope")
        if len(self.scopes)<2:
            print(self.scopes)
            assert(False and "less than two scopes are left, cannot close one now")
        # deallocate last scope of variables
        for vname in reversed(self.scopes[-1]):
            self.dealloc_var(vname)
        self.scopes.pop()

    def check_close(self):
        # release last scope
        if len(self.scopes)!=1:
            print(self.scopes)
            assert(False and "self.scopes does not have exactly one scope left for function to close")
        
        # deallocate last scope of variables
        for vname in reversed(self.scopes[0]):
            self.dealloc_var(vname)
        
        assert(self.bp_diff == 0)
        assert(len(self.nametooffset)==0)
        assert(len(self.namestack)==0)

ASM_size_to_type = {
        1:"byte",
        2:"short",
        4:"long",
        8:"quad",
        }
ASM_type_to_letter = {
        "byte":"b",
        "short":"w",
        "long":"l",
        "quad":"q",
        }
ASM_type_to_rax = {
        "byte":"al",
        "short":"ax",
        "long":"eax",
        "quad":"rax",
        }
ASM_type_to_rcx = {
        "byte":"cl",
        "short":"cx",
        "long":"ecx",
        "quad":"rcx",
        }

class CodeCTX:
    """
    Code into which code is emitted.
    Afterwards can be called with write() to get asm to file
    """

    def __init__(self,filename,typectx):
        """Set up facilities"""
        self.filename = filename
        self.typectx = typectx
        self.data_items = []
        self.names = {} # just to prevent duplicates
        self.functions = {}
        self.function_cur = None
        self.tagid = 0
        self.globals = {}
        self.tempid = 0
    
    def check_name(self,name):
        if name in self.names:
            print(f"CodeError: duplicate asm name '{name}'")
            quit()
        self.names[name] = 1
    def del_name(self,name):
        if not name in self.names:
            print(f"CodeError: del name did not exist '{name}'")
            assert(False)
        del self.names[name]

    def function_open(self,fname):
        self.check_name(fname)
        assert(self.function_cur is None)
        fid = len(self.functions)
        self.function_cur = CodeCTXFunction(fname,fid,self)
    def function_close(self):
        assert(not self.function_cur is None)
        self.function_cur.check_close()
        self.functions[self.function_cur.name] = self.function_cur
        self.function_cur = None
    
    def function_alloc_var_with_type(self,vname,vtype,vmutable):
        assert(not self.function_cur is None)
        self.function_cur.alloc_var_with_type(vname,vtype,vmutable)
    def function_alloc_var_from_reg(self,vname,reg,vtype,vmutable):
        assert(not self.function_cur is None)
        self.function_cur.alloc_var_from_reg(vname,reg,vtype,vmutable)
    def function_var_to_reg(self,vname,reg):
        assert(not self.function_cur is None)
        self.function_cur.var_to_reg(vname,reg)
    def function_reg_to_var(self,vname,reg):
        assert(not self.function_cur is None)
        self.function_cur.reg_to_var(vname,reg)
    def function_put_code(self,line):
        assert(not self.function_cur is None)
        self.function_cur.put_code_line(line)

    def function_var_access_str(self,vname):
        """get variable access string"""
        assert(not self.function_cur is None)
        return self.function_cur.var_access_str(vname)
    
    def function_open_scope(self):
        assert(not self.function_cur is None)
        self.function_cur.open_scope()
    def function_close_scope(self):
        assert(not self.function_cur is None)
        self.function_cur.close_scope()

    def function_get_name(self,name):
        """Get info about the name
        return None if name not found.
        if can find:
        - global: return 0, gType, isMutable
        - local:  return 1, lType, isMutable
        """
        
        # check if local:
        assert(not self.function_cur is None)
        if name in self.function_cur.nametooffset:
            f = self.function_cur
            return 1,f.nametotype[name],f.nametomutable[name]
        elif name in self.globals:
            gType,isMutable = self.globals[name]
            return 0,gType,isMutable

        return None
    
    def add_global(self,name,gType,isMutable):
        """global variable"""
        self.check_name(name)
        self.globals[name] = gType,isMutable

    def add_data_item(self,name,dtype,value,isGlobal):
        self.check_name(name)
        self.data_items.append((name,dtype,value,isGlobal))
    
    def new_tag(self):
        tagid = self.tagid
        self.tagid += 1
        return f".LC{tagid}"
 
    def new_temp(self):
        tempid = self.tempid
        self.tempid += 1
        return f".tmp{tempid}"


    def write(self,infile,outfile,indent=" "*3):
        """Write code to outfile"""
        filename = os.path.basename(infile)
        with open(outfile,"w") as f:
            # Header
            f.write(f'{indent}.file "{filename}"\n')
            
            # data section
            for gname,gtype,gval,gglob in self.data_items:
                info = "global" if gglob else "local"
                f.write(f'# # data: {gname} {gtype} "{gval}" {info}\n')
                if gtype == "byte":
                    if gglob: # if global
                        f.write(f'{indent}.globl {gname}\n')
                    f.write(f'{indent}.data\n')
                    f.write(f'{indent}.type {gname}, @object\n')
                    f.write(f'{indent}.size {gname}, 1\n')
                    f.write(f'{gname}:\n')
                    f.write(f'{indent}.byte {gval}\n')
                elif gtype == "short":
                    if gglob: # if global
                        f.write(f'{indent}.globl {gname}\n')
                    f.write(f'{indent}.data\n')
                    f.write(f'{indent}.align 2\n')
                    f.write(f'{indent}.type {gname}, @object\n')
                    f.write(f'{indent}.size {gname}, 2\n')
                    f.write(f'{gname}:\n')
                    f.write(f'{indent}.value {gval}\n')
                elif gtype == "long":
                    if gglob: # if global
                        f.write(f'{indent}.globl {gname}\n')
                    f.write(f'{indent}.data\n')
                    f.write(f'{indent}.align 4\n')
                    f.write(f'{indent}.type {gname}, @object\n')
                    f.write(f'{indent}.size {gname}, 4\n')
                    f.write(f'{gname}:\n')
                    f.write(f'{indent}.long {gval}\n')
                elif gtype == "quad":
                    if gglob: # if global
                        f.write(f'{indent}.globl {gname}\n')
                    f.write(f'{indent}.data\n')
                    f.write(f'{indent}.align 8\n')
                    f.write(f'{indent}.type {gname}, @object\n')
                    f.write(f'{indent}.size {gname}, 8\n')
                    f.write(f'{gname}:\n')
                    f.write(f'{indent}.quad {gval}\n')
                elif gtype == "pointer": # same as quad?
                    if gglob: # if global
                        f.write(f'{indent}.globl {gname}\n')
                    f.write(f'{indent}.data\n') # modify?
                    f.write(f'{indent}.align 8\n')
                    f.write(f'{indent}.type {gname}, @object\n')
                    f.write(f'{indent}.size {gname}, 8\n')
                    f.write(f'{gname}:\n')
                    f.write(f'{indent}.quad {gval}\n')
                elif gtype == "string":
                    if gglob: # if global
                        f.write(f'{indent}.globl {gname}\n')
                    f.write(f'{indent}.section .rodata\n')
                    f.write(f'{gname}:\n')
                    f.write(f'{indent}.string "{gval}"\n')
                else:
                    print(f"CodeError: do not know data type '{gtype}'")
                    quit()
                
            
            # text section
            for fname,func in self.functions.items():
                f.write(f'\n')
                f.write(f'########## Function: {fname}\n')
                f.write(f'{indent}.text\n')
                f.write(f'{indent}.globl {fname}\n')
                f.write(f'{indent}.type  {fname}, @function\n')
                f.write(f'{fname}:\n')
                f.write(f'LFB{func.fid}:\n')
                f.write(f'{indent}.cfi_startproc\n')
                f.write(f'{indent}pushq %rbp\n')
                
                # set bp to new base:
                f.write(f'{indent}movq  %rsp, %rbp\n')
                f.write(f'{indent}# # body begin\n') # body begin
                
                for c in func.code: # dump lines
                    f.write(c)
                    f.write("\n")

                f.write(f'{indent}# # body end\n') # body end
                f.write(f'{indent}popq  %rbp\n')
                f.write(f'{indent}ret\n')
                f.write(f'{indent}.cfi_endproc\n')
                f.write(f'LFE{func.fid}:\n')
                f.write(f'{indent}.size  {fname}, .-{fname}\n')
 

            # Footer
            f.write(f'{indent}.ident "peterem-comp: 0.001"\n')
            f.write(f'{indent}.section{indent}.note.GNU-stack,"",@progbits\n')


# ################################################
# # Helper Functions for data extraction from pt #
# ################################################

def ptparse_strip(pt):
    """strip shell if meaningless:
    (False,([],[[pt]])) -> pt
    """
    isToken,payload = pt
    if not isToken:
        tokens,listoflists = payload
        if len(tokens)==0 and len(listoflists)==1 and len(listoflists[0])==1:
            return listoflists[0][0]
    return pt

def ptparse_unpack_brackets(pt,bracket):
    """unpack a layer of brackets
    expect: (False, ([bracket,bracket],[[lst]]))
    if match: return (False,([],[[lst]]))
    else None
    """
    isToken,payload = pt
    if isToken:
        return None
    
    tokens,listoflists = payload
    if len(tokens) !=2 or len(listoflists)!=1:
        return None
    
    if tokens[0].name != "bracket" or tokens[0].value != bracket:
        return None

    # success
    return (False, ([], listoflists))

def ptparse_delimiter_list(pt,delimiters):
    """check if is a delimiter list
    if yes: return (tokens, listoflists)
    else (list with one list): return ([],[lst])

    delimiters: list of (name,value)
    to match tokens.
    if value is None: matches all values
    """
    ddict = {d:1 for d in delimiters}
    
    isToken,payload = pt
    if isToken:
        return ([],[[pt]])
    else:
        tokens,listoflists = payload
        if len(tokens) == 0:
            if len(listoflists)==1:
                return ([],listoflists)
            else:
                print("internal error: listoflists not length 1")
                print(pt)
                print(tokens)
                print(listoflists)
                assert(False)
        else:
            for t in tokens:
                if (not (t.name,t.value) in ddict) and (not (t.name,None) in ddict):
                    # bad token
                    return ([],[[pt]])
            # all tokens were ok
            return (tokens,listoflists)

def ptparse_isdelimiterlist(pt,delimiters):
    """check if is delimiter list where delimiter occurs
    return True/False
    """
    ddict = {d:1 for d in delimiters}
    
    isToken,payload = pt
    if isToken:
        return False
    else:
        tokens,listoflists = payload
        if len(tokens) == 0:
            return False
        else:
            for t in tokens:
                if (not (t.name,t.value) in ddict) and (not (t.name,None) in ddict):
                    # bad token
                    return False
            # all tokens were ok
            return True


def ptparse_isNothing(pt):
    """Check if pt is (False, ([],[[]]))"""
    isToken,payload = pt
    if isToken:
        return False
    tokens,listoflists = payload
    if len(tokens) != 0 or len(listoflists) != 1 or len(listoflists[0])!=0:
        return False
    return True

def ptparse_isToken(pt, token_list=None):
    """check if is a token
    if token_list is not None: also check if matches
    a (name, val) pair. If val is None -> match
    """
    isToken,payload = pt
    if not isToken:
        return False
    else:
        if token_list is None:
            return True
        tdict = {d:1 for d in token_list}
        tk = payload
        if (tk.name,tk.value) in tdict or (tk.name,None) in tdict:
            return True
        else:
            return False

def ptparse_tokenmin(t1,t2):
    """returns the first of the two tokens"""
    if t1 is None:
        return t2
    if t2 is None:
        return t1
    if t1.line < t2.line or (t1.line==t2.line and t1.start <= t2.start):
        return t1
    else:
        return t2

def ptparse_getfirsttoken(pt):
    """given pt, extract first token (recursively)"""
    isToken,payload = pt
    if isToken:
        return payload
    else:
        tokens,listoflists = payload
        cur = None
        for t in tokens:
            cur = ptparse_tokenmin(cur,t)
        for l in listoflists:
            for pt2 in l:
                cur = ptparse_tokenmin(cur, ptparse_getfirsttoken(pt2))
        return cur

def ptparse_markfirsttokeninlist(l):
    """takes list of pt's, search recursively for first token"""
    cur = None
    for pt in l:
        cur = ptparse_tokenmin(cur, ptparse_getfirsttoken(pt))
    cur.mark()


def ptparse_getlist(pt,k):
    """if pt = (False,[],[[k-elements]])
    return list of k-elements
    else: return None
    """
    isToken,payload = pt
    if isToken:
        return None
    else:
        tokens,listoflists = payload
        if len(tokens)==0 and len(listoflists)==1 and len(listoflists[0])==k:
            return listoflists[0]
        else:
            return None

def ptparse_expression(pt):
    """General parsing function to detect expressions
    """
    # types:
    # - name, number, string
    # - (): unpack - recurse
    # - assign
    # - operators
    # - funcptr (args): function call (take first, apply rest)
    # - cast (type,expr): fake function
    
    isToken,payload = pt

    if isToken:
        tk = payload
        if tk.name == "name":
            return ASTObjectExpressionName(pt)
        elif tk.name == "str":
            return ASTObjectExpressionString(pt)
        elif tk.name == "num":
            return ASTObjectExpressionNumber(pt)
        else:
            print("PTParseError: unexpected token (expected: name, string or number)")
            tk.mark()
            quit()
            
    else:
        tokens, listoflists = payload
        if len(tokens) == 0:
            assert(len(listoflists)==1)
            ll = listoflists[0]
            if len(ll) == 0:
                # TODO: some sort of panick mode?
                assert(False and "nothing")
            elif len(ll) == 1:
                # must unpack
                ptsub = ll[0]
                return ptparse_expression(ptsub)
            elif ptparse_isToken(ll[0], [("keyword","var"),("keyword","const")]):
                # var/const definition
                return ASTObjectExpressionDeclaration(pt)
            elif ptparse_isToken(ll[0], [("keyword","return")]):
                # return statement
                return ASTObjectExpressionReturn(pt)
            else:
                # list of elements: function calls
                if len(ll)>2:
                    pt_rtl = ptparse_list_rtl(pt)
                    return ptparse_expression(pt_rtl)
                assert(len(ll)==2)
                
                if ptparse_isToken(ll[0],[("keyword","cast")]):
                    assert(False and "cast not implemented")
                return ASTObjectExpressionFunctionCall(pt)
        else:
            # inspect first token:
            tk = tokens[0]
            if tk.name == "operator":
                return ptparse_expression_operator(pt)
            elif tk.name == "bracket":
                if tk.value == "(":
                    # unpack brackets
                    unpack = ptparse_unpack_brackets(pt,"(")
                    strip = ptparse_strip(unpack)
                    if ptparse_isNothing(strip):
                        print("PTParseError: expected expression inside brackets.")
                        tokens[0].mark()
                        quit()
                    return ptparse_expression(strip)
                elif tk.value == "{":
                    return ASTObjectExpressionScope(pt)
                else:
                    print("PTParseError: unexpected bracket in expression.")
                    tokens[0].mark()
                    quit()
            else:
                print(tokens)
                assert(False and "unhandled token")

def ptparse_expression_operator(pt):
    """Parse operator expression."""
    isToken, payload = pt
    assert(not isToken)
    tokens,listoflists = payload
    assert(len(tokens)>0)
    assert(tokens[0].name == "operator")

    # inspect first token to see what operator we have here
    tk = tokens[0]

    if tk.value in ["=","+=","-=","/=","*="]:
        if len(tokens) > 1: # if multiple assignments: break ltr
            pt_ltr = ptparse_delimiterlist_ltr(pt)
            return ptparse_expression_operator(pt_ltr)
        
        assert(len(listoflists)==2)
        return ASTObjectExpressionAssignment(pt)
    elif tk.value in ASTObjectExpressionBinOp_rtl_operators:
        if len(tokens) > 1: # if multiple assignments: break rtl
            pt_rtl = ptparse_delimiterlist_rtl(pt)
            return ptparse_expression_operator(pt_rtl)
        
        assert(len(listoflists)==2)
        if(len(listoflists[0])==0 and len(listoflists[1])==0):
            # pure operator
            print("SyntaxError: cannot have operator without operands.")
            tk.mark()
            quit()
        elif(len(listoflists[0])==0):
            # unary with right operand
            if tk.value in ASTObjectExpressionBinOp_rtl_operators_also_right_unary:
                return ASTObjectExpressionUnaryOp(pt)
            else:
                print("SyntaxError: this operator is not a unary operator with a right operand.")
                tk.mark()
                quit()

        elif(len(listoflists[1])==0):
            # unary with left operand
            print("SyntaxError: cannot have operator with only right operand.")
            tk.mark()
            quit()
        else:
            # binary operator
            return ASTObjectExpressionBinOp(pt)
    else:
        print(tokens)
        assert(False and "token not handled")

def ptparse_delimiterlist_ltr(pt):
    """Take any delimiter list, left to right
    x + v
      x + v
        x + ..."""
    isToken, payload = pt
    assert(not isToken)
    tokens,listoflists = payload
    assert(len(tokens) + 1 == len(listoflists))

    # extract rightmost elements
    rhs = (False,([tokens[-1]], listoflists[-2:]))
    
    # reduce over rest of elements
    i = len(tokens)-2
    while i>=0:
        rhs = (False, ([tokens[i]], [listoflists[i], [rhs]]))
        i-=1

    return rhs

def ptparse_delimiterlist_rtl(pt):
    """Take any delimiter list, right to left
          v + x
        v + x
    ... + x"""
    isToken, payload = pt
    assert(not isToken)
    tokens,listoflists = payload
    assert(len(tokens) + 1 == len(listoflists))

    # extract leftmostmost elements
    lhs = (False,([tokens[0]], listoflists[0:2]))
    
    # reduce over rest of elements
    i = 1
    while i<len(tokens):
        lhs = (False, ([tokens[i]], [[lhs],listoflists[i+1]]))
        i+=1
    return lhs

def ptparse_list_rtl(pt):
    """Take any list, right to left
        v x
       v x
    ... x"""
    isToken, payload = pt
    assert(not isToken)
    tokens,listoflists = payload
    assert(len(tokens) ==0)
    assert(len(listoflists)==1)
    ll = listoflists[0]

    # extract leftmostmost elements
    lhs = (False,([], [[ll[0], ll[1]]]))
    
    # reduce over rest of elements
    i = 2
    while i<len(ll):
        lhs = (False, ([], [[lhs,ll[i]]]))
        i+=1

    return lhs

def ptparse_type(pt):
    """
    forms:
    - name: value type
    - *name: pointer type
    - out_t(in_t,in_t): function type

    need to check things like:
    - assignment
    - casting
    - operators
    """
    
    isToken,payload = pt

    if isToken:
        tk = payload
        if tk.name == "name" or tk.name == "type":
            if tk.value in ASTObjectTypeNumber_types:
                return ASTObjectTypeNumber(pt)
            elif tk.name == "type" and tk.value == "void":
                return ASTObjectTypeVoid(pt)
            else:
                return ASTObjectTypeStruct(pt)
        else:
            print("PTParseError: syntax error: expected type name.")
            tk.mark()
            quit()
    else:
        tokens,listoflists = payload
        if len(tokens) == 0:
            assert(len(listoflists)==1)
            ll = listoflists[0]
            if len(ll) == 1:
                strip = ll[0]
                return ptparse_type(strip)
            elif len(ll)==2:
                # function type
                return ASTObjectTypeFunction(pt) 
            else:
                print("PTParseError: syntax error: around type description.")
                ptparse_markfirsttokeninlist(ll)
                quit()
        else:
            tk = tokens[0]
            if tk.name == "bracket" and tk.value == "(":
                assert(len(tokens)==2)
                assert(len(listoflists)==1)
                # unpack bracket and strip
                unpack = ptparse_unpack_brackets(pt,"(")
                strip = ptparse_strip(unpack)
                return ptparse_type(strip)
            elif tk.name == "operator":
                if tk.value == "*":
                    if len(tokens) > 1:
                        pt_ltr = ptparse_delimiterlist_ltr(pt)
                        return ptparse_type(pt_ltr)
                    return ASTObjectTypePointer(pt)
                else:
                    print("PTParseError: unexpected operator token in type.")
                    tk.mark()
                    quit()

            else:
                print("PTParseError: unexpected token in type.")
                tk.mark()
                quit()

    assert(False and "panick")

# ##########################
# # ASTObjects for parsing #
# ##########################

class ASTObjectType(ASTObject):
    """
    generic Type ast object
    """
    def __init__(self,pt):
        assert(False)

    # attributes to be defined by all:
    def isPointer(self):
        return False
    def isNumber(self):
        return False
    def isStruct(self):
        return False
    def isFunction(self):
        return False
    def isVoid(self):
        return False
    def isNull(self):
        return False

    def checkValid(self, typectx):
        """Check if a type is valid"""
        assert(False and "not implemented")
    
    def equals(self,other):
        print(self)
        print(other)
        assert(False and "not implemented")

    def toStr(self):
        print(self)
        assert(False and "not implemented")
    
    def sizeof(self):
        print(self)
        assert(False and "not implemented")

    def softCastImmediate(self,otype,oval):
        if otype.equals(self): # only allow if same type
            return oval
        else:
            return None

class ASTObjectTypeVoid(ASTObjectType):
    """
    void type ast object
    """
    def __init__(self,pt,token=None):
        if pt is None:
            # if pt is None, token cannot be None
            assert(not token is None)
        else:
            assert(ptparse_isToken(pt,[("type","void")]))
    
    def isVoid(self):
        return True

    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[void-type]")
     
    def checkValid(self, typectx):
        pass

    def equals(self,other):
        return type(self)==type(other)
    def toStr(self):
        return "void"
    def sizeof(self):
        return 0

class ASTObjectTypePointer(ASTObjectType):
    """
    pointer type ast object
    """
    def __init__(self,pt):
        isToken,payload = pt
        assert(not isToken)
        tokens,listoflists = payload
        assert(len(tokens)==1)
        # expect pointer type:
        # * sth
        if len(tokens)>1:
            print("PTParseError: too many operator tokens for pointer type.")
            tokens[0].mark()
            quit()
        assert(len(listoflists)==2)
        lhs = listoflists[0]
        rhs = listoflists[1]
        if len(lhs)>0:
            print("PTParseError: syntax error: nothing allowed left of pointer type '*'.")
            tokens[0].mark()
            quit()

        # now go recursive
        self.type = ptparse_type((False, ([],[rhs])))
    
    def isPointer(self):
        return True

    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[pointer-type]")
        self.type.print_ast(depth = depth+step)
     
    def checkValid(self, typectx):
        self.type.checkValid(typectx)

    def equals(self,other):
        if not type(self)==type(other):
            return False
        return self.type.equals(other.type)

    def toStr(self):
        return f"*{self.type.toStr}"
    def sizeof(self):
        return 8

ASTObjectTypeNumber_types = {
        "i64":8,
        "i32":4,
        "i16":2,
        "i8":1,
        "float":4,
        "double":8,
        "u64":8,
        "u32":4,
        "u16":2,
        "u8":1,
        }# numbers are size in bytes

ASTObjectTypeNumber_types_rank = {
        "i64":6400,
        "i32":3200,
        "i16":1600,
        "i8":800,
        "float":9900,
        "double":9901,
        "u64":6401,
        "u32":3201,
        "u16":1601,
        "u8":801,
        }# numbers are size in bytes

def number_type_max(a,b):
    """looks at types_rank above, returns the one with max rank
    input: type objects (not strings!)"""
    ra = ASTObjectTypeNumber_types_rank[a.name]
    rb = ASTObjectTypeNumber_types_rank[b.name]
    return a if ra>=rb else b

ASTObjectTypeNumber_types_float = ["double","float"]

ASTObjectTypeNumber_types_to_signed = {
        "i64":"i64",
        "i32":"i32",
        "i16":"i16",
        "i8":"i8",
        "float":"float",
        "double":"double",
        "u64":"i64",
        "u32":"i32",
        "u16":"i16",
        "u8":"i8",
        }# numbers are size in bytes

def number_type_signed(typeName):
    """return boolean, True if signed"""
    sngd = ASTObjectTypeNumber_types_to_signed[typeName]
    return sngd == typeName

def number_type_to_letter(typeName):
    """returns letter used for move/etc"""
    size = ASTObjectTypeNumber_types[typeName]
    asmType = ASM_size_to_type[size]
    letter = ASM_type_to_letter[asmType]
    return letter

def number_to_integer_view(typeName,value):
    """from typeName (eg float, i32, ...) to quad ..."""
    size = ASTObjectTypeNumber_types[typeName]
    asmType = ASM_size_to_type[size]
    
    # floating point number handling:
    if typeName == "float":
        value = value.view(np.uint32)
    if typeName == "double":
        value = value.view(np.uint64)
    
    return asmType, value



class ASTObjectTypeNumber(ASTObjectType):
    """
    number type ast object, see list in dictionary above:
    """
    def __init__(self,pt, name=None):
        """use name if want to generate from name"""
        if name is None:
            isToken,payload = pt
            assert(isToken)
            tk = payload
            assert(tk.name == "name" or tk.name == "type")
            assert(tk.value in ASTObjectTypeNumber_types)
            self.name = tk.value
        else:
            self.name = name

    def isNumber(self):
        return True

    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[number-type] {self.name}")
    
    def checkValid(self, typectx):
        assert(self.name in typectx.typeforname)
        assert(typectx.typeforname[self.name].isNumber())
    
    def equals(self,other):
        if not type(self)==type(other):
            return False
        return self.name == other.name
 
    def toStr(self):
        return self.name
    def sizeof(self):
        return ASTObjectTypeNumber_types[self.name]

    def softCastImmediate(self,otype,oval):
        if otype.equals(self): # only allow if same type
            return oval
        if otype.isNumber():
            isFloat = otype.name in ASTObjectTypeNumber_types_float
            toInteger = self.name not in ASTObjectTypeNumber_types_float

            if isFloat and toInteger:
                print(f"Warning: cannot softCastImmediate {otype.name} value {oval} to integer type {self.name}.")
                return None
                
            if self.name == "u8":
                return np.uint8(oval)
            elif self.name == "u16":
                return np.uint16(oval)
            elif self.name == "u32":
                return np.uint32(oval)
            elif self.name == "u64":
                return np.uint64(oval)
            elif self.name == "i8":
                return np.int8(oval)
            elif self.name == "i16":
                return np.int16(oval)
            elif self.name == "i32":
                return np.int32(oval)
            elif self.name == "i64":
                return np.int64(oval)
            elif self.name == "double":
                return np.double(oval)
            elif self.name == "float":
                return np.single(oval)
            else:
                print(f"Warning: cannot softCastImmediate {self.toStr()} to {otype.toStr()}")
                return None
        else:
            return None
    
    def signedCastImmediate(self,oval):
        """just cast to signed
        return ctype,cval
        """
        ctype = ASTObjectTypeNumber_types_to_signed[self.name]
        ctype = ASTObjectTypeNumber(None,ctype)
        cval = self.softCastImmediate(ctype, oval)
        if ctype is None:
            print(f"Warning: cannot signedCastImmediate {self.toStr()}")
        return ctype,cval

    def softCastRegister(self,codectx,oType,regDict,doubleReg):
        """cast register value.
        if type is integer, then use regDict, asmType -> register name.
        if floating: xmm register name in doubeReg
        Return True or False (success?)
        """

        sFloat = self.name in ASTObjectTypeNumber_types_float
        oFloat = oType.name in ASTObjectTypeNumber_types_float
        
        if sFloat and oFloat:
            # float to float
            # cvtss2sd
            ssuffix = "s" if self.name == "float" else "d"
            osuffix = "s" if oType.name == "float" else "d"
            codectx.function_put_code(f"cvts{osuffix}2s{ssuffix} %{doubleReg}, %{doubleReg} # cast: %{doubleReg} from {oType.name} to {self.name}")
            return True
        elif not sFloat and oFloat:
            # float to int
            # cvttss2si
            sng = "s" if number_type_signed(self.name) else "z"
            msize = 8
            masmType = ASM_size_to_type[msize]
            mreg = regDict[masmType]
            ml = ASM_type_to_letter[masmType]
            
            suffix = "s" if oType.name == "float" else "d"
            app = "q" if number_type_signed(self.name) else ""
            codectx.function_put_code(f"cvtts{suffix}2si{app} %{doubleReg}, %{mreg} # cast: %{doubleReg} = %{mreg}")
            return True
        elif sFloat and not oFloat:
            # int to float
            # stretch int register to 64 bits
            sng = "s" if number_type_signed(oType.name) else "z"
            osize = ASTObjectTypeNumber_types[oType.name]
            msize = 8
            oasmType = ASM_size_to_type[osize]
            masmType = ASM_size_to_type[msize]
            oreg = regDict[oasmType]
            mreg = regDict[masmType]
            ol = ASM_type_to_letter[oasmType]
            ml = ASM_type_to_letter[masmType]
            
            if osize<msize:
                codectx.function_put_code(f"mov{sng}{ol}{ml} %{oreg}, %{mreg} # cast %{regDict['quad']} from {oType.toStr()} to 64 bits")
            
            suffix = "s" if self.name == "float" else "d"
            if number_type_signed(oType.name):
                # signed int
                codectx.function_put_code(f"cvtsi2s{suffix} %{mreg}, %{doubleReg} # cast: %{mreg} = %{doubleReg}")
                return True
            else:
                return False # TODO
        else:
            # int to int
            sl = number_type_to_letter(self.name)
            ol = number_type_to_letter(oType.name)
            ssize = ASTObjectTypeNumber_types[self.name]
            osize = ASTObjectTypeNumber_types[oType.name]
            sasmType = ASM_size_to_type[ssize]
            oasmType = ASM_size_to_type[osize]
            sreg = regDict[sasmType]
            oreg = regDict[oasmType]

            sng = "s" if number_type_signed(oType.name) else "z"
            if osize >= ssize:
                # ignore cast
                codectx.function_put_code(f"# nop # cast %{regDict['quad']} from {oType.toStr()} to {self.toStr()}")
                return True
            else:
                codectx.function_put_code(f"mov{sng}{ol}{sl} %{oreg}, %{sreg} # cast %{regDict['quad']} from {oType.toStr()} to {self.toStr()}")
                return True
            
    def immToReg(self,codectx,val,regDict,floatReg):
        """write imm value to register.
        if type is integer, then use regDict, asmType -> register name.
        if floating: xmm register name in floatReg
        Return True or False (success?)
        """
        asmType,asmVal = number_to_integer_view(self.name,val)
        # write imm to register
        if self.name in ASTObjectTypeNumber_types_float:
            suffix = "s" if self.name == "float" else "d"
            # dump value
            tag = codectx.new_tag()
            codectx.add_data_item(tag,asmType,asmVal,False)
            # load to xmm0
            codectx.function_put_code(f"movs{suffix} {tag}(%rip), %xmm0 # %{floatReg} = {val}")
        else:
            letter = ASM_type_to_letter[asmType]
            reg = regDict[asmType]
            codectx.function_put_code(f"mov{letter} ${asmVal}, %{reg} # %{regDict['quad']} = {val}")

        return True


class ASTObjectTypeStruct(ASTObjectType):
    """
    struct type ast object
    """
    def __init__(self,pt,token = None):
        """if from pt: only give pt, if from token set pt=None"""
        if token is None:
            isToken,payload = pt
            assert(isToken)
            tk = payload
            assert(tk.name == "name")
            self.name = tk.value
            self.token_ = tk
        else:
            self.token_ = token
            self.name = token.value
    
    def token(self):
        return self.token_

    def isStruct(self):
        return True

    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[struct-type] {self.name}")
    
    def checkValid(self, typectx):
        if not self.name in typectx.typeforname:
            print("TypeError: struct not declared.")
            self.token().mark()
            quit()
        assert(typectx.typeforname[self.name].isStruct())
 
    def equals(self,other):
        if not type(self)==type(other):
            return False
        return self.name == other.name
    
    def toStr(self):
        return self.name
 
class ASTObjectTypeFunction(ASTObjectType):
    """
    function type ast object
    """
    def __init__(self,pt,_return_type=None,_arg_types=None):
        """If want to set from types, then can"""
        if _return_type is not None:
            assert(_arg_types is not None)
            self.return_type = _return_type
            self.argument_types = _arg_types
        else:
            isToken,payload = pt
            assert(not isToken)
            tokens,listoflists = payload
            assert(len(tokens)==0)
            assert(len(listoflists)==1)
            ll = listoflists[0]
            assert(len(ll)==2)

            # return type:
            self.return_type = ptparse_type(ll[0])

            # argument types:
            unpack = ptparse_unpack_brackets(ll[1],"(")
            if unpack is None:
                print("PTParseError: syntax error: expected brackets for arguments of function type.")
                ptparse_markfirsttokeninlist([ll[1]])
                quit()
            
            unpack = ptparse_strip(unpack)
            tokens,listoflists = ptparse_delimiter_list(unpack,[("comma",",")])
            self.argument_types = []

            # check that none of the lists is empty
            if len(tokens)>0:
                for i,ll in enumerate(listoflists):
                    if len(ll)==0:
                        if i == 0:
                            print("PTParseError: syntax error: expected function argument type before this comma.")
                            tokens[0].makr()
                            quit()
                        else:
                            print("PTParseError: syntax error: expected function argument type after this comma.")
                            tokens[i-1].mark()
                            quit()

            # parse the argument types
            for ll in listoflists:
                if len(ll)>0:
                    arg = ptparse_type((False,([],[ll])))
                    self.argument_types.append(arg)
 

    def isFunction(self):
        return True

    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[function-type]")
        print(" "*depth + f"return type:")
        self.return_type.print_ast(depth = depth+step)
        print(" "*depth + f"arguments:")
        for arg in self.argument_types:
            arg.print_ast(depth = depth+step)
    
    def checkValid(self, typectx):
        self.return_type.checkValid(typectx)
        for arg in self.argument_types:
            arg.checkValid(typectx)

    def equals(self,other):
        if not type(self)==type(other):
            return False
        if not self.return_type.equals(other.return_type):
            return False
        if len(self.argument_types) != len(other.argument_types):
            return False
        for i in range(len(self.argument_types)):
            a1 = self.argument_types[i]
            a2 = other.argument_types[i]
            if not a1.equals(a2):
                return False
        return True

    def toStr(self):
        args = ",".join([a.toStr() for a in self.argument_types])
        return f"({self.return_type.toStr()}(args))"

class ASTObjectFunction(ASTObject):
    """
    Function ast object
    """

    def __init__(self,pt):
        # function type name (bracket-body) {bracket-body}
        l = ptparse_getlist(pt, 5) # get the 5 elements def
        if l is None:
            l = ptparse_getlist(pt, 4) # get the 4 elements decl
        if l is None:
            print("PTParseError: syntax error: expected 'function type name (args) {body:optional}'")
            ptparse_markfirsttokeninlist([pt])
            quit()

        # check that first is function
        if ptparse_isToken(l[0],[("keyword","function")]):
            pass
        else:
            print("PTParseError: syntax error: expected 'function'")
            ptparse_markfirsttokeninlist([l[0]])
            quit()

        # check return type:
        self.return_type = ptparse_type(l[1])

        # check name:
        if ptparse_isToken(l[2],[("name",None)]):
            self.name_token = l[2][1]
            self.name = l[2][1].value
        
        # check args:
        # l[3]
        # expect (comma list):
        unpack = ptparse_unpack_brackets(l[3],"(")
        if unpack is None:
            print("PTParseError: syntax error: expected function argument brackets.")
            ptparse_markfirsttokeninlist([l[3]])
            quit()
        
        unpack = ptparse_strip(unpack)
        tokens,listoflists = ptparse_delimiter_list(unpack,[("comma",",")])
        self.varconst = {}
        self.arguments = []

        # check that none of the lists is empty
        if len(tokens)>0:
            for i,ll in enumerate(listoflists):
                if len(ll)==0:
                    if i == 0:
                        print("PTParseError: syntax error: expected function argument before this comma.")
                        tokens[0].makr()
                        quit()
                    else:
                        print("PTParseError: syntax error: expected function argument after this comma.")
                        tokens[i-1].mark()
                        quit()

        # parse the arguments
        for ll in listoflists:
            if len(ll)>0:
                arg = ASTObjectVarConst((False,([],[ll])))
                if not arg.isMutable:
                    print("PTParseError: function arguments must be var, not const.")
                    arg.token().mark()
                    quit()
                self.add_argument(arg)
        
        if len(l) == 5: # function definition
            # check body:
            # l[4]
            # expect (comma list):
            self.body = ASTObjectExpressionScope(l[4])
        else: # function declaration
            self.body = None
    
    def add_argument(self,arg):
        """arg: ASTObjectVarConst
        """
        self.varconst[arg.name] = arg
        self.arguments.append(arg)

    def token(self):
        return self.name_token

    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[Function] {self.name}")
        print(" "*depth + f"return type:")
        self.return_type.print_ast(depth = depth+step)
        print(" "*depth + f"arguments:")
        for arg in self.arguments:
            arg.print_ast(depth = depth+step)
        if self.body:
            print(" "*depth + f"body:")
            self.body.print_ast(depth = depth+step)
        else:
            print(" "*depth + f"declaration")
 
    def checkSignature(self, typectx):
        """Check type validity of signature"""
        self.return_type.checkValid(typectx)
        for arg in self.arguments:
            arg.type.checkValid(typectx)

    def signature(self):
        """return type of function"""
        return ASTObjectTypeFunction(None,
                self.return_type,
                [a.type for a in self.arguments])
    
    def checkCompatible(self,other):
        """checks if two Function objects are compatible.
        returns: error if not compatible (aborts)
        or the definition if one exists
        or else self 
        """
        if (not self.body is None) and (not other.body is None):
            print("PTParseError: duplicate definition.")
            self.token().mark()
            other.token().mark()
            quit()

        if not self.signature().equals(other.signature()):
            print("TypeError: conflicting function signatures in declarations.")
            self.token().mark()
            other.token().mark()
            quit()

        if other.body:
            return other
        return self


        
class ASTObjectStruct(ASTObject):
    """
    Struct ast object
    """

    def __init__(self,pt):
        # struct name {bracket-body}
        l = ptparse_getlist(pt, 3) # get the 3 elements
        if l is None:
            print("PTParseError: syntax error: expected 'struct name {body}'")
            ptparse_markfirsttokeninlist([pt])
            quit()

        # check that first is function
        if ptparse_isToken(l[0],[("keyword","struct")]):
            pass
        else:
            print("PTParseError: syntax error: expected 'function'")
            ptparse_markfirsttokeninlist([l[0]])
            quit()

        # check name:
        if ptparse_isToken(l[1],[("name",None)]):
            self.name_token = l[1][1]
            self.name = l[1][1].value
        
        # check body:
        unpack = ptparse_unpack_brackets(l[2],"{")
        if unpack is None:
            print("PTParseError: syntax error: expected struct body brackets.")
            ptparse_markfirsttokeninlist([l[2]])
            quit()
        
        unpack = ptparse_strip(unpack)
        tokens,listoflists = ptparse_delimiter_list(unpack,[("semicolon",";")])

        # parse list of body instructions.
        # They are a sequence of declarations.
        self.body = []
        for ll in listoflists:
            if len(ll) > 0:
                exp = ASTObjectExpressionDeclaration((False,([],[ll])))
                self.body.append(exp)

    def token(self):
        return self.name_token
 
    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[Struct] {self.name}")
        print(" "*depth + f"body:")
        for exp in self.body:
            exp.print_ast(depth = depth+step)
 

class ASTObjectExpression(ASTObject):
    """
    Expression ast object
    this is the 
    """

    def __init__(self,pt):
        assert(False)

    # to implement in derived classes:
    def isReadable(self):
        return False
    def isWritable(self):
        return False

    def token(self):
        # return token that points to this expression
        # used for error messages
        assert(False)

    def codegen_expression(self,codectx,needImmediate):
        """
        returns eType,eReg,eVal
        eType: a type object of return value
        eReg: True if in eax/rax, false if in eVal
        eVal: None if in eax/rax, immediate of type eType
        """
        print(f"not implemented {type(self)}")
        assert(False and "not implemented")

    def codegen_assign(self,codectx,needImmediate,aType,aReg,aVal):
        """
        returns eType,eReg,eVal
        write values given, return same values
        """
        print(f"not implemented {type(self)}")
        assert(False and "not implemented")

class ASTObjectExpressionScope(ASTObjectExpression):
    """Code scope {block}"""

    def __init__(self,pt):
        unpack = ptparse_unpack_brackets(pt,"{")
        self.token_ = pt[1][0][0]
        if unpack is None:
            print("PTParseError: syntax error: expected scope brackets.")
            ptparse_markfirsttokeninlist([pt])
            quit()
        
        unpack = ptparse_strip(unpack)
        tokens,listoflists = ptparse_delimiter_list(unpack,[("semicolon",";")])

        # parse list of body instructions.
        # They are a sequence of expressions.
        # For this we apply a general expression detector.
        self.body = []
        for ll in listoflists:
            if len(ll) > 0:
                exp = ptparse_expression((False,([],[ll])))
                self.body.append(exp)

    def isReadable(self):
        return True
    def isWritable(self):
        return False

    def token(self):
        return self.token_

    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[Scope]")
        for exp in self.body:
            exp.print_ast(depth = depth+step)

    def codegen_expression(self,codectx,needImmediate):
        """See super for desc"""
        
        codectx.function_open_scope()
        
        codectx.function_put_code(f"")
        for exp in self.body:
            eType,eReg,eVal = exp.codegen_expression(codectx,needImmediate)
            codectx.function_put_code(f"")
        
        codectx.function_close_scope()

        return ASTObjectTypeVoid(None,token=self.token()),True,None

 
class ASTObjectExpressionAssignment(ASTObjectExpression):
    """Assignment of some kind"""
    def __init__(self,pt):
        isToken, payload = pt
        assert(not isToken)
        tokens,listoflists = payload
        assert(len(tokens)>0)
        assert(tokens[0].name == "operator")
        assert(len(listoflists)==2)
        tk = tokens[0]
        assert( tk.value in ["=","+=","-=","/=","*="] )
        
        lhs = listoflists[0]
        rhs = listoflists[1]

        self.operator = tk.value
        self.token_ = tokens[0]
        self.lhs = ptparse_expression((False,([],[lhs])))
        self.rhs = ptparse_expression((False,([],[rhs])))
        
        if not self.lhs.isWritable():
            print("PTParseError: cannot write to left-hand-side of this assignment.")
            tokens[0].mark()
            quit()

        if tk.value != "=":
            if not self.lhs.isReadable():
                print("PTParseError: cannot read from left-hand-side of this read-modify-write operator.")
                tokens[0].mark()
                quit()

        if not self.rhs.isReadable():
            print("PTParseError: cannot read/get value from right-hand-side of this assignment.")
            tokens[0].mark()
            quit()

    def isReadable(self):
        return True
    def isWritable(self):
        return True

    def token(self):
        return self.token_
 
    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[Assignment] {self.operator}")
        print(" "*depth + f"lhs:")
        self.lhs.print_ast(depth = depth+step)
        print(" "*depth + f"rhs:")
        self.rhs.print_ast(depth = depth+step)

    def codegen_expression(self,codectx,needImmediate):
        """See super for desc"""
        assert(not needImmediate and "could maybe do if really want")
        # get rhs:
        aType,aReg,aVal = self.rhs.codegen_expression(codectx,needImmediate)
        
        # pass content to write code:
        aType,aReg,aVal = self.lhs.codegen_assign(codectx,needImmediate, aType,aReg,aVal)

        return aType,aReg,aVal # forward what was written

class ASTObjectExpressionFunctionCall(ASTObjectExpression):
    """Function Call"""
    def __init__(self,pt):
        isToken, payload = pt
        assert(not isToken)
        tokens,listoflists = payload
        assert(len(tokens)==0)
        assert(len(listoflists)==1)
        ll = listoflists[0]
        assert(len(ll)==2)
        lhs = ll[0]
        rhs = ll[1]
        
        self.token_ = ptparse_getfirsttoken(lhs)

        self.func = ptparse_expression((False,([],[[lhs]])))
        if not self.func.isReadable():
            print("PTParseError: cannot read/evaluate function name/pointer.")
            tokens[0].mark()
            quit()
        
        # arguments
        unpack = ptparse_unpack_brackets(rhs,"(")
        if unpack is None:
            print("PTParseError: syntax error: expected function call argument brackets.")
            ptparse_markfirsttokeninlist([rhs])
            quit()
 
        unpack = ptparse_strip(unpack)
        tokens,listoflists = ptparse_delimiter_list(unpack,[("comma",",")])
        self.arguments = []
        
        # check that none of the arguments is empty
        if len(tokens)>0:
            for i,ll in enumerate(listoflists):
                if len(ll)==0:
                    if i == 0:
                        print("PTParseError: syntax error: expected argument before this comma.")
                        tokens[0].mark()
                        quit()
                    else:
                        print("PTParseError: syntax error: expected argument after this comma.")
                        tokens[i-1].mark()
                        quit()

        # parse the arguments
        for ll in listoflists:
            if len(ll)>0:
                arg = ptparse_expression((False,([],[ll])))
                if not arg.isReadable():
                    print("PTParseError: cannot read/evaluate function argument.")
                    tokens[0].mark()
                    quit()
                self.arguments.append(arg)
 
       
    def isReadable(self):
        return True
    def isWritable(self):
        return True

    def token(self):
        return self.token_
 
    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[Function Call]")
        print(" "*depth + f"func:")
        self.func.print_ast(depth = depth+step)
        print(" "*depth + f"args:")
        for i,arg in enumerate(self.arguments):
            print(" "*depth + f"#{i}:")
            arg.print_ast(depth = depth+step)

ASTObjectExpressionBinOp_rtl_operators = [
        "+","-","*","/","%",
        ]

ASM_bin_ops = {
        "+":"add",
        "-":"sub",
        "*":"mul",
        "/":"div",
        }

ASTObjectExpressionBinOp_rtl_operators_also_right_unary = [
        "-","*",
        ]

class ASTObjectExpressionBinOp(ASTObjectExpression):
    """Binary operator of any kind
    reads both sides and returns some result
    """
    def __init__(self,pt):
        isToken, payload = pt
        assert(not isToken)
        tokens,listoflists = payload
        assert(len(tokens)==1)
        assert(tokens[0].name == "operator")
        assert(len(listoflists)==2)
        tk = tokens[0]
        assert( tk.value in ASTObjectExpressionBinOp_rtl_operators )
        
        lhs = listoflists[0]
        rhs = listoflists[1]

        self.operator = tk.value
        self.token_ = tk
        self.lhs = ptparse_expression((False,([],[lhs])))
        self.rhs = ptparse_expression((False,([],[rhs])))
        
        if not self.lhs.isReadable():
            print("PTParseError: cannot read from left-hand-side of this binary operator.")
            tokens[0].mark()
            quit()

        if not self.rhs.isReadable():
            print("PTParseError: cannot read from right-hand-side of this binary operator.")
            tokens[0].mark()
            quit()

    def isReadable(self):
        return True
    def isWritable(self):
        return True

    def token(self):
        return self.token_
 
    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[BinOp] {self.operator}")
        print(" "*depth + f"lhs:")
        self.lhs.print_ast(depth = depth+step)
        print(" "*depth + f"rhs:")
        self.rhs.print_ast(depth = depth+step)
    
    def codegen_expression(self,codectx,needImmediate):
        """See super for desc"""
        
        # get lhs:
        lType,lReg,lVal = self.lhs.codegen_expression(codectx,needImmediate)
        
        if lReg:
            # send to local variable
            tmp = codectx.new_temp()
            if lType.isNumber() and lType.name in ASTObjectTypeNumber_types_float:
                codectx.function_alloc_var_from_reg(tmp,"xmm0",lType,False)
            else:
                codectx.function_alloc_var_from_reg(tmp,"rax",lType,False)

        rType,rReg,rVal = self.rhs.codegen_expression(codectx,needImmediate)

        if lType.isNumber() and rType.isNumber():
            t = number_type_max(lType,rType)
            
            if (not lReg) and (not rReg):
                # convert if needed:
                if not t.equals(lType):
                    lVal = t.softCastImmediate(lType,lVal)
                    if lVal is None:
                        print(f"TypeError: could not convert {lType.toStr()} to {t.toStr()} for left-hand-side of operator.")
                        self.token().mark()
                        quit()
                if not t.equals(rType):
                    rVal = t.softCastImmediate(rType,rVal)
                    if rVal is None:
                        print(f"TypeError: could not convert {rType.toStr()} to {t.toStr()} for right-hand-side of operator.")
                        self.token().mark()
                        quit()
                
                
                def immCompGo():
                    if self.operator == "+":
                        res = lVal + rVal
                        return t,False,res
                    elif self.operator == "-":
                        res = lVal - rVal
                        return t,False,res
                    elif self.operator == "*":
                        res = lVal * rVal
                        return t,False,res
                    elif self.operator == "/":
                        if rVal == 0:
                            print("Error: cannot divide by zero!")
                            self.token().mark()
                            quit()
                        res = None
                        if t.name in ASTObjectTypeNumber_types_float:
                            res = lVal / rVal
                        else:
                            res = lVal // rVal
                        return t,False,res
                    else:
                        self.token().mark()
                        assert(False and "BinOp imm not implemented")
                np.seterr(all="raise")
                error = ""
                try:
                    return immCompGo()
                except FloatingPointError as e:
                    error = e
                
                np.seterr(all="ignore")
                t,_,res = immCompGo()
                print(f"Warning: unexpected computation in immediate values: {error}")
                print(f"{lVal} {self.operator} {rVal} = {res}")
                self.token().mark()
                np.seterr(all="warn")
                return t,False,res
            
            if not rReg:
                # imm to rax / xmm0
                rType.immToReg(codectx,rVal,ASM_type_to_rax,"xmm0")
                rReg = True

            if rReg:
                # move right arg rax/xmm0 -> rcx/xmm1
                if lType.isNumber() and rType.name in ASTObjectTypeNumber_types_float:
                    suffix = "s" if t.name == "float" else "d"
                    codectx.function_put_code(f"movs{suffix} %xmm0, %xmm1 # %xmm1 = %xmm0")
                else:
                    codectx.function_put_code(f"movq %rax, %rcx # %rcx = %rax")
                
                # move lhs to rax/xmm0
                if lReg:
                    if lType.isNumber() and lType.name in ASTObjectTypeNumber_types_float:
                        codectx.function_var_to_reg(tmp,"xmm0")
                    else:
                        codectx.function_var_to_reg(tmp,"rax")
                    
                else:
                    # imm to rax / xmm0
                    lType.immToReg(codectx,lVal,ASM_type_to_rax,"xmm0")
                    lReg = True

                # convert if needed:
                if not t.equals(lType):
                    success = t.softCastRegister(codectx, lType, ASM_type_to_rax, "xmm0")
                    if not success:
                        print(f"TypeError: could not convert {lType.toStr()} to {t.toStr()} of left-hand-side operand.")
                        self.token().mark()
                        quit()
                if not t.equals(rType):
                    success = t.softCastRegister(codectx, rType, ASM_type_to_rcx, "xmm1")
                    if not success:
                        print(f"TypeError: could not convert {lType.toStr()} to {t.toStr()} of right-hand-side operand.")
                        self.token().mark()
                        quit()
                if not self.operator in ASM_bin_ops:
                    print(f"CodeError: binary operator '{self.operator}' not implemented for floats/doubles.")
                    self.token().mark()
                    assert(False and "not implemented")

                asm_op = ASM_bin_ops[self.operator]
 
                if t.name in ASTObjectTypeNumber_types_float:
                    suffix = "s" if t.name == "float" else "d"
                    
                    codectx.function_put_code(f"{asm_op}s{suffix} %xmm1, %xmm0 # %xmm0 = %xmm0 {self.operator} %xmm1")
                    return t,True,None
                else:
                    # perform rax = rax OP rcx in dtype t
                    size = ASTObjectTypeNumber_types[t.name]
                    asmType = ASM_size_to_type[size]
                    letter = ASM_type_to_letter[asmType]
                    rax = ASM_type_to_rax[asmType]
                    rcx = ASM_type_to_rcx[asmType]
                    

                    if self.operator in ["*","/"]:
                        # single argument exceptions
                        if number_type_signed(t.name):
                            codectx.function_put_code(f"i{asm_op}{letter} %{rcx} # %rax = %rax {self.operator} %rcx")
                            return t,True,None
                        else:
                            codectx.function_put_code(f"{asm_op}{letter} %{rcx} # %rax = %rax {self.operator} %rcx")
                            return t,True,None
                    else:
                        codectx.function_put_code(f"{asm_op}{letter} %{rcx}, %{rax} # %{rax} = %{rax} {self.operator} %{rcx}")
                        return t,True,None
            else:
                assert(False and "lReg, rImm - is handled!")
        else:
            print(f"error: not both sides numbers {lType.toStr()} and {rType.toStr()}")
            self.token().mark()
            quit()

        print(lType,lReg,lVal)
        print(rType,rReg,rVal)
        assert(False and "should never arrive here!")

class ASTObjectExpressionUnaryOp(ASTObjectExpression):
    """unary operator of any kind
    reads left or right side
    """
    def __init__(self,pt):
        isToken, payload = pt
        assert(not isToken)
        tokens,listoflists = payload
        assert(len(tokens)==1)
        assert(tokens[0].name == "operator")
        assert(len(listoflists)==2)
        tk = tokens[0]
        assert( tk.value in ASTObjectExpressionBinOp_rtl_operators )
        
        if len(listoflists[0])==0:
            assert(tk.value in ASTObjectExpressionBinOp_rtl_operators_also_right_unary)
            assert(len(listoflists[1])>0)
            self.isRight = True
            self.arg = listoflists[1]
        else:
            assert(False)

        self.operator = tk.value
        self.token_ = tk
        self.arg = ptparse_expression((False,([],[self.arg])))
        
        if not self.arg.isReadable():
            print("PTParseError: cannot read from operand of this unary operator.")
            tokens[0].mark()
            quit()

    def isReadable(self):
        return True
    def isWritable(self):
        return True

    def token(self):
        return self.token_
 
    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[UnaryOp] {self.operator}")
        print(" "*depth + f"arg (right: {self.isRight}):")
        self.arg.print_ast(depth = depth+step)
    
    def codegen_expression(self,codectx,needImmediate):
        """See super for desc"""
        aType,aReg,aVal = self.arg.codegen_expression(codectx,needImmediate)
        if aReg and needImmediate:
            print("SyntaxError: need immediate value, which was not obtainable.")
            self.token().mark()
            quit()

        if aReg:
            assert(False and "not implemented")
        else:
            # immediate value:
            if aType.isNumber():
                if self.operator == "-" and self.isRight:
                    ctype,cval = aType.signedCastImmediate(aVal)
                    if ctype is None:
                        print(f"TypeError: could not cast '{aType.toStr()}' to a signed type.")
                        self.token().mark()
                        quit()
                    else:
                        return ctype,False,-cval # apply minus
                else:
                    print(f"TypeError: did not know how to apply unary operator to type '{aType.toStr()}' (right: {self.isRight})")
                    self.token().mark()
                    quit()

            else:
                print(f"TypeError: did not know how to apply unary operator to type '{aType.toStr()}'")
                self.token().mark()
                quit()


class ASTObjectExpressionDeclaration(ASTObjectExpression):
    """var/const declaration
    const type name
    var type name
    """
    def __init__(self,pt):
        # parse var / const definition
        l = ptparse_getlist(pt, 3)
        if l is None:
            print("PTParseError: syntax error: expected 'const/var type name'")
            ptparse_markfirsttokeninlist([pt])
            quit()

        # check if var / const:
        if ptparse_isToken(l[0],[("keyword","var")]):
            self.isMutable = True
        elif ptparse_isToken(l[0],[("keyword","const")]):
            self.isMutable = False
        else:
            print("PTParseError: syntax error: expected 'const/var'")
            ptparse_markfirsttokeninlist([l[0]])
            quit()

        # check type:
        self.type = ptparse_type(l[1])

        # check name:
        if ptparse_isToken(l[2],[("name",None)]):
            self.token_ = l[2][1]
            self.name = l[2][1].value
        else:
            print("PTParseError: syntax error: expected 'const/var'")
            ptparse_markfirsttokeninlist([l[2]])
            quit()

    def isReadable(self):
        return True
    def isWritable(self):
        return True

    def token(self):
        return self.token_

    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[{'var' if self.isMutable else 'const'}] {self.name}")
        print(" "*depth + f"type:")
        self.type.print_ast(depth = depth+step)

    def codegen_expression(self,codectx,needImmediate):
        """check super for desc
        if needImmediate is set, this will fail.
        does not return anything.
        """
        if needImmediate:
            print(f"error: variable declaration cannot be used as static value (is not immediate value).")
            self.token().mark()
            quit()
        
        # check if name already exists
        ret = codectx.function_get_name(self.name)
        if not (ret is None):
            print(f"error: '{self.name}' duplicate declaration.")
            self.token().mark()
            quit()

        # allocate variable
        if self.type.isNumber():
            codectx.function_alloc_var_with_type(self.name,self.type, self.isMutable)
        else:
            print(self.type.toStr())
            self.token().mark()
            assert(False and "local var decl not implemented for non number types")

        return ASTObjectTypeVoid(None,token=self.token()),True,None

    def codegen_assign(self,codectx,needImmediate,aType,aReg,aVal):
        """check super for desc"""
        # allocate via expression:
        eType,eReg,eVal = self.codegen_expression(codectx,needImmediate)

        # new assign to the variable
        astname = ASTObjectExpressionName(None,self.name,self.token())
        return astname.codegen_assign(codectx, needImmediate, aType,aReg,aVal)

 
class ASTObjectExpressionName(ASTObjectExpression):
    """const/variable name"""
    def __init__(self,pt, _name = None, _token = None):
        """either init via pt, or set _name and _token"""
        if _name is None:
            isToken, payload = pt
            assert(isToken)
            tk = payload
            assert(tk.name == "name")
            self.name = tk.value
            self.token_ = tk
        else:
            self.name = _name
            self.token_ = _token

    def isReadable(self):
        return True
    def isWritable(self):
        return True

    def token(self):
        return self.token_
 
    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[name] {self.name}")

    def codegen_expression(self,codectx,needImmediate):
        """check super for desc"""
        if needImmediate:
            print(f"error: '{self.name}' cannot be accessed statically (is not an immediate value).")
            self.token().mark()
            quit()
        
        # find out if global or local:
        ret = codectx.function_get_name(self.name)
         
        if ret is None:
            print(f"error: '{self.name}' undefined (first use in function).")
            self.token().mark()
            quit()
        
        kind,vType,isMutable = ret

        if kind == 0 or kind == 1:# global or local
            memloc = ""
            if kind == 0:
                memloc = f"{self.name}(%rip)"
            else:
                memloc = codectx.function_var_access_str(self.name)
            
            if vType.isNumber():
                size = ASTObjectTypeNumber_types[vType.name]
                asmType = ASM_size_to_type[size]
                if vType.name in ASTObjectTypeNumber_types_float:
                    suffix = "s" if vType.name == "float" else "d"
                    
                    ## load to xmm0
                    codectx.function_put_code(f"movs{suffix} {memloc}, %xmm0 # %xmm0 = {self.name}")
                    return vType,True,None
                else:
                    letter = ASM_type_to_letter[asmType]
                    rax = ASM_type_to_rax[asmType]
                    codectx.function_put_code(f"mov{letter} {memloc}, %{rax} # %rax = {self.name}")
                    return vType,True,None
            else:
                print(f"TypeError: cannot assign '{aType.toStr()}' to anything.")
                self.token().mark()
                quit()
                
        else:
            assert(False and "should never end here")

    
    def codegen_assign(self,codectx,needImmediate,aType,aReg,aVal):
        """check super for desc"""
        # find out if global or local:
        ret = codectx.function_get_name(self.name)
        
        if ret is None:
            print(f"error: '{self.name}' undefined (first use in function).")
            self.token().mark()
            quit()
        
        kind,vType,isMutable = ret
        
        # check if constant:
        if not isMutable:
            print(f"error: cannot write to constant '{self.name}'.")
            self.token().mark()
            quit()

        # check type conversions imm
        if (not aReg) and (not aType.equals(vType)):
            if aType.isNumber() and vType.isNumber():
                # immediate: number to number
                newVal = vType.softCastImmediate(aType,aVal)
                if not newVal is None:
                    aType = vType
                    aVal = newVal

        # check type conversion reg
        if aReg and (not aType.equals(vType)):
            if aType.isNumber() and vType.isNumber():
                # reg: number to number
                success = vType.softCastRegister(codectx, aType, ASM_type_to_rax, "xmm0")
                if not success:
                    print(f"TypeError: could not convert {aType.toStr()} to {vType.toStr()} for assignment.")
                    self.token().mark()
                    quit()
                # adjust aType:
                aType = vType
                    
       
        # if no method of changing it works:
        if not aType.equals(vType):
            print(f"TypeError: cannot assign '{aType.toStr()}' to '{vType.toStr()}'.")
            self.token().mark()
            quit()

        if kind == 0 or kind == 1:# global or local
            memloc = ""
            if kind == 0:
                memloc = f"{self.name}(%rip)"
            else:
                memloc = codectx.function_var_access_str(self.name)

            if aReg:
                if aType.isNumber():
                    if aType.name in ASTObjectTypeNumber_types_float:
                        suffix = "s" if aType.name == "float" else "d"
                        ## load from xmm0
                        codectx.function_put_code(f"movs{suffix} %xmm0, {memloc} # {self.name} = %xmm0")
                    else:
                        size = ASTObjectTypeNumber_types[aType.name]
                        asmType = ASM_size_to_type[size]
                        letter = ASM_type_to_letter[asmType]
                        rax = ASM_type_to_rax[asmType]
                        codectx.function_put_code(f"mov{letter} %{rax}, {memloc} # {self.name} = %{rax}")
                        
                else:
                    print(f"TypeError: cannot assign '{aType.toStr()}' to anything.")
                    assert(False)
            else:
                # immediate to var

                asmType,asmVal = number_to_integer_view(aType.name,aVal)
                if aType.isNumber():
                    if aType.name in ASTObjectTypeNumber_types_float:
                        suffix = "s" if aType.name == "float" else "d"
                        # dump value
                        tag = codectx.new_tag()
                        codectx.add_data_item(tag,asmType,asmVal,False)
                        # load via xmm0
                        codectx.function_put_code(f"movs{suffix} {tag}(%rip), %xmm0 # {self.name} = {aVal}")
                        codectx.function_put_code(f"movs{suffix} %xmm0, {memloc}")
                    else:
                        letter = ASM_type_to_letter[asmType]
                        codectx.function_put_code(f"mov{letter} ${asmVal}, {memloc} # {self.name} = {aVal}")
                else:
                    print(f"TypeError: cannot assign '{aType.toStr()}' to anything.")
                    assert(False)
                    
        else:
            assert(False and "should never end here")

        return aType,aReg,aVal

class ASTObjectExpressionNumber(ASTObjectExpression):
    """literal number expression"""
    def __init__(self,pt):
        isToken, payload = pt
        assert(isToken)
        tk = payload
        assert(tk.name == "num")
        self.number = tk.value
        self.token_ = tk

    def isReadable(self):
        return True
    def isWritable(self):
        return False

    def token(self):
        return self.token_
 
    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[number] {self.number}")

    def codegen_expression(self,codectx,needImmediate):
        """See super for desc"""
        # TODO: add multiple number types
        if "." in self.number:
            return ASTObjectTypeNumber(None,"double"), False, np.double(self.number)
        
        else:
            return ASTObjectTypeNumber(None,"u64"), False, np.uint64(self.number)

class ASTObjectExpressionString(ASTObjectExpression):
    """literal string expression"""
    def __init__(self,pt):
        isToken, payload = pt
        assert(isToken)
        tk = payload
        assert(tk.name == "str")
        self.string = tk.value
        self.token_ = tk

    def isReadable(self):
        return True
    def isWritable(self):
        return False

    def token(self):
        return self.token_
 
    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[string] '{self.string}'")


class ASTObjectExpressionReturn(ASTObjectExpression):
    """return statement"""
    def __init__(self,pt):
        isToken, payload = pt
        assert(not isToken)
        tokens,listoflists = payload
        assert(len(tokens)==0)
        assert(len(listoflists)==1)
        l = listoflists[0]

        if not ptparse_isToken(l[0], [("keyword","return")]):
            print("PTParseError: expected return statement.")
            ptparse_markfirsttokeninlist([l[0]])
            quit()

        self.token_ = l[0][1]

        if len(l) !=2:
            print(f"PTParseError: syntax error in print statement. (expected 'return <expression>')")
            ptparse_markfirsttokeninlist([l[0]])
            quit()

        self.expression = ptparse_expression(l[1])

        if not self.expression.isReadable():
            print("PTParseError: cannot read/evaluate return expression.")
            ptparse_markfirsttokeninlist([l[1]])
            quit()

    def isReadable(self):
        return False
    def isWritable(self):
        return False

    def token(self):
        return self.token_
 
    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[return]")
        print(" "*depth + f"expression:")
        self.expression.print_ast(depth = depth+step)

class ASTObjectVarConst(ASTObject):
    """
    Var/Const ast object
    """

    def __init__(self,pt):
        self.isMutable = False # var/const - True/False
        # True iff: defined as var or only with type or only assigned to
        # if the variable was previously defined as a constant, this may lead to a conflict!
        # False iff: defined as const.
        self.name = None # string
        self.name_token = None
        self.type = None # sub ast
        self.expression = None # sub ast, can be None

        # check if is assignment =
        if ptparse_isdelimiterlist(pt,[("operator","=")]):
            # split by first =
            isToken,(tokens,listoflists) = pt
            lhs = (False,([],[listoflists[0]]))
            rhs = (False,(tokens[1:],listoflists[1:]))

            self.expression = ptparse_expression(rhs)
        else:
            lhs = pt

        # parse var / const definition
        l = ptparse_getlist(lhs, 3)
        if l is None:
            print("PTParseError: syntax error: expected 'const/var type name'")
            ptparse_markfirsttokeninlist([lhs])
            quit()

        # check if var / const:
        if ptparse_isToken(l[0],[("keyword","var")]):
            self.isMutable = True
        elif ptparse_isToken(l[0],[("keyword","const")]):
            self.isMutable = False
        else:
            print("PTParseError: syntax error: expected 'const/var'")
            ptparse_markfirsttokeninlist([l[0]])
            quit()

        # check type:
        self.type = ptparse_type(l[1])

        # check name:
        if ptparse_isToken(l[2],[("name",None)]):
            self.name_token = l[2][1]
            self.name = l[2][1].value

    def token(self):
        return self.name_token

    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[{'var' if self.isMutable else 'const'}] {self.name}")
        print(" "*depth + f"type:")
        self.type.print_ast(depth = depth+step)
        if self.expression is not None:
            print(" "*depth + f"expression:")
            self.expression.print_ast(depth = depth+step)
    
    def checkType(self,typectx):
        """Only check type of variable"""
        self.type.checkValid(typectx)
    
    def checkCompatible(self,other):
        """checks if two VarConst objects are compatible.
        returns: error if not compatible (aborts)
        or the definition if one exists
        or else self 
        """
        if not (self.isMutable == other.isMutable):
            print("PTParseError: conflicting var/const declaration.")
            self.token().mark()
            other.token().mark()
            quit()

        if (not self.expression is None) and (not other.expression is None):
            print("PTParseError: duplicate definition.")
            self.token().mark()
            other.token().mark()
            quit()

        if not self.type.equals(other.type):
            print("TypeError: conflicting declarations.")
            self.token().mark()
            other.token().mark()
            quit()

        if other.expression:
            return other
        return self
    
class ASTObjectBase(ASTObject):
    """
    Base ast object for a file
    """

    def __init__(self, pt):
        ## ----------------- init
        # name used
        self.names = {}
        # global functions
        self.functions = {}
        # global variables / constants
        self.varconst = {} # declaration/definition
        self.varconst_definitions = [] # order of definitions
        # structs
        self.structs = {}

        ## ----------------- parse
        self.init_parse(pt)
    
    def check_name(self,ast):
        """check if name of ast is already taken"""
        if ast.name in self.names:
            print("PTParseError: duplicate name definition.")
            ast.token().mark()
            self.names[ast.name].token().mark()
            quit()
 
    def add_varconst(self, var):
        """ var: ASTObjectVarConst
        """
        # check if varconst already given
        if var.name in self.varconst:
            var2 = self.varconst[var.name]
            # check compatibility
            var = var.checkCompatible(var2)
        else:
            self.check_name(var)
        self.names[var.name] = var
        self.varconst[var.name] = var
        if var.expression: # order of definitions
            self.varconst_definitions.append(var)

    def add_struct(self, struct):
        """ var: ASTObjectStruct
        """
        self.check_name(struct)
        self.names[struct.name] = struct
        self.structs[struct.name] = struct

    def add_function(self, func):
        """ func: ASTObjectFunction
        """
        # check if function already given
        if func.name in self.functions:
            func2 = self.functions[func.name]
            # check compatibility
            func = func.checkCompatible(func2)
        else:
            self.check_name(func)
        self.names[func.name] = func
        self.functions[func.name] = func

    def init_parse(self,pt):
        """used in __init__ to do the parsing"""
        
        # expect: semicolon list (or else take as single item)
        pt = ptparse_strip(pt)
        tokens, listoflists = ptparse_delimiter_list(pt,[("semicolon",";")])

        # per list expect: var, const, function, struct (or empty)
        for l in listoflists:
            if len(l)==0:
                continue
            elif ptparse_isToken(l[0],[("keyword","var")]):
                # var type name
                var = ASTObjectVarConst((False,([],[l])))
                self.add_varconst(var)

            elif ptparse_isToken(l[0],[("keyword","const")]):
                # const type name
                var = ASTObjectVarConst((False,([],[l])))
                self.add_varconst(var)
                
            elif ptparse_isToken(l[0],[("keyword","function")]):
                # function type name (bracket-body) {bracket-body}
                func = ASTObjectFunction((False,([],[l])))
                self.add_function(func)
            
            elif ptparse_isToken(l[0],[("keyword","struct")]):
                # struct name {bracket-body}
                struct = ASTObjectStruct((False,([],[l])))
                self.add_struct(struct)

            elif ptparse_isdelimiterlist(l[0],[("operator","=")]):
                assert(len(l)==1)
                # var/cont type name = expression
                var = ASTObjectVarConst(l[0])
                self.add_varconst(var)
            else:
                print("PTParseError: bad syntax (expect: var, const, function or struct statement)")
                ptparse_markfirsttokeninlist(l)
                quit()

    
    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[Base]")
        print(" "*depth + f"varconst:")
        for name,var in self.varconst.items():
            var.print_ast(depth = depth+step)
        print(" "*depth + f"structs:")
        for name,struct in self.structs.items():
            struct.print_ast(depth = depth+step)
        print(" "*depth + f"functions:")
        for name,func in self.functions.items():
            func.print_ast(depth = depth+step)

    def typecheck(self):
        typectx = TypeCTX() # new type context
        self.typectx = typectx

        # 1 collect all struct names
        #   typecheck struct members, including no cycles
        typectx.register_structs(self.structs)

        # 2 collect function types of functions
        typectx.check_function_signatures(self.functions)

        # 3 collect types of globals
        typectx.check_globals(self.varconst)

    def codegen(self, filename, outfile):
        #codectx = CodeCTX(filename,self.typectx)
        #codectx.add_data_item("num1","byte",5,True)
        #codectx.add_data_item("num2","short",1000,True)
        #codectx.add_data_item("num3","long",1000000,True)
        #codectx.add_data_item("num4","quad",1000000000000,True)
        #tag = codectx.new_tag()
        #codectx.add_data_item(tag,"string","hello world",False)
        #codectx.add_data_item("str1","pointer",tag,True)
        #codectx.function_open("func1")
        #codectx.function_alloc_var_from_reg("a","rdi")
        #codectx.function_alloc_var_from_reg("b","rsi")
        #codectx.function_alloc_var_from_reg("c","rdx")
        #codectx.function_var_to_reg("c","rax")
        #codectx.function_var_to_reg("b","rcx")
        #codectx.function_var_to_reg("a","rdx")
        #codectx.function_put_code("addl %ecx, %eax")
        #codectx.function_put_code("addl %edx, %eax")

        ##codectx.function_reg_to_var("a","rdi")
        ##codectx.function_var_to_reg("a","rax") # return
        #codectx.function_close()
        #
        #codectx.function_open("func2")
        #tag = codectx.new_tag()
        #codectx.add_data_item(tag,"string","new string",False) # string immediate
        #codectx.function_put_code(f"leaq {tag}(%rip), %rax") # tag to reg
        #codectx.function_put_code("movq %rax, str1(%rip)") # reg to global
        #codectx.function_close()
        #codectx.write(filename,outfile)
        
        
        codectx = CodeCTX(filename,self.typectx)
        
        # 1: code gen for globals
        self.codegen_globals(codectx)

        # 2: code gen for functions
        self.codegen_functions(codectx)
        
        codectx.write(filename,outfile)

    def codegen_globals(self,codectx):
        for name,var in self.varconst.items():
            assert(type(var) == ASTObjectVarConst)
            codectx.add_global(var.name,var.type,var.isMutable)
            if var.expression is not None:
                eType,eReg,eVal = var.expression.codegen_expression(codectx,needImmediate=True)
                assert(eReg == False)
                
                newVal = var.type.softCastImmediate(eType,eVal)
                if newVal is None:
                    print(f"TypeError: cannot assign {eType.toStr()} to {var.type.toStr()}")
                    var.token().mark()
                    quit()

                # now can assume newVal has type var.type
                if var.type.isNumber():
                    asmType,newVal = number_to_integer_view(var.type.name,newVal)
                    codectx.del_name(var.name) # name hack to have global + value for global
                    codectx.add_data_item(var.name,asmType,newVal,True)
                else:
                    print(f"Not implemented {var.type.toStr()} global assignment.")
            

    def codegen_functions(self,codectx):
        for name,func in self.functions.items():
            # 1 open function
            codectx.function_open(name)
            
            # 2 put arg into local variables
            #codectx.function_alloc_var_from_reg("a","rdi")
            #codectx.function_alloc_var_from_reg("b","rsi")
            #codectx.function_alloc_var_from_reg("c","rdx")
        
            # 3 body
            ##codectx.function_var_to_reg("a","rax") # return
            
            codectx.function_put_code("")
            eType,eReg,eVal = func.body.codegen_expression(codectx,needImmediate=False)

            # 4 close function
            codectx.function_close()


class PTParser():
    """Take parse tree pt, produce ast of AST objects
    Via recursive decent.
    The main magic is implemented via the AST objects,
    which get a sub pt, and must recursively
    extract subsub pt's and launch sub AST objects.
    """
    def __init__(self):
        pass

    def parse(self, pt):
        """parsing a pt into an ast
        input: pt that needs to be turned into ast
        """
        return ASTObjectBase(pt)



def main(argv):
    if len(argv) > 1:
        filename = argv[0]
        outfile = argv[1]
        with open(filename, "r") as f:
            seq = f.read()
    else:
        print("Input error: need file input and output for parser/compiler!")
        quit()
    
    l = lexer.BasicLexer()
    
    print("Lexing...")
    tokens = l.lex(seq,filename)
    print([str(t) for t in tokens])
    
    print("Parsing tokens into pt ...")
    
    p = BasicParser()
   
    pt = p.parse(tokens)
    print(pt)
    p.print_parse_tree(pt)

    print("Parsing pt into ast ...")
    ptp = PTParser()
    
    pt2 = ptparse_strip(pt)
    p.print_parse_tree(pt)

    ast = ptp.parse(pt)
    ast.print_ast()

    ast.typecheck()
    
    print("Generating code now")
    ast.codegen(filename, outfile)

if __name__ == "__main__":
    main(sys.argv[1:])


