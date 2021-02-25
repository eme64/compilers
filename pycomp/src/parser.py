#!/usr/bin/env python3

import sys
from collections import deque
import lexer

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
    
    def parse_apply_rule(self, rule, pt, lex):
        """traversal impl for parse"""
        # Traversal bottom up (post order)
        
        isToken, payload = pt
        if not isToken:
            tokens, listoflists = payload
            # recurse
            listoflists = [[self.parse_apply_rule(rule, i, lex) for i in l] for l in listoflists]
            # post order
            listoflists = [rule(l, lex) for l in listoflists]
            
            # reconstruct pt node
            return (False,(tokens, listoflists))
        else:
            return pt # just return token

    def parse(self,tokens, lex):
        """argument lex: for error messages
        
        Input: tokens from lexer
        Output: pt
        """
        lst = [(True,t) for t in tokens]
        pt = (False, ([], [lst]))
        for rule in self.rules:
            # Traverse old pt, generate a new one
            pt = self.parse_apply_rule(rule, pt, lex)
        return pt

    def set_rules(self,rules):
        """
        rules: list of rules
        rule is a function: rule(nodes, lex) -> new node list
        """
        self.rules = rules

    def print_parse_tree(self, pt, depth=0,step=3):
        """purely for debugging purposes"""
        isToken, payload = pt
        if isToken:
            tname,tval,tline,tstart = payload
            print(" "*depth + f"<{tname:10}> {tval}")
        else:
            tokens,listoflists = payload
            for t in tokens:
                tname,tval,tline,tstart = t
                print(" "*depth + f"[{tname:10}] {tval}")
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

        def rule_brackets(nodes, lex):
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
                    token = payload
                    tname,tval,tline,tstart = token
                    if tname == "bracket":
                        if tval in bracket_map:
                            # close bracket
                            # check if there is an opening bracket:
                            if cur_token is None:
                                print("ParseError: missing opening bracket.")
                                lex.mark_token(token)
                                quit()
                            
                            # check if matches cur_token
                            expect = bracket_map[tval]
                            cur_token_val = cur_token[1]

                            if cur_token_val == expect:
                                # create a new bracket pt node:
                                new_node = (False,([cur_token,token],[cur_nodes]))
                                # pop from stack
                                cur_token, cur_nodes = q.pop()

                                # insert new node
                                cur_nodes.append(new_node)
                            else:
                                print("ParseError: closing bracket did not match with opening bracket.")
                                lex.mark_token(cur_token)
                                lex.mark_token(token)
                                quit()

                        else:
                            # open bracket
                            # push cur to stack
                            q.append((cur_token,cur_nodes))
                            cur_token = token
                            cur_nodes = []
                    else:
                        cur_nodes.append(pt)
                else:
                    cur_nodes.append(pt)

            # check if all brackets were matched:
            if not cur_token is None:
                print("ParseError: opening bracket without closing bracket.")
                lex.mark_token(cur_token)
                quit()

            return cur_nodes
        
        def rule_delimiter_factory(token_list):
            """generates a rule that splits lists whereever a token is matched
            token_list = list of (tname,tval)
            if no such token is found the nodelist will be untouched.
            else, we list all n tokens and all n+1 sublists.
            """
            token_dict = {t:0 for t in token_list}

            def rule(nodes, lex):
                # check for occurances:
                occ = 0
                for pt in nodes:
                    isToken,payload = pt
                    if isToken:
                        tname,tval,_,_ = payload
                        key = (tname,tval)
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
                        tname,tval,_,_ = payload
                        key = (tname,tval)
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

    def __init__(self, pt, lex, parent):
        """
        pt, lex: what it was generated from
        parent: parent AST object. May be handy if some context is required.
        """
        pass

    def print_ast(self,depth=0,step=3):
        """recursive print the ast"""
        print(" "*depth + f"<print_ast Error: Not implemented! {type(self)}>")

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
    
    if tokens[0][0] != "bracket" or tokens[0][1] != bracket:
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
        return ([],[pt])
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
                tname,tval,_,_ = t
                if (not (tname,tval) in ddict) and (not (tname,None) in ddict):
                    # bad token
                    return ([],[pt])
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
                tname,tval,_,_ = t
                if (not (tname,tval) in ddict) and (not (tname,None) in ddict):
                    # bad token
                    return False
            # all tokens were ok
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
        tname,tval,_,_ = payload
        if (tname,tval) in tdict or (tname,None) in tdict:
            return True
        else:
            return False

