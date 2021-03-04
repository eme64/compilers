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
from collections import deque
import lexer
import math

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
    
    def typecheck(self,typectx):
        """
        input: TypeCTX
        output: return type

        determines types
        checks for automatic conversions
        checks if types consistent
        """
        assert(False and "typecheck not implemented")

class TypeCTX:
    """
    Keeps information about types
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

        print("size",self.sizeforname)
        print("alig",self.alignmentforname)
        print("offset",self.structmemberoffset)
        assert(False)

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
    
    print("ptparse_type",pt)
    isToken,payload = pt

    if isToken:
        tk = payload
        if tk.name == "name" or tk.name == "type":
            if tk.value in ASTObjectTypeNumber_types:
                return ASTObjectTypeNumber(pt)
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
                print("function type!",ll)
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

    def checkValid(self, typectx):
        """Check if a type is valid"""
        assert(False and "not implemented")

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


ASTObjectTypeNumber_types = {
        "i32":4,
        "float":4,
        "double":8,
        "u64":8,
        "u32":4,
        "u16":2,
        "u8":1,
        }# numbers are size in bytes

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

 
class ASTObjectTypeFunction(ASTObjectType):
    """
    function type ast object
    """
    def __init__(self,pt):
        isToken,payload = pt
        assert(not isToken)
        tokens,listoflists = payload
        assert(len(tokens)==0)
        assert(len(listoflists)==1)
        ll = listoflists[0]
        assert(len(ll)==2)

        # return type:
        print("top",pt)
        print("check",ll[0])
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

class ASTObjectFunction(ASTObject):
    """
    Function ast object
    """

    def __init__(self,pt):
        # function type name (bracket-body) {bracket-body}
        l = ptparse_getlist(pt, 5) # get the 5 elements
        if l is None:
            print("PTParseError: syntax error: expected 'function type name (args) {body}'")
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
                self.add_argument(arg)
                        
        # check body:
        # l[4]
        # expect (comma list):
        unpack = ptparse_unpack_brackets(l[4],"{")
        if unpack is None:
            print("PTParseError: syntax error: expected function body brackets.")
            ptparse_markfirsttokeninlist([l[4]])
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
        print(" "*depth + f"body:")
        for exp in self.body:
            exp.print_ast(depth = depth+step)
 
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

class ASTObjectExpressionName(ASTObjectExpression):
    """const/variable name"""
    def __init__(self,pt):
        isToken, payload = pt
        assert(isToken)
        tk = payload
        assert(tk.name == "name")
        self.name = tk.value
        self.token_ = tk

    def isReadable(self):
        return True
    def isWritable(self):
        return True

    def token(self):
        return self.token_
 
    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[name] {self.name}")

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
        self.varconst = {}
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
        self.check_name(var)
        self.names[var.name] = var
        self.varconst[var.name] = var

    def add_struct(self, struct):
        """ var: ASTObjectStruct
        """
        self.check_name(struct)
        self.names[struct.name] = struct
        self.structs[struct.name] = struct

    def add_function(self, func):
        """ func: ASTObjectFunction
        """
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
        
        # 1 collect all struct names
        #   typecheck struct members, including no cycles
        typectx.register_structs(self.structs)

        # 2 collect function types of functions
        # 3 collect types of globals
        # 4 evaluate global assignments
        # 5 type check function bodies
        assert(False and "not fully implemented")
 
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
    if len(argv) > 0:
        filename = argv[0]
        with open(filename, "r") as f:
            seq = f.read()
    else:
        print("Input error: need file input for parser!")
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


if __name__ == "__main__":
    main(sys.argv[1:])


