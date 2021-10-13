import pyparsing as pyp
import math
import operator
import datetime


class NumericStringParser(object):
    '''
    Most of this code comes from the fourFn.py pyparsing example
    http://pyparsing.wikispaces.com/file/view/fourFn.py
    http://pyparsing.wikispaces.com/message/view/home/15549426
    __author__='Paul McGuire'

    All I've done is rewrap Paul McGuire's fourFn.py as a class, so I can use it
    more easily in other places.
    '''


    def __init__(self, dict_var={}):
        self.dict_var = dict_var
        """
        expop   :: '^'
        multop  :: '*' | '/'
        addop   :: '+' | '-'
        integer :: ['+' | '-'] '0'..'9'+
        atom    :: PI | E | real | fn '(' expr ')' | '(' expr ')'
        factor  :: atom [ expop factor ]*
        term    :: factor [ multop factor ]*
        expr    :: term [ addop term ]*
        """
        point = pyp.Literal( "." )
        e     = pyp.CaselessLiteral( "E" )
        fnumber = pyp.Combine( 
                                pyp.Word( "+-" + pyp.nums, pyp.nums ) + 
                                pyp.Optional( point + pyp.Optional( pyp.Word( pyp.nums ) ) ) +
                                pyp.Optional( e + pyp.Word( "+-" + pyp.nums, pyp.nums ) )
                            )
        ident = pyp.Word(pyp.alphas, pyp.alphas + pyp.nums + "_$")       
        plus  = pyp.Literal( "+" )
        minus = pyp.Literal( "-" )
        mult  = pyp.Literal( "*" )
        div   = pyp.Literal( "/" )
        pow_   = pyp.Literal( "^" )
        lshift = pyp.Literal( "<<" )
        rshift = pyp.Literal( ">>" )

        # not_   = pyp.Literal( "not" )
        and_   = pyp.Literal( "and" )
        or_   = pyp.Literal( "or" )
        xor_   = pyp.Literal( "xor" )

        eq   = pyp.Literal( "==" )
        neq  = pyp.Literal( "!=" )
        gt   = pyp.Literal( ">" )
        ge   = pyp.Literal( ">=" )
        lt   = pyp.Literal( "<" )
        le   = pyp.Literal( "<=" )
        

        lpar  = pyp.Literal( "(" ).suppress()
        rpar  = pyp.Literal( ")" ).suppress()
        addop  = plus | minus | and_ | or_ | xor_
        multop = mult | div | lshift | rshift
        equop = eq | neq | ge | gt | le | lt 
        expop = pow_ # | not_

        pi    = pyp.CaselessLiteral( "PI" )
        variables = pyp.Word("$", pyp.alphanums + '.' + '_')
        expr = pyp.Forward()
        equation = pyp.Forward()
        atom = (
                    (
                        pyp.Optional(pyp.oneOf("- +")) +
                        (pi | e | fnumber | ident + lpar + expr + rpar | variables).setParseAction(self.pushFirst)
                    ) | 
                    pyp.Optional(pyp.oneOf("- +")) +
                    pyp.Group(lpar + expr + rpar)
                ).setParseAction(self.pushUMinus)       
        # by defining exponentiation as "atom [ ^ factor ]..." instead of 
        # "atom [ ^ atom ]...", we get right-to-left exponents, instead of left-to-right
        # that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        factor = pyp.Forward()
        factor      <<  atom    +    pyp.ZeroOrMore( ( expop    +   factor  ).setParseAction( self.pushFirst ) )
        term        =   factor  +    pyp.ZeroOrMore( ( multop   +   factor  ).setParseAction( self.pushFirst ) )
        expr        <<  term    +    pyp.ZeroOrMore( ( addop    +   term    ).setParseAction( self.pushFirst ) )
        equation    <<  expr    +    pyp.ZeroOrMore( ( equop    +   expr    ).setParseAction( self.pushFirst ) )
        self.bnf = equation
        # map operator symbols to corresponding arithmetic operations
        epsilon = 1e-12
        self.opn = {    
            "+" : operator.add,
            "-" : operator.sub,
            "*" : operator.mul,
            "/" : operator.truediv,
            "^" : operator.pow,
            "<<" : operator.lshift,
            ">>" : operator.rshift
        }

        self.equality_opn = {
            "==" : operator.eq,
            "!=" : operator.ne,
            ">=" : operator.ge,
            ">" : operator.gt,
            "<=" : operator.le,
            "<" : operator.lt
        }

        self.logical_opn = {
            "and" : operator.and_,
            "or" : operator.or_,
            "not" : operator.not_,
            "xor" : operator.xor,
        }
        
        self.fn  = {    
            "sin" : math.sin,
            "cos" : math.cos,
            "tan" : math.tan,
            "acos" : math.acos,
            "asin" : math.asin,
            "atan" : math.atan,
            "sqrt" : math.sqrt,
            "abs" : abs,
            "trunc" : lambda a: int(a),
            "round" : round,
            "exp" : math.exp,
            "log" : math.log,
            "log2" : math.log2,
            "Log" : math.log10,
            "not" : operator.not_,
            # For Python3 compatibility, cmp replaced by ((a > 0) - (a < 0)). See
            # https://docs.python.org/3.0/whatsnew/3.0.html#ordering-comparisons
            "sgn" : lambda a: abs(a) > epsilon and ((a > 0) - (a < 0)) or 0
        }
        self.exprStack = []
        

    def pushFirst(self, strg, loc, toks ):
        self.exprStack.append( toks[0] )


    def pushUMinus(self, strg, loc, toks ):
        if toks and toks[0] == '-':
            self.exprStack.append( 'unary -' )

        
    def evaluateStack(self, s ):
        op = s.pop()
        if op == 'unary -':
            op1 = self.evaluateStack(s)
            if op1 is None:
                return None
            return 0. - op1

        elif op == 'not':
            op1 = self.evaluateStack(s)
            if op1 is None:
                return None
            return int(self.logical_opn[op]( int(op1)))

        elif op in ['>>', '<<']:
            op2 = self.evaluateStack( s )
            op1 = self.evaluateStack( s )
            if op1 is None or op2 is None:
                return None
            return self.opn[op]( int(op1), int(op2) )

        elif op in list(self.opn.keys()):
            op2 = self.evaluateStack( s )
            op1 = self.evaluateStack( s )
            if op1 is None or op2 is None:
                return None
            return self.opn[op]( op1, op2 )
        
        elif op in list(self.logical_opn.keys()):
            op2 = self.evaluateStack( s )
            op1 = self.evaluateStack( s )
            if op1 is None or op2 is None:
                return None
            return self.logical_opn[op]( int(op1), int(op2) )

        elif op in list(self.equality_opn.keys()):
            op2 = self.evaluateStack( s )
            op1 = self.evaluateStack( s )
            if op1 is None or op2 is None:
                return None
            return int(self.equality_opn[op]( op1, op2 ))

        elif op == "PI":
            return math.pi # 3.1415926535

        elif op.startswith('$'): # custom variables
            op = op[1:]
            split_op = op.split('.')
            key = split_op[0] 
            property_name = split_op[1] if len(split_op) > 1 else None

            if property_name is None:
                value = self.dict_var[key]
            else:
                value = getattr(self.dict_var[key], property_name)
            
            if isinstance(value, datetime.datetime):
                value = (value - datetime.datetime(1970,1,1)).total_seconds()
            
            return value

        elif op == "E":
            return math.e  # 2.718281828

        elif op in self.fn:
            op1 =  self.evaluateStack(s)
            if op1 is None:
                return None
            return self.fn[op](op1)

        elif op[0].isalpha():
            return 0
        else:
            return float(op)
        
        
    def eval(self, num_string, parseAll = True):
        self.exprStack = []
        results = self.bnf.parseString(num_string, parseAll)
        val = self.evaluateStack( self.exprStack[:] )
        return val



