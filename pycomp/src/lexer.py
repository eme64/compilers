#!/usr/bin/env python3

import sys
import os

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
    
    def hex(self):
        lower = list(range(ord('a'), ord('f')+1))
        upper = list(range(ord('A'), ord('F')+1))
        return self.digit() + lower + upper


    def bracket(self):
        return [ord(c) for c in "()[]{}"]

    def legible(self):
        top = list(range(ord(' '), ord('~')+1))
        return top + ["\t"]
    
    def all(self):
        return list(range(256))
    
    def minus(self, base, sub):
        rhs = set(sub)
        return [c for c in base if not c in rhs]

class Token:
    def __init__(self,lex,name,value,line,start, parent = None):
        self.lex = lex
        self.name = name
        self.value = value
        self.line = line
        self.start = start
        self.parent = parent
        self.depth = 0
        if self.parent is not None:
            self.depth = self.parent.depth + 1
            if self.depth > 100:
                print("LexError: lexer depth exceeded.")
                self.mark()
                quit()

    def __repr__(self):
        return f"<{self.name}, {self.value}, {self.line}, {self.start}>"
    def mark(self):
        """Mark token"""
        if self.parent is not None:
            self.parent.mark()
        print(f"in {self.lex.filename}:{self.line}")
        print(self.lex.lines[self.line][:-1])
        print(" "*self.start+"^")

class Lexer:
    """FSM based lexer
    
    state: one of finetely many, "init" is the initial state, and the neutral state whenever no particular token is being tokenized
    start: points to first character of current token
    action(line,linenum,state,start,pos): decide what to do with newly added character at position pos.
    tokens: list of already processed tokens, can append new tokens
    rules: list of (state,character,action) tuples. given a state and next character, choose action.
    """

    def __init__(self):
        """Constructor"""
        self.rules = []
        self.state_dict = {}
        self.isUsed = False
        self.anchor_token = None
    
    def push_token(self, name, value):
        """Push current token for a type name and value
        
        internally, also start position in line are remembered
        """
        token = Token(self,name,value,self.line,self.start,self.anchor_token)
        #print("push_token:",token)
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
                    print(f"LexError: already found {c} '{chr(c)}' in state_dict for state '{state}'")
                    quit()
                sd[c] = action
            

    def lex(self, seq, filename):
        """lexes a sequence seq, returns a list of tokens. filename for error messages"""
        assert(self.isUsed == False)
        self.isUsed = True

        self.filename = filename
        self.tokens = []
        self.start = 0
        self.line = 0
        self.state = "init"
        self.pos = 0

        lines = [l+"\n" for l in seq.splitlines()]
        self.lines = lines

        while True:
            # check if rule available for state:
            if not self.state in self.state_dict:
                print(f"LexError (internal): state '{self.state}' has no rules")
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
                print(f"LexError: unexpected character {c} '{chr(c)}' for state {self.state}")
                self.mark_pos()
                quit()
            
            accept, state, start = action(lines[self.line], self.line, self.state, self.start, self.pos)

            self.state = state
            self.start = start
            
            if accept:
                self.pos += 1
                if self.pos >= len(lines[self.line]):
                    # end of line, already passed "\n"
                    if self.state != "init" and self.state != "com2":
                        print(f"LexError: end of line not 'init' but '{self.state}' state for line {self.line}")
                        print(lines[self.line])
                        quit()
                    self.start = 0
                    self.pos = 0
                    self.line += 1

                    if self.line >= len(lines):
                        break # end of file

        return self.tokens
    
    def mark_parent(self):
        if self.parent is not None:
            self.parent.mark_start()

    def mark_pos(self):
        self.mark_parent()
        print(f"in {self.filename}:{self.line}")
        print(self.lines[self.line][:-1])
        print(" "*self.pos+"^")

    def mark_line(self,linenum):
        self.mark_parent()
        print(f"in {self.filename}:{linenum}")
        print(self.lines[self.line][:-1])


    def mark_start(self):
        print(f"in {self.filename}:{self.line}")
        print(self.lines[self.line][:-1])
        print(" "*self.start+"^")