def ptparse_tokenmin(t1,t2):
    """returns the first of the two tokens"""
    if t1 is None:
        return t2
    if t2 is None:
        return t1
    _,_,t1l,t1s = t1
    _,_,t2l,t2s = t2
    if t1l < t2l or (t1l==t2l and t1s <= t2s):
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

def ptparse_markfirsttokeninlist(l,lex):
    """takes list of pt's, search recursively for first token"""
    cur = None
    for pt in l:
        cur = ptparse_tokenmin(cur, ptparse_getfirsttoken(pt))
    lex.mark_token(cur)


def ptparse_getlist(pt,lex,k):
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

def ptparse_expression(pt,lex, parent):
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
        tname,tval,_,_ = payload

        if tname == "name":
            return ASTObjectExpressionName(pt,lex,parent)
        elif tname == "string":
            # TODO
            assert(False and "string")
        elif tname == "num":
            return ASTObjectExpressionNumber(pt,lex,parent)
        else:
            print("PTParseError: unexpected token (expected: name, string or number)")
            lex.mark_token(payload)
            quit()
            
    else:
        tokens, listoflists = payload
        if len(tokens) == 0:
            assert(len(listoflists)==1)
            ll = listoflists[0]
            if len(ll) == 0:
                # TODO
                assert(False and "nothing")
            elif len(ll) == 1:
                # must unpack
                ptsub = ll[0]
                return ptparse_expression(ptsub,lex, parent)
            elif ptparse_isToken(ll[0], [("name","var"),("name","const")]):
                # var/const definition
                return ASTObjectExpressionDeclaration(pt, lex, parent)
            elif ptparse_isToken(ll[0], [("name","return")]):
                # return statement
                return ASTObjectExpressionReturn(pt,lex,parent)
            else:
                # list of elements: function calls
                # TODO
                print(ll)
                assert(False and "function calls")
        else:
            # inspect first token:
            tname,tval,_,_ = tokens[0]
            if tname == "operator":
                return ptparse_expression_operator(pt, lex, parent)
            elif tname == "bracket":
                # TODO
                assert(False and "bracket")
            else:
                print(tokens)
                assert(False and "unhandled token")

def ptparse_expression_operator(pt,lex,parent):
    """Parse operator expression."""
    isToken, payload = pt
    assert(not isToken)
    tokens,listoflists = payload
    assert(len(tokens)>0)
    assert(tokens[0][0] == "operator")

    # inspect first token to see what operator we have here
    tname,tval,_,_ = tokens[0]

    if tval in ["=","+=","-=","/=","*="]:
        if len(tokens) > 1: # if multiple assignments: break ltr
            pt_ltr = ptparse_delimiterlist_ltr(pt,lex)
            return ptparse_expression_operator(pt_ltr,lex, parent)
        
        assert(len(listoflists)==2)
        return ASTObjectExpressionAssignment(pt, lex, parent)
    elif tval in ["+","-"]:
        if len(tokens) > 1: # if multiple assignments: break ltr
            pt_rtl = ptparse_delimiterlist_rtl(pt,lex)
            return ptparse_expression_operator(pt_rtl,lex, parent)
        
        assert(len(listoflists)==2)
        return ASTObjectExpressionBinOp(pt, lex, parent)
    else:
        print(tokens)
        assert(False and "token not handled")

def ptparse_delimiterlist_ltr(pt,lex):
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


# ##########################
# # ASTObjects for parsing #
# ##########################