if __name__ == "__main__":
    

    dict_var = {"A": 10, "B": 100}
    nsp = NumericStringParser(dict_var)
    print(nsp.eval('$A+$B / 3 '))

    import dataclasses
    @dataclasses.dataclass
    class TestClass:
        name: str
        value_A: float
        valueB: int = 0

    dict_var = {"A_A": TestClass('nameA', 10.01), "B_B": TestClass('nameB', 100 , 10)}
    nsp = NumericStringParser(dict_var)
    print(nsp.eval('$A_A.value_A * $A_A.valueB + $B_B.value_A * $B_B.valueB / 3 '))

    # @dataclasses.dataclass
    class TestClass2:
        def __init__(self, name, value):
            self.name = name
            self.value = value
        
        @property
        def value2(self):
            return self.value * self.value

    expression = """ 0.5 * $A.value * ( 0.25 * $C.value * $D.value - ( $D.value - 2 * $E.value ) * sqrt( 100 + $E.value * $D.value - $E.value^ 2)  ) """

    expression = """ $A.value2 """

    dict_var = {}
    dict_var["A"] = TestClass2('nameA', 10.0)
    dict_var["B"] = TestClass2('nameB', 2.0)
    dict_var["C"] = TestClass2('nameC', 4.0)
    dict_var["D"] = TestClass2('nameD', 3.0)
    dict_var["E"] = TestClass2('nameE', 5.0)

    nsp = NumericStringParser(dict_var)
    print(nsp.eval(expression))


    expressions = []
    expressions.append('1 or 0')
    expressions.append('1 or 1')
    expressions.append('0 or 1')
    expressions.append('0 or 0')
    expressions.append('1 and 0')
    expressions.append('1 and 1')
    expressions.append('0 and 1')
    expressions.append('0 and 0')
    expressions.append('1 xor 0')
    expressions.append('1 xor 1')
    expressions.append('0 xor 1')
    expressions.append('0 xor 0')
    expressions.append('1 or not(0)')
    expressions.append('1 or not(1)')
    expressions.append('0 or not(1)')
    expressions.append('0 or not(0)')
    expressions.append('1 and not(0)')
    expressions.append('1 and not(1)')
    expressions.append('0 and not(1)')
    expressions.append('0 and not(0)')
    expressions.append('1 xor not(0)')
    expressions.append('1 xor not(1)')
    expressions.append('0 xor not(1)')
    expressions.append('not(0)*3.5')
    expressions.append('not(1)*3.5')

    expressions.append('5 - 3 > 5 - 3')
    expressions.append('5 - 3 < 5 - 3')
    expressions.append('5 - 3 == 5 - 3')
    expressions.append('5 - 3 != 5 - 3')
    expressions.append('5 - 3 <= 5 - 3')
    expressions.append('5 - 3 >= 5 - 3')

    expressions.append('(1 and (1 or 0)) == (1 or not(1))')
    
    expressions.append('2 >> 10')
    expressions.append('1 << 10')

    nsp = NumericStringParser(dict_var)
    for e in expressions:
        try:
            answer = int(eval(e))
        except:
            answer = None
        print(f'{e} = {nsp.eval(e)} (Correct answer: {answer})')
