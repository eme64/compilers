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
    
    print("Parsing...")
    
    p = Parser()
    
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
    
    def rule_delimiter_factory(token_dict):
        pass # TODO

    p.set_rules([
        rule_brackets,
        ])
    
    pt = p.parse(tokens, l)
    print(pt)
    p.print_parse_tree(pt)


if __name__ == "__main__":
    main(sys.argv[1:])