class ASTObjectFunction(ASTObject):
    """
    Function ast object
    """

    def __init__(self,pt,lex,parent):
        # function type name (bracket-body) {bracket-body}
        l = ptparse_getlist(pt, lex, 5) # get the 5 elements
        if l is None:
            print("PTParseError: syntax error: expected 'function type name (args) {body}'")
            ptparse_markfirsttokeninlist([pt],lex)
            quit()

        # check that first is function
        if ptparse_isToken(l[0],[("name","function")]):
            pass
        else:
            print("PTParseError: syntax error: expected 'function'")
            ptparse_markfirsttokeninlist([l[0]],lex)

        # check type:
        # TODO l[1]

        # check name:
        if ptparse_isToken(l[2],[("name",None)]):
            self.name_token = l[2][1]
            self.name = l[2][1][1]
            #print(self.name)
            #lex.mark_token(self.name_token)
        
        # check args:
        # l[3]
        # expect (comma list):
        unpack = ptparse_unpack_brackets(l[3],"(")
        if unpack is None:
            print("PTParseError: syntax error: expected function argument brackets.")
            ptparse_markfirsttokeninlist([l[3]],lex)
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
                        lex.mark_token(tokens[0])
                        quit()
                    else:
                        print("PTParseError: syntax error: expected function argument after this comma.")
                        lex.mark_token(tokens[i-1])
                        quit()

        # parse the arguments
        for ll in listoflists:
            if len(ll)>0:
                arg = ASTObjectVarConst((False,([],[ll])), lex, self)
                self.add_argument(lex,arg)
                        
        # check body:
        # l[4]
        # expect (comma list):
        unpack = ptparse_unpack_brackets(l[4],"{")
        if unpack is None:
            print("PTParseError: syntax error: expected function body brackets.")
            ptparse_markfirsttokeninlist([l[4]],lex)
            quit()
        
        unpack = ptparse_strip(unpack)
        tokens,listoflists = ptparse_delimiter_list(unpack,[("semicolon",";")])

        # parse list of body instructions.
        # They are a sequence of expressions.
        # For this we apply a general expression detector.
        self.body = []
        for ll in listoflists:
            if len(ll) > 0:
                exp = ptparse_expression((False,([],[ll])), lex, self)
                self.body.append(exp)
    
    def add_argument(self,lex,arg):
        """arg: ASTObjectVarConst
        """
        self.varconst[arg.name] = arg
        self.arguments.append(arg)

    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[Function] {self.name}")
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

    def __init__(self,pt,lex,parent):
        # struct name {bracket-body}
        l = ptparse_getlist(pt, lex, 3) # get the 3 elements
        if l is None:
            print("PTParseError: syntax error: expected 'struct name {body}'")
            ptparse_markfirsttokeninlist([pt],lex)
            quit()

        # check that first is function
        if ptparse_isToken(l[0],[("name","struct")]):
            pass
        else:
            print("PTParseError: syntax error: expected 'function'")
            ptparse_markfirsttokeninlist([l[0]],lex)

        # check name:
        if ptparse_isToken(l[1],[("name",None)]):
            self.name_token = l[1][1]
            self.name = l[1][1][1]
            #print(self.name)
            #lex.mark_token(self.name_token)
        
        # check body:
        # TODO l[2]
 
    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[Struct] {self.name}")

class ASTObjectExpression(ASTObject):
    """
    Expression ast object
    this is the 
    """

    def __init__(self,pt,lex,parent):
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
    def __init__(self,pt,lex,parent):
        isToken, payload = pt
        assert(not isToken)
        tokens,listoflists = payload
        assert(len(tokens)>0)
        assert(tokens[0][0] == "operator")
        assert(len(listoflists)==2)
        tname,tval,_,_ = tokens[0]
        assert( tval in ["=","+=","-=","/=","*="] )
        
        lhs = listoflists[0]
        rhs = listoflists[1]

        self.operator = tval
        self.token_ = tokens[0]
        self.lhs = ptparse_expression((False,([],[lhs])), lex,self)
        self.rhs = ptparse_expression((False,([],[rhs])), lex,self)
        
        if not self.lhs.isWritable():
            print("PTParseError: cannot write to left-hand-side of this assignment.")
            lex.mark_token(tokens[0])
            quit()

        if tval != "=":
            if not self.lhs.isReadable():
                print("PTParseError: cannot read from left-hand-side of this read-modify-write operator.")
                lex.mark_token(tokens[0])
                quit()

        if not self.rhs.isReadable():
            print("PTParseError: cannot read/get value from right-hand-side of this assignment.")
            lex.mark_token(tokens[0])
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


