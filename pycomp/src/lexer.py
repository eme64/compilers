#!/usr/bin/env python3

class CharSets:
    """Member functions provide common lists of characters"""

    def whitespace(self):
        return [ord(c) for c in " \t\n"]
    
    def digit(self):
        return [ord(c) for c in "0123456789"]
    
    def letter(self):
        lower = list(range(ord('a'), ord('z')+1))
        upper = list(range(ord('A'), ord('Z')+1))
        return lower+upper

    def bracket(self):
        return [ord(c) for c in "()[]{}"]

class Lexer:
    """FSM based lexer
    
    state: one of finetely many, "init" is the initial state
    start: points to first character of current token
    action(line,linenum,state,start,pos): decide what to do with newly added character at position pos.
    tokens: list of already processed tokens, can append new tokens
    rules: list of (state,character,action) tuples. given a state and next character, choose action.
    """

    def __init__(self):
        """Constructor"""
        print("new lexer")
        self.rules = []
        self.state_dict = {}
    
    def push_token(self, name, value):
        """Push current token for a type name and value
        
        internally, also start position in line are remembered
        """
        token = (name,value,self.line,self.start)
        print("push_token:",token)
        self.tokens.append(token)


    def set_rules(self, rules):
        """argument: rules, list of (state, [chars], action) tuples.
        chars is a list of characters (ord)
        action(line,linenum,state,start,pos): returns (accept, state, start)
        if accept is false, the current character is tried again, else advanced
        """
        self.rules = rules

        self.state_dict = {}
        for state,characters,action in self.rules:
            #print("chars:", characters)
            #print("chars:", [chr(c) for c in characters])

            if not state in self.state_dict:
                self.state_dict[state] = {} # ensure exists
            
            sd = self.state_dict[state]

            for c in characters:
                if c in sd:
                    print(f"Error: already found {c} '{chr(c)}' in state_dict for state '{state}'")
                    quit()
                sd[c] = action
            

    def lex(self, seq, filename):
        """lexes a sequence seq, returns a list of tokens. filename for error messages"""
        self.tokens = []
        self.start = 0
        self.line = 0
        self.state = "init"
        self.pos = 0

        lines = [l+"\n" for l in seq.splitlines()]
        
        while True:
            # check if rule available for state:
            if not self.state in self.state_dict:
                print(f"Error: state '{self.state}' has no rules")
                quit()
            
            sd = self.state_dict[self.state]
            c = ord(lines[self.line][self.pos])
            
            # check if rule available for character and state
            action = None
            if c in sd:
                action = sd[c]
            elif -1 in sd:
                action = sd[-1]
            else:
                print(f"Error: unexpected character {c} '{chr(c)}' for state {self.state}")
                print(f"in {filename}:{self.line}")
                print(lines[self.line][:-1])
                print(" "*self.pos+"^")
                quit()
            
            accept, state, start = action(lines[self.line], self.line, self.state, self.start, self.pos)

            self.state = state
            self.start = start
            
            if accept:
                self.pos += 1
                if self.pos >= len(lines[self.line]):
                    # end of line, already passed "\n"
                    if self.state != "init":
                        print(f"Error: end of line not 'init' but '{self.state}' state for line {self.line}")
                        print(lines[self.line])
                        quit()
                    self.start = 0
                    self.pos = 0
                    self.line += 1


        return self.tokens

def main():
    print("hello world")
    l = Lexer()

    seq = """
    var int x;
    ;;;
    ;

    x = 5;
    print(x);
    """
    
    cs = CharSets()

    def action_whitespace(line,linenum,state,start,pos):
        return (True, "init", pos+1)
    
    # names:
    #   letters, digit, underscore
    #   but cannot start with digit
    
    def action_name(line,linenum,state,start,pos):
        return (True, "name", start)
    def action_name_end(line,linenum,state,start,pos):
        value = line[start:pos]
        l.push_token("name", value)
        return (False,"init", pos)
    
    # separators:
    def action_semicolon(line,linenum,state,start,pos):
        l.push_token("semicolon", ";")
        return (True,"init", pos+1)
    def action_comma(line,linenum,state,start,pos):
        l.push_token("comma", ",")
        return (True,"init", pos+1)
    
    # operators:
    #   some are single char, some multichar.
    #   list below is then converted into query structure
    operators = ["=", "==", "<", ">", "<=", ">=", "!", "!=",
                 "&", "&&", "|" "||", "%", "^", ">>", "<<",
                 "*", "/", "~",
                 "+", "++", "-", "--", "->", ".", "+=", "-="]
    
    operator_char = list(set([ord(c) for o in operators for c in o]))

    operator_tree = {}

    for o in operators:
        t = operator_tree
        # traverse tree
        for char in o:
            c = ord(char)
            if not c in t:
                t[c] = {}
            t = t[c]
        # place an item there
        t[0] = o

    def action_operator(line,linenum,state,start,pos):
        l.push_token("operator", line[start:pos+1])
        return (True, "init", pos+1)
        # TODO: implement correctly

    # numbers:
    def action_digit(line,linenum,state,start,pos):
        return (True, "num", start)
        # TODO: implement correctly
    

    l.set_rules([
        # whitespaces:
        ("init", cs.whitespace(),                         action_whitespace),
        
        # operators
        ("init", operator_char,                           action_operator),
        
        # names:
        ("init", cs.letter() + [ord("_")],                action_name),
        ("name", cs.letter() + cs.digit() + [ord("_")],   action_name),
        ("name", [-1],                                    action_name_end),
        
        # separators:
        ("init", [ord(";")],                              action_semicolon),
        ("init", [ord(",")],                              action_comma),
        
        # numbers
        ("init", cs.digit(),   action_digit),
        ])

    tokens = l.lex(seq, "test.script")
    print(tokens)

if __name__ == "__main__":
    main()