class BasicLexer(Lexer):
    """Lexer that is initialized with the rules to lex
    - names/identifiers
    - strings ""
    - numers (decimal with dot)
    - brackets ()[]{}
    - comma, semicolon
    - operators (for list see below)
    - single line comments starting with #
    
    Macros:
    - ECHO: prints whole line
    - IMPORT: lex other file, append tokens to list
    """
    def __init__(self, parent = None, anchor_token = None):
        super().__init__()
        self.parent = parent
        self.anchor_token = anchor_token

        ### set up rules:
        
        cs = CharSets()

        def action_whitespace(line,linenum,state,start,pos):
            return (True, "init", pos+1)
        
        keyword_names = {t:1 for t in [
                "struct","function","var","const",
                "cast","sizeof",
                "if","while","for",
                "return",
                ]}
        builtintype_names = {t:1 for t in [
                "i32",
                "float","double",
                "u64","u32","u16","u8",
                "void",
                ]}

        # names:
        #   letters, digit, underscore
        #   but cannot start with digit
        
        def action_name(line,linenum,state,start,pos):
            return (True, "name", start)
        def action_name_end(line,linenum,state,start,pos):
            value = line[start:pos]
            if value in keyword_names:
                self.push_token("keyword", value)
            elif value in builtintype_names:
                self.push_token("type", value)
            else:
                self.push_token("name", value)
            return (False,"init", pos)
        
        # separators:
        def action_semicolon(line,linenum,state,start,pos):
            self.push_token("semicolon", ";")
            return (True,"init", pos+1)
        def action_comma(line,linenum,state,start,pos):
            self.push_token("comma", ",")
            return (True,"init", pos+1)

        # brackets:
        def action_bracket(line,linenum,state,start,pos):
            value = line[start:pos+1]
            self.push_token("bracket", value)
            return (True,"init", pos+1)
        
        # operators:
        #   some are single char, some multichar.
        #   list below is then converted into query structure
        operators = ["==", "<", ">", "<=", ">=", "!", "!=",
                     "&", "&&", "|","||", "%", "^", ">>", "<<",
                     "*", "/", "~",
                     "+", "++", "-", "--", "->", ".",
                     "=","+=", "-=","/=","*=",
                     "//","/*",# For comments
                     ]
        
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

        def check_operator(last,curr):
            """check if operator last is extensible with character curr
            returns "extensible", "last", or "error"
            last is string
            curr is ord (-1 if just want to check if last is valid or not)
            """
            t = operator_tree
            # traverse tree
            for char in last:
                c = ord(char)
                if not c in t:
                    return "error"
                t = t[c]

            if curr in t:
                return "extensible"
            elif 0 in t:
                return "last" # 0 here means item was placed
            else:
                return "error"

        def action_operator(line,linenum,state,start,pos):
            last = line[start:pos]
            curr = line[pos]
            res = check_operator(last, ord(curr))

            if res == "extensible":
                return (True, "oper", start)
            elif res == "last":
                if last == "//": # comment
                    return (False,"com",pos)
                if last == "/*": # comment
                    return (False,"com2",pos)
                self.push_token("operator", last)
                return (False, "init", pos)
            else:
                print(f"LexError: syntax error around operator")
                self.mark_pos()
                quit()

        def action_operator_end(line,linenum,state,start,pos):
            value = line[start:pos]
            res = check_operator(value, -1) # -1 as as sentinel/dummy
            if res == "last":
                if value == "//": # comment
                    return (False,"com",pos)
                if value == "/*": # comment
                    return (False,"com2",pos)
                self.push_token("operator", value)
                return (False,"init", pos)
            else:
                print(f"LexError: syntax error around operator")
                self.mark_start()
                quit()

        # numbers:
        def action_digit(line,linenum,state,start,pos):
            return (True, "num", start)
        def action_num(line,linenum,state,start,pos):
            return (True, "num", start)
        def action_num_end(line,linenum,state,start,pos):
            value = line[start:pos]
            
            # check validity of number
            parts = value.split(".")
            if len(parts) > 2:
                print(f"LexError: syntax error around number '{value}'")
                l.mark_start()
                quit()

            self.push_token("num", value)
            return (False,"init", pos)

        # strings:
        #    for now only on one line
        def action_string(line,linenum,state,start,pos):
            return (True, "str", start)
        def action_string_escape(line,linenum,state,start,pos):
            return (True, "str_esc", start)
        def action_string_escape_h1(line,linenum,state,start,pos):
            return (True, "str_esc_h1", start)
        def action_string_escape_h2(line,linenum,state,start,pos):
            return (True, "str_esc_h2", start)
        def action_string_end(line,linenum,state,start,pos):
            value = line[start+1:pos]
            
            # check string for escape sequences:
            res = []
            state = None
            xval = ""
            for c in value:
                if state is None:
                    if c != "\\":
                        res.append(c)
                    else:
                        state = "esc"
                elif state == "esc":
                    d = {"n":"\n", "t":"\t", "\'":"\'", "\"": "\"","\\":"\\"}
                    if c in d:
                        res.append(d[c])
                        state = None
                    elif c == "x":
                        state = "h1"
                        xval = ""
                    else:
                        print(c, ord(c), value)
                        assert(False)
                elif state == "h1": # for \x
                    xval = c
                    state = "h2"
                elif state == "h2": # for \x
                    xval += c
                    state = None
                    res.append(chr( int(xval, 16) ))
            
            # join the character array back together
            value = "".join(res)

            self.push_token("str", value)
            return (True,"init", pos+1)
        
        # comment:
        #   goes from double-slash // all the way to end of line
        def action_comment(line,linenum,state,start,pos):
            return (True, "com", pos)
        def action_comment_end(line,linenum,state,start,pos):
            return (True, "init", pos)

        # multiline comment:
        #   goes from /* ... */
        def action_comment2(line,linenum,state,start,pos):
            return (True, "com2", pos)
        def action_comment2_star(line,linenum,state,start,pos):
            return (True, "com2_s", pos)
        def action_comment2_end(line,linenum,state,start,pos):
            return (True, "init", pos)
        
        # preprocessor:
        def action_preprocess(line,linenum,state,start,pos):
            return (True, "pre", pos)
        def action_preprocess_end(line,linenum,state,start,pos):
            preprocessor_exec(line,linenum)
            return (True, "init", pos)
        
        def preprocessor_exec(line,linenum):
            # strip beginning including first #
            i = line.find("#")+1
            strip = line[i:-1]
            
            # extract command + rest
            j = strip.find(" ")
            cmd = strip[:j].upper()
            rest = strip[j+1:]

            if cmd == "ECHO":
                print("PreprocessorEcho",end=" ")
                self.mark_line(linenum)
            elif cmd == "IMPORT":
                anchor_token = Token(self,"anchor","anchor",linenum,i,self.anchor_token)
                sublex = BasicLexer(self,anchor_token)
                
                filename = rest.strip()
                isLib = False
                if filename.startswith("\"") and filename.endswith("\""):
                    filename = filename[1:-1]
                elif filename.startswith("<") and filename.endswith(">"):
                    filename = filename[1:-1]
                    isLib = True
                    assert(False and "library not implemented yet")
                else:
                    print(f"LexError: import expects \"path\" or <library>, got '{filename}'.")
                    self.mark_line(linenum)
                    quit()

                ddir, _ = os.path.split(self.filename)
                fname = os.path.join(ddir, filename)
                
                try:
                    with open(fname,"r") as f:
                        seq = f.read()
                except:
                    print(f"LexError: import file not found.")
                    self.mark_line(linenum)
                    quit()
                
                tokens = sublex.lex(seq,fname)
                self.tokens += tokens

            elif cmd == "DEFINE":
                self.mark_line(linenum)
                assert(False and "not implemented")
            elif cmd == "UNDEFINE":
                self.mark_line(linenum)
                assert(False and "not implemented")
            elif cmd == "IFDEF":
                self.mark_line(linenum)
                assert(False and "not implemented")
            elif cmd == "ENDIF":
                self.mark_line(linenum)
                assert(False and "not implemented")
            else:
                print(f"PreprocessorError: unknown command {cmd}.")
                self.mark_line(linenum)
                quit()

        self.set_rules([
            # whitespaces:
            ("init", cs.whitespace(),                         action_whitespace),
            
            # operators
            ("init", operator_char,                           action_operator),
            ("oper", operator_char,                           action_operator),
            ("oper", [-1],                                    action_operator_end),
            
            # names:
            ("init", cs.letter() + [ord("_")],                action_name),
            ("name", cs.letter() + cs.digit() + [ord("_")],   action_name),
            ("name", [-1],                                    action_name_end),
            
            # separators:
            ("init", [ord(";")],                              action_semicolon),
            ("init", [ord(",")],                              action_comma),
            
            # numbers
            ("init", cs.digit(),                              action_digit),
            ("num",  cs.digit() + [ord(".")],                 action_num),
            ("num",  [-1],                                    action_num_end),
            
            # brackets
            ("init", cs.bracket(),                            action_bracket),
            
            # strings:
            ("init", [ord("\"")],                             action_string),
            ("str",  [ord("\\")],                             action_string_escape),
            ("str",  [ord("\"")],                             action_string_end),
            ("str",  cs.minus(cs.legible(), [ord("\""), ord("\\")]),    action_string),
            ("str_esc",    [ord(c) for c in "\"\'nt\\"],                action_string),
            ("str_esc",    [ord("x")],                                  action_string_escape_h1),
            ("str_esc_h1", cs.hex(),                                    action_string_escape_h2),
            ("str_esc_h2", cs.hex(),                                    action_string),
            
            # preprocessor:
            ("init", [ord("#")],                             action_preprocess),
            ("pre",  cs.minus(cs.all(), [ord("\n")]),        action_preprocess),
            ("pre",  [ord("\n")],                            action_preprocess_end),
            # comment:
            ("com",  cs.minus(cs.all(), [ord("\n")]),        action_comment),
            ("com",  [ord("\n")],                            action_comment_end),
            
            # multiline comment
            ("com2",  cs.minus(cs.all(), [ord("*")]),        action_comment2),
            ("com2",  [ord("*")],                            action_comment2_star),
            ("com2_s",[ord("*")],                            action_comment2_star),
            ("com2_s",[ord("/")],                            action_comment2_end),
            ("com2_s",cs.minus(cs.all(), [ord("/"),ord("*")]),        action_comment2),
            ])


def main(argv):
    l = BasicLexer()
    
    if len(argv) > 0:
        filename = argv[0]
        with open(filename, "r") as f:
            seq = f.read()
    else:
        filename = "test.script"
        seq = ("var int x;\n"
               ";;;\n"
               ";\n\n"
               "x = 5.346234;\n"
               "print(x);\n"
               "\n"
               "function x(int a, int b, int c) {\n"
               "   return a+b+c;\n"
               "};\n"
               "x = a << b;\n"
               "a++;\n"
               "x = a * b + c / d + x(abc->xyz) + *yi;\n"
               "a = a-- + x ^ z ||& ~!u;\n"
               "x = \"hello world\";\n"
               "y = \"asdf \\n \\\" \\\\ asdff\";\n"
               "z = \" hello \\x41 \\x3B \\\" \\n \";\n"
               "h=x # asdfasdfasdf asdfasdf\n"
               "h=x# # # \\n; hello\n"
               "end\n"
               )
    
    tokens = l.lex(seq, filename)
    print([str(t) for t in tokens])

if __name__ == "__main__":
    main(sys.argv[1:])

