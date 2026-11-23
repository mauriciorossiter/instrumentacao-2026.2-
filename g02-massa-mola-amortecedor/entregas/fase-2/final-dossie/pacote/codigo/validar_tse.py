# -*- coding: utf-8 -*-
"""Validador estrutural do .tse gerado: terminais de cada conexao existem e toda entrada esta ligada."""
import re, sys
TERM = {
 "core/Signal Controlled Voltage Source": {"in", "p_node", "n_node"},
 "core/Inductor": {"p_node", "n_node"}, "core/Resistor": {"p_node", "n_node"}, "core/Capacitor": {"p_node", "n_node"},
 "core/Current Measurement": {"p_node", "n_node", "out"}, "core/Voltage Measurement": {"p_node", "n_node", "out"},
 "core/Ground": {"node"}, "core/Probe": {"in"}, "core/SCADA Input": {"out"}, "core/Gain": {"in", "out"},
 "core/Scope": set(),
}
txt = open(sys.argv[1], encoding="utf-8").read()
comps = {}
for m in re.finditer(r'component "([^"]+)" ("[^"]+"|\S+) \{(.*?)\n        \}', txt, re.S):
    tipo, nome, body = m.group(1), m.group(2).strip('"'), m.group(3)
    body = body + chr(10)
    if tipo == "core/C function":
        ins = re.search(r'input_terminals = "([^"]*)"', body).group(1)
        outs = re.search(r'output_terminals = "([^"]*)"', body).group(1)
        ti = set(re.findall(r"real (\w+);", ins)); to = set(re.findall(r"real (\w+);", outs))
        comps[nome] = (tipo, ti | to, ti)
        for f in ("output_fnc", "update_fnc", "init_fnc", "arb_defs"):
            code = re.search(f + r' = "(.*?)(?<!\\)"\n', body, re.S).group(1)
            if code.count("{") != code.count("}") or code.count("(") != code.count(")"):
                print("CHAVES/PARENTESES DESBALANCEADOS", nome, f)
    else:
        comps[nome] = (tipo, TERM[tipo], {"in"} if tipo in ("core/Probe", "core/Gain") else
                       ({"in"} if tipo == "core/Signal Controlled Voltage Source" else set()))
junc = set(re.findall(r"junction (\S+) (?:sp|pe)", txt))
usados = {}
erros = 0
for a, b in re.findall(r"connect (\"[^\"]+\"|\S+) (\"[^\"]+\"|\S+) as", txt):
    for t in (a.strip('"'), b.strip('"')):
        if t in junc:
            continue
        c, term = t.rsplit(".", 1)
        if c not in comps:
            print("componente inexistente", t); erros += 1; continue
        if term not in comps[c][1]:
            print("terminal inexistente", t); erros += 1
        usados.setdefault(c, set()).add(term)
for c, (tipo, tt, ins) in comps.items():
    falta = ins - usados.get(c, set())
    if falta:
        print("entrada sem ligacao:", c, falta); erros += 1
print(sys.argv[1].split("/")[-2], len(comps), "componentes,", len(junc), "juncoes,", erros, "erros")
