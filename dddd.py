from ly.lex import Token
from ly.lex.lilypond import Note, Rest, Skip, ChordStart
import ly.document
import ly.rhythm

txt = r"a!6 ( bf'16)"
s = ly.lex.state("lilypond")

# for t in s.tokens(txt):
#     print(t, t.__class__.__name__)

txt = r"\relative{<c d>8 c[ d4 e] f\)]}"
selection = (27, len(txt))
selection = (10, len(txt))
select = True


def nextMusicToken(doc, pos):
    cursor = ly.document.Cursor(doc, pos)
    source = ly.document.Source(cursor, True, ly.document.INSIDE, True)

    for token in source:
        if token.pos >= pos:
            if isinstance(token, Note) or isinstance(token, Rest) \
                    or isinstance(token, Skip) or isinstance(token, ChordStart):
                return token.pos, token.end


def hasSelection():
    return select


def search_spanners(item1, item2):
    last = None
    for span in positions:
        if span[1] < item2[0] and span[0] >= item1[1]:
            last = span[1]

    return last


def get_spanners_positions(doc, pos, max_offset=1e5):
    from ly.lex.lilypond import BeamStart, BeamEnd, SlurStart, SlurEnd, PhrasingSlurStart, PhrasingSlurEnd
    cursor = ly.document.Cursor(doc, pos)
    source = ly.document.Source(cursor, True, ly.document.INSIDE, True)

    positions = []
    for token in source:
        if token.pos >= max_offset:
            break
        if isinstance(token, BeamStart) or isinstance(token, BeamEnd) \
                or isinstance(token, SlurStart) or isinstance(token, SlurEnd) \
                or isinstance(token, PhrasingSlurStart) or isinstance(token, PhrasingSlurEnd):
            positions.append((token.pos, token.end))
    return positions


doc = ly.document.Document(txt)
crs = ly.document.Cursor(doc, selection[0], selection[1])
source = ly.document.Source(crs, True, ly.document.PARTIAL, True)

if hasSelection():
    partial = ly.document.INSIDE
else:
    # just select until the end of the current line
    crs.select_end_of_block()
    partial = ly.document.OUTSIDE

items = list(map(lambda it: (it.pos, it.end), ly.rhythm.music_items(crs, partial=partial)))

if len(items) == 1:
    raise Exception("jjjj")

if hasSelection():
    tk = nextMusicToken(doc, items[-1][1])
    items.append(tk if tk else (crs.end, crs.end))
    crs.select_end_of_block()

else:
    del items[3:]
    if len(items) < 3:
        items.append((crs.end, crs.end))

for item in items:
    print(item)

positions = get_spanners_positions(doc, items[0][1], items[-1][0])
print(positions)

a = search_spanners(items[0], items[1])
b = search_spanners(items[-2], items[-1])

if not a:
    a = items[0][1]

if not b:
    b = items[1][1]
# for span in positions:
#     if span[1] < items[1].pos and span[0] >= items[0].end:
#         a = span[1]
#
# for span in positions:
#     if span[1] < items[2].pos and span[0] >= items[1].end:
#         b = span[1]

print(a, b)
print(txt[:a] + "§" + txt[a:b] + "§" + txt[b:])
