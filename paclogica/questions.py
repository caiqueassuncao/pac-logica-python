"""Banco de questões por tópico. Cada questão é um dicionário com:

prompt       texto acima do quadro
lines        conteúdo do quadro: lista de (texto, estilo), estilo em big|text|accent|muted
options      alternativas
answer       índice da alternativa correta
explanation  explicação mostrada depois da resposta
table        opcional: (cabeçalhos, linhas de booleanos, nº de colunas de entrada)
"""
import random
from .logic import (formula_var as V, formula_not as N, formula_bin as B,
                    formula_str, evaluate, truth_rows, make_class_question, make_equiv_question)

TOPIC_NAMES = {
    "conectivos": "Regras dos conectivos",
    "frases": "Frase → fórmula",
    "argumentos": "Silogismo ou sofisma",
    "tabelas": "Tabela-verdade",
}

P, Q = V("p"), V("q")

def shuffled(correct, wrong):
    options = [correct] + list(wrong)
    random.shuffle(options)
    return options, options.index(correct)

def connective_table(op):
    if op == "¬":
        return ["p", "¬p"], [[r["p"], not r["p"]] for r in truth_rows(["p"])], 1
    ast = B(op, P, Q)
    return (["p", "q", formula_str(ast, True)],
            [[r["p"], r["q"], evaluate(ast, r)] for r in truth_rows(["p", "q"])], 2)

# 1. Regras dos conectivos: (conectivo, enunciado, correta, erradas, explicação)
RULES = [
    ("∧", "A conjunção p ∧ q é verdadeira quando:", "p e q são ambas verdadeiras",
     ["pelo menos uma delas é verdadeira", "p e q são ambas falsas"],
     "Na conjunção (“e”), as duas partes precisam ser verdadeiras."),
    ("∧", "A conjunção p ∧ q é falsa quando:", "pelo menos uma delas é falsa",
     ["somente quando as duas são falsas", "p e q são ambas verdadeiras"],
     "Na conjunção (“e”), basta uma parte falsa para tudo ser falso."),
    ("∨", "A disjunção p ∨ q é verdadeira quando:", "pelo menos uma delas é verdadeira",
     ["somente quando as duas são verdadeiras", "p e q são ambas falsas"],
     "Na disjunção (“ou”), basta uma parte verdadeira."),
    ("∨", "A disjunção p ∨ q é falsa quando:", "p e q são ambas falsas",
     ["pelo menos uma delas é falsa", "p e q são ambas verdadeiras"],
     "A disjunção (“ou”) só é falsa quando as duas partes são falsas."),
    ("→", "O condicional p → q é falso quando:", "p é verdadeira e q é falsa",
     ["p é falsa e q é verdadeira", "p e q são ambas falsas"],
     "O condicional só é falso no caso V → F: a promessa foi quebrada."),
    ("→", "O condicional p → q é verdadeiro quando:", "p é falsa ou q é verdadeira",
     ["somente quando p e q são verdadeiras", "p é verdadeira e q é falsa"],
     "O condicional é verdadeiro em todos os casos, menos em V → F."),
    ("↔", "O bicondicional p ↔ q é verdadeiro quando:", "p e q têm o mesmo valor lógico",
     ["p e q têm valores lógicos diferentes", "somente quando p e q são verdadeiras"],
     "O bicondicional (“se e somente se”) é verdadeiro quando os lados são iguais: V e V, ou F e F."),
    ("↔", "O bicondicional p ↔ q é falso quando:", "p e q têm valores lógicos diferentes",
     ["p e q são ambas falsas", "p e q são ambas verdadeiras"],
     "O bicondicional é falso quando um lado é V e o outro é F."),
    ("¬", "A negação ¬p é verdadeira quando:", "p é falsa",
     ["p é verdadeira", "sempre, qualquer que seja p"],
     "A negação inverte o valor: ¬V = F e ¬F = V."),
]

def make_rule_question():
    op, statement, correct, wrong, explanation = random.choice(RULES)
    options, answer = shuffled(correct, wrong)
    return {"prompt": "Complete a regra:", "lines": [(statement, "text")],
            "options": options, "answer": answer, "explanation": explanation,
            "table": connective_table(op)}