class ASTObjectExpressionBinOp(ASTObjectExpression):
    """Binary operator of any kind
    reads both sides and returns some result
    """
    def __init__(self,pt,lex,parent):
        isToken, payload = pt
        assert(not isToken)
        tokens,listoflists = payload
        assert(len(tokens)==1)
        assert(tokens[0][0] == "operator")
        assert(len(listoflists)==2)
        tname,tval,_,_ = tokens[0]
        assert( tval in ["+","-"] )
        
        lhs = listoflists[0]
        rhs = listoflists[1]

        self.operator = tval
        self.token_ = tokens[0]
        self.lhs = ptparse_expression((False,([],[lhs])), lex,self)
        self.rhs = ptparse_expression((False,([],[rhs])), lex,self)
        
        if not self.lhs.isReadable():
            print("PTParseError: cannot read from left-hand-side of this binary operator.")
            lex.mark_token(tokens[0])
            quit()

        if not self.rhs.isReadable():
            print("PTParseError: cannot read from right-hand-side of this binary operator.")
            lex.mark_token(tokens[0])
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
    def __init__(self,pt,lex,parent):
        # parse var / const definition
        l = ptparse_getlist(pt, lex, 3)
        if l is None:
            print("PTParseError: syntax error: expected 'const/var type name'")
            ptparse_markfirsttokeninlist([pt],lex)
            quit()

        # check if var / const:
        if ptparse_isToken(l[0],[("name","var")]):
            self.isMutable = True
        elif ptparse_isToken(l[0],[("name","const")]):
            self.isMutable = False
        else:
            print("PTParseError: syntax error: expected 'const/var'")
            ptparse_markfirsttokeninlist([l[0]],lex)
            quit()

        # check type:
        # TODO: l[1] + print

        # check name:
        if ptparse_isToken(l[2],[("name",None)]):
            self.token_ = l[2][1]
            self.name = l[2][1][1]
        else:
            print("PTParseError: syntax error: expected 'const/var'")
            ptparse_markfirsttokeninlist([l[2]],lex)
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

class ASTObjectExpressionName(ASTObjectExpression):
    """const/variable name"""
    def __init__(self,pt,lex,parent):
        isToken, payload = pt
        assert(isToken)
        tname,tval,_,_ = payload
        assert(tname == "name")
        self.name = tval
        self.token_ = payload

    def isReadable(self):
        return True
    def isWritable(self):
        return True

    def token(self):
        return self.token_
 
    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[name] {self.name}")

class ASTObjectExpressionNumber(ASTObjectExpression):
    """const/variable name"""
    def __init__(self,pt,lex,parent):
        isToken, payload = pt
        assert(isToken)
        tname,tval,_,_ = payload
        assert(tname == "num")
        self.number = tval
        self.token_ = payload

    def isReadable(self):
        return True
    def isWritable(self):
        return False

    def token(self):
        return self.token_
 
    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[number] {self.number}")

class ASTObjectExpressionReturn(ASTObjectExpression):
    """return statement"""
    def __init__(self,pt,lex,parent):
        isToken, payload = pt
        assert(not isToken)
        tokens,listoflists = payload
        assert(len(tokens)==0)
        assert(len(listoflists)==1)
        l = listoflists[0]

        if not ptparse_isToken(l[0], [("name","return")]):
            print("PTParseError: expected return statement.")
            ptparse_markfirsttokeninlist([l[0]],lex)
            quit()

        self.token_ = l[0][1]

        if len(l) !=2:
            print(f"PTParseError: syntax error in print statement. (expected 'return <expression>')")
            ptparse_markfirsttokeninlist([l[0]],lex)
            quit()

        self.expression = ptparse_expression(l[1],lex,self)

        if not self.expression.isReadable():
            print("PTParseError: cannot read/evaluate return expression.")
            ptparse_markfirsttokeninlist([l[1]],lex)
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

    def __init__(self,pt,lex,parent):
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

            #self.expression = ASTObjectExpression(rhs,lex,self)
            self.expression = ptparse_expression(rhs,lex,self)
        else:
            lhs = pt

        # parse var / const definition
        l = ptparse_getlist(lhs, lex, 3)
        if l is None:
            print("PTParseError: syntax error: expected 'const/var type name'")
            ptparse_markfirsttokeninlist([lhs],lex)
            quit()

        # check if var / const:
        if ptparse_isToken(l[0],[("name","var")]):
            self.isMutable = True
        elif ptparse_isToken(l[0],[("name","const")]):
            self.isMutable = False
        else:
            print("PTParseError: syntax error: expected 'const/var'")
            ptparse_markfirsttokeninlist([l[0]],lex)
            quit()

        # check type:
        # TODO l[1]

        # check name:
        if ptparse_isToken(l[2],[("name",None)]):
            self.name_token = l[2][1]
            self.name = l[2][1][1]
            #print(self.name)
            #lex.mark_token(self.name_token)

    def print_ast(self,depth=0,step=3):
        print(" "*depth + f"[{'var' if self.isMutable else 'const'}] {self.name}")
        print(" "*depth + f"type:")
        if self.expression is not None:
            print(" "*depth + f"expression:")
            self.expression.print_ast(depth = depth+step)

