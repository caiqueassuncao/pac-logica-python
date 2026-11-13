import random
from .config import VARIABLES, OPS

def formula_var(v): return ("var", v)
def formula_not(a): return ("not", a)
def formula_bin(op, a, b): return ("bin", op, a, b)

def formula_str(node, top=False):
    if node[0] == "var":
        return node[1]
    if node[0] == "not":
        return "¬" + formula_str(node[1])
    s = formula_str(node[2]) + " " + node[1] + " " + formula_str(node[3])
    return s if top else "(" + s + ")"

def evaluate(node, env):
    if node[0] == "var": return env[node[1]]
    if node[0] == "not": return not evaluate(node[1], env)
    a, b = evaluate(node[2], env), evaluate(node[3], env)
    op = node[1]
    if op == "∧": return a and b
    if op == "∨": return a or b
    if op == "→": return (not a) or b
    return a == b

def used_vars(node):
    if node[0] == "var": return {node[1]}
    if node[0] == "not": return used_vars(node[1])
    return used_vars(node[2]) | used_vars(node[3])

def truth_rows(vars_):
    return [dict(zip(vars_, [not bool((i >> (len(vars_)-1-j)) & 1) for j in range(len(vars_))]))
            for i in range(1 << len(vars_))]

def signature(node, vars_):
    return "".join("1" if evaluate(node, row) else "0" for row in truth_rows(vars_))

def classify_signature(sig):
    if "0" not in sig: return 0
    if "1" not in sig: return 2
    return 1

def gen_formula(depth, vars_, top=True):
    if depth == 0 or (not top and random.random() < .25):
        return formula_var(random.choice(vars_))
    op = random.choice(["¬", "¬", "∧", "∨", "→", "↔", "∧", "∨", "→"])
    if top and op == "¬" and depth < 2:
        op = random.choice(OPS)
    if op == "¬":
        return formula_not(gen_formula(depth-1, vars_, top))
    a = gen_formula(depth-1, vars_, False)
    b = gen_formula(depth-1, vars_, False)
    return formula_bin(op, a, b)

TEMPLATES = {
    0: lambda p,q: [
        formula_bin("∨", formula_var(p), formula_not(formula_var(p))),
        formula_bin("→", formula_var(p), formula_var(p)),
        formula_bin("→", formula_bin("∧", formula_var(p), formula_var(q)), formula_var(p)),
        formula_bin("→", formula_var(p), formula_bin("∨", formula_var(p), formula_var(q))),
        formula_not(formula_bin("∧", formula_var(p), formula_not(formula_var(p)))),
    ],
    2: lambda p,q: [
        formula_bin("∧", formula_var(p), formula_not(formula_var(p))),
        formula_not(formula_bin("∨", formula_var(p), formula_not(formula_var(p)))),
        formula_bin("↔", formula_var(p), formula_not(formula_var(p))),
        formula_not(formula_bin("→", formula_var(p), formula_var(p))),
    ]
}

def make_class_question():
    target = random.randrange(3)
    p, q = VARIABLES[:]
    if random.random() < .5: p, q = q, p
    if target != 1 and random.random() < .6:
        ast = random.choice(TEMPLATES[target](p, q))
    else:
        ast = None
        for _ in range(3000):
            candidate = gen_formula(random.choice([1,2,2]), VARIABLES)
            vs = sorted(used_vars(candidate))
            if len(vs) >= 2 and len(formula_str(candidate, True)) <= 13 and classify_signature(signature(candidate, vs)) == target:
                ast = candidate
                break
        if ast is None: ast = random.choice(TEMPLATES[target](p, q))
    vs = sorted(used_vars(ast))
    return {"type":"class", "formula":formula_str(ast, True), "ast":ast, "vars":vs, "answer":target}

def make_equiv_question():
    pool = {}
    for _ in range(800):
        ast = gen_formula(random.choice([1,2,2]), VARIABLES)
        sig = signature(ast, VARIABLES)
        if sig in ("0000", "1111") or len(used_vars(ast)) < 2 or len(formula_str(ast, True)) > 12:
            continue
        pool.setdefault(sig, set()).add(formula_str(ast, True))
    groups = [k for k,v in pool.items() if len(v) > 1]
    if not groups: return make_class_question()
    sig = random.choice(groups)
    formulas = list(pool[sig]); random.shuffle(formulas)
    correct = formulas[1]
    wrong_groups = [k for k in pool if k != sig]
    wrong_groups.sort(key=lambda k: sum(a != b for a,b in zip(k,sig)) + random.random()*1.5)
    wrong = [random.choice(list(pool[k])) for k in wrong_groups[:3]]
    options = [correct] + wrong
    random.shuffle(options)
    return {"type":"equiv", "formula":formulas[0], "options":options, "answer":options.index(correct), "sig":sig}

def make_question():
    return make_class_question() if random.random() < .5 else make_equiv_question()