def make_value_question():
    """Valores dados para p e q: exatamente uma das três proposições é verdadeira (ou falsa)."""
    while True:
        env = {"p": random.random() < .5, "q": random.random() < .5}
        asts = [B(op, P, Q) for op in random.sample(["∧", "∨", "→", "↔"], 3)]
        values = [evaluate(a, env) for a in asts]
        for wanted in random.sample([True, False], 2):
            if values.count(wanted) == 1:
                labels = [formula_str(a, True) for a in asts]
                word = "verdadeira" if wanted else "falsa"
                tf = lambda b: "V" if b else "F"
                return {
                    "prompt": f"Qual proposição é {word}?",
                    "lines": [(f"p = {tf(env['p'])},  q = {tf(env['q'])}", "big")],
                    "options": labels, "answer": values.index(wanted),
                    "explanation": " · ".join(f"{l} = {tf(v)}" for l, v in zip(labels, values)),
                    "table": (["p", "q"] + labels, [[env["p"], env["q"]] + values], 2),
                }

# 2. Silogismo ou sofisma: (premissa 1, premissa 2, conclusão, válido?, explicação)
ARGUMENTS = [
    ("Todo mamífero é animal.", "Todo gato é mamífero.", "Logo, todo gato é animal.", True,
     "Silogismo: se todo gato está entre os mamíferos e todo mamífero está entre os animais, todo gato é animal."),
    ("Nenhum peixe é mamífero.", "Todo tubarão é peixe.", "Logo, nenhum tubarão é mamífero.", True,
     "Silogismo: os tubarões estão dentro do grupo dos peixes, que não tem mamíferos."),
    ("Se chove, a rua fica molhada.", "Choveu.", "Logo, a rua está molhada.", True,
     "Válido (modus ponens): de p → q e p, conclui-se q."),
    ("Se Ana estuda, ela passa na prova.", "Ana não passou na prova.", "Logo, Ana não estudou.", True,
     "Válido (modus tollens): de p → q e ¬q, conclui-se ¬p."),
    ("Ou vou ao cinema ou vou ao teatro.", "Não fui ao cinema.", "Logo, fui ao teatro.", True,
     "Válido (silogismo disjuntivo): de p ∨ q e ¬p, conclui-se q."),
    ("Se acordo cedo, tomo café.", "Se tomo café, fico disposto.", "Logo, se acordo cedo, fico disposto.", True,
     "Válido (silogismo hipotético): de p → q e q → r, conclui-se p → r."),
    ("Se chove, a rua fica molhada.", "A rua está molhada.", "Logo, choveu.", False,
     "Sofisma (afirmar o consequente): a rua pode estar molhada por outro motivo."),
    ("Se Ana estuda, ela passa na prova.", "Ana não estudou.", "Logo, Ana não passou.", False,
     "Sofisma (negar o antecedente): Ana pode passar mesmo sem estudar."),
    ("Todo gato é mamífero.", "Todo cachorro é mamífero.", "Logo, todo gato é cachorro.", False,
     "Sofisma: ser mamífero em comum não faz de um gato um cachorro."),
    ("Todo médico usa jaleco.", "João usa jaleco.", "Logo, João é médico.", False,
     "Sofisma: outras pessoas também usam jaleco (dentistas, cientistas...)."),
    ("Alguns alunos são atletas.", "Alguns atletas são músicos.", "Logo, alguns alunos são músicos.", False,
     "Sofisma: os atletas que são alunos podem não ser os mesmos que são músicos."),
    ("Se é cachorro, então é animal.", "Rex não é cachorro.", "Logo, Rex não é animal.", False,
     "Sofisma (negar o antecedente): Rex pode ser um gato, que também é animal."),
]
ARGUMENT_OPTIONS = ["Silogismo (válido)", "Sofisma (inválido)"]

def make_argument_question():
    p1, p2, conclusion, valid, explanation = random.choice(ARGUMENTS)
    return {
        "prompt": "Este argumento é um silogismo ou um sofisma?",
        "lines": [(f"Premissa 1: {p1}", "text"), (f"Premissa 2: {p2}", "text"), (conclusion, "accent")],
        "options": ARGUMENT_OPTIONS[:], "answer": 0 if valid else 1, "explanation": explanation,
    }