class ASTObjectBase(ASTObject):
    """
    Base ast object for a file
    """

    def __init__(self, pt, lex, parent):
        ## ----------------- init
        self.parent = parent
        # name used
        self.names = {}
        # global functions
        self.functions = {}
        # global variables / constants
        self.varconst = {}
        # structs
        self.structs = {}

        ## ----------------- parse
        self.init_parse(pt,lex,parent)
    
    def add_varconst(self, lex, var):
        """ var: ASTObjectVarConst
        """
        # TODO: make function out of it, reject duplicates
        self.names[var.name] = var
        self.varconst[var.name] = var

    def add_struct(self, lex, struct):
        """ var: ASTObjectStruct
        """
        # TODO: make function out of it, reject duplicates
        self.names[struct.name] = struct
        self.structs[struct.name] = struct

    def add_function(self, lex, func):
        """ func: ASTObjectFunction
        """
        # TODO: make function out of it, reject duplicates
        self.names[func.name] = func
        self.functions[func.name] = func


    def init_parse(self,pt,lex,parent):
        """used in __init__ to do the parsing"""
        
        # expect: semicolon list (or else take as single item)
        pt = ptparse_strip(pt)
        tokens, listoflists = ptparse_delimiter_list(pt,[("semicolon",";")])

        # per list expect: var, const, function, struct (or empty)
        for l in listoflists:
            if len(l)==0:
                continue
            elif ptparse_isToken(l[0],[("name","var")]):
                # var type name
                var = ASTObjectVarConst((False,([],[l])) ,lex,self)
                self.add_varconst(lex,var)

            elif ptparse_isToken(l[0],[("name","const")]):
                # const type name
                var = ASTObjectVarConst((False,([],[l])) ,lex,self)
                self.add_varconst(lex,var)
                
            elif ptparse_isToken(l[0],[("name","function")]):
                # function type name (bracket-body) {bracket-body}
                func = ASTObjectFunction((False,([],[l])) ,lex,self)
                self.add_function(lex,func)
            
            elif ptparse_isToken(l[0],[("name","struct")]):
                # struct name {bracket-body}
                struct = ASTObjectStruct((False,([],[l])) ,lex,self)
                self.add_struct(lex,struct)

            elif ptparse_isdelimiterlist(l[0],[("operator","=")]):
                assert(len(l)==1)
                # var/cont type name = expression
                var = ASTObjectVarConst(l[0] ,lex,self)
                self.add_varconst(lex,var)
            else:
                print("PTParseError: bad syntax (expect: var, const, function or struct statement)")
                ptparse_markfirsttokeninlist(l,lex)
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
 
class PTParser():
    """Take parse tree pt, produce ast of AST objects
    Via recursive decent.
    The main magic is implemented via the AST objects,
    which get a sub pt, and must recursively
    extract subsub pt's and launch sub AST objects.
    """
    def __init__(self):
        pass

    def parse(self, pt, lex):
        """parsing a pt into an ast
        input: pt that needs to be turned into ast
        lex: lex object that was used to generate pt (used for error messages)"""
        return ASTObjectBase(pt,lex,None)



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
    print(tokens)
    
    print("Parsing tokens into pt ...")
    
    p = BasicParser()
   
    pt = p.parse(tokens, l)
    print(pt)
    p.print_parse_tree(pt)

    print("Parsing pt into ast ...")
    ptp = PTParser()
    
    pt2 = ptparse_strip(pt)
    p.print_parse_tree(pt)

    ast = ptp.parse(pt,l)
    ast.print_ast()


if __name__ == "__main__":
    main(sys.argv[1:])


