"""Brace / environment balance of out/notes.tex (no LaTeX compiler on this machine)."""
import re
s = open("out/notes.tex", encoding="utf-8").read()
b = re.findall(r"\\begin\{(\w+\*?)\}", s)
e = re.findall(r"\\end\{(\w+\*?)\}", s)
print("braces:", s.count("{") - s.count("}"), "| begin:", len(b), "end:", len(e), "| unmatched:", sorted(set(b) ^ set(e)), "| \\pend left:", s.count("\\pend"))