# 3. Frase → fórmula: frases com p e q (forma afirmativa e negativa)
CONTEXTS = [
    ("está chovendo", "não está chovendo", "eu levo guarda-chuva", "eu não levo guarda-chuva"),
    ("Ana estuda", "Ana não estuda", "Ana passa na prova", "Ana não passa na prova"),
    ("o alarme toca", "o alarme não toca", "eu acordo", "eu não acordo"),
    ("faz sol", "não faz sol", "vamos à praia", "não vamos à praia"),
    ("Pedro treina", "Pedro não treina", "Pedro fica em forma", "Pedro não fica em forma"),
    ("a loja está aberta", "a loja não está aberta", "eu compro pão", "eu não compro pão"),
]
# (modelo da frase, fórmula correta, alternativas erradas, explicação)
PATTERNS = [
    ("{p} e {q}.", B("∧", P, Q), [B("∨", P, Q), B("→", P, Q), B("↔", P, Q)],
     "“e” indica conjunção (∧)."),
    ("{p} ou {q}.", B("∨", P, Q), [B("∧", P, Q), B("→", P, Q), B("↔", P, Q)],
     "“ou” indica disjunção (∨)."),
    ("Se {p}, então {q}.", B("→", P, Q), [B("→", Q, P), B("∧", P, Q), B("↔", P, Q)],
     "“Se..., então...” é o condicional (→). A ordem importa: o “se” vem primeiro."),
    ("{p} se, e somente se, {q}.", B("↔", P, Q), [B("→", P, Q), B("→", Q, P), B("∧", P, Q)],
     "“se, e somente se” é o bicondicional (↔)."),
    ("{np}.", N(P), [P, N(Q), Q],
     "“não” indica negação (¬)."),
    ("{p}, mas {nq}.", B("∧", P, N(Q)), [B("∧", N(P), Q), B("∧", P, Q), B("→", P, N(Q))],
     "“mas” tem o mesmo papel do “e” (∧); a segunda parte está negada."),
    ("Se {np}, então {q}.", B("→", N(P), Q), [B("→", P, Q), B("∧", N(P), Q), B("→", Q, N(P))],
     "Condicional (→) com a primeira parte negada: ¬p → q."),
    ("{np} e {nq}.", B("∧", N(P), N(Q)), [B("∨", N(P), N(Q)), B("∧", P, Q), B("∧", N(P), Q)],
     "Duas negações ligadas por “e”: ¬p ∧ ¬q."),
]

def make_sentence_question():
    p, np, q, nq = random.choice(CONTEXTS)
    template, correct, wrong, explanation = random.choice(PATTERNS)
    sentence = template.format(p=p, np=np, q=q, nq=nq)
    sentence = sentence[0].upper() + sentence[1:]
    options, answer = shuffled(formula_str(correct, True), [formula_str(w, True) for w in wrong])
    return {
        "prompt": "Qual fórmula representa a frase?",
        "lines": [(f"“{sentence}”", "text"), ("", "muted"), (f"p: {p}", "muted"), (f"q: {q}", "muted")],
        "options": options, "answer": answer, "explanation": explanation,
    }

# 4. Tabela-verdade (questões originais, mais difíceis)
def make_table_question():
    q = make_class_question() if random.random() < .5 else make_equiv_question()
    if q["type"] == "class":
        kind = ["uma tautologia", "uma contingência", "uma contradição"][q["answer"]]
        return {
            "prompt": "Classifique a proposição:", "lines": [(q["formula"], "big")],
            "options": ["Tautologia", "Contingência", "Contradição"], "answer": q["answer"],
            "explanation": f"A proposição {q['formula']} é {kind}. Tautologia: sempre V · "
                           "Contradição: sempre F · Contingência: V e F.",
            "table": (q["vars"] + [q["formula"]],
                      [[r[v] for v in q["vars"]] + [evaluate(q["ast"], r)] for r in truth_rows(q["vars"])],
                      len(q["vars"])),
        }
    correct = q["options"][q["answer"]]
    return {
        "prompt": "Qual fórmula é logicamente equivalente a:", "lines": [(q["formula"], "big")],
        "options": q["options"], "answer": q["answer"],
        "explanation": "Fórmulas equivalentes têm a mesma coluna na tabela-verdade.",
        "table": (["p", "q", q["formula"], correct],
                  [[r["p"], r["q"], s == "1", s == "1"] for r, s in zip(truth_rows(["p", "q"]), q["sig"])], 2),
    }

GENERATORS = {
    "conectivos": lambda: make_rule_question() if random.random() < .7 else make_value_question(),
    "frases": make_sentence_question,
    "argumentos": make_argument_question,
    "tabelas": make_table_question,
}

def make_question(topics=("conectivos",)):
    topic = random.choice([t for t in topics if t in GENERATORS] or ["conectivos"])
    question = GENERATORS[topic]()
    question["topic"] = topic
    return question
