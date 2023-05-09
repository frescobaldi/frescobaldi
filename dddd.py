import ly.lex
txt = r"a!6 ( bf'16)"
s = ly.lex.state("lilypond")

for t in s.tokens(txt):
    print(t, t.__class__.__name__)

"""
\relative c'{
    c c c c
}
"""