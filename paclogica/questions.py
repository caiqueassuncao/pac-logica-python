"""Questões de lógica proposicional para o Pac-Lógica.

Este arquivo contém o banco de questões unificado. 
Ele integra os geradores dinâmicos originais e as questões extras de forma que a 
função `make_question` possa retornar questões de ambas as fontes.

Cada questão é um dicionário com:
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
V_VAL, F_VAL = True, False

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

# ============================================================================
# RESUMOS TEÓRICOS (Das questões extras)
# ============================================================================
RESUMOS = {
    "conjuncao": "p ∧ q ('p e q') só é verdadeira quando as duas partes são verdadeiras.",
    "disjuncao": "p ∨ q ('p ou q') só é falsa quando as duas partes são falsas. "
                 "É um 'ou' inclusivo: vale se uma das duas, ou as duas, forem verdadeiras.",
    "condicional": "p → q só é falsa quando p é verdadeiro e q é falso (promessa quebrada). "
                   "Se p é falso, a condicional é verdadeira.",
    "bicondicional": "p ↔ q é verdadeiro quando p e q têm o mesmo valor (ambos V ou ambos F) "
                     "e falso quando têm valores diferentes.",
    "avaliacao": "Para avaliar uma fórmula, troque as letras pelos valores, resolva primeiro os "
                 "parênteses e a negação, depois ∧, ∨, → e, por último, ↔.",
    "modus_ponens": "Modus ponens: de p → q e p, conclui-se q. Argumento válido.",
    "modus_tollens": "Modus tollens: de p → q e ¬q, conclui-se ¬p. Argumento válido.",
    "silogismo_hipotetico": "Silogismo hipotético: de p → q e q → r, conclui-se p → r. Argumento válido.",
    "silogismo_disjuntivo": "Silogismo disjuntivo: de p ∨ q e ¬p, conclui-se q. Argumento válido.",
    "afirmacao_consequente": "Afirmar o consequente (de p → q e q, concluir p) é um sofisma: "
                             "q pode ser verdadeiro por outro motivo.",
    "negacao_antecedente": "Negar o antecedente (de p → q e ¬p, concluir ¬q) é um sofisma: "
                           "q pode ser verdadeiro mesmo sem p.",
    "falacia_disjuncao": "Como o 'ou' é inclusivo, saber que p é verdadeiro não permite "
                         "concluir que q é falso.",
    "silogismo_categorico": "Em argumentos com 'todo', 'nenhum' e 'algum', pense em conjuntos: "
                            "'todo A é B' significa que A está dentro de B.",
    "termo_medio": "O termo médio (o que aparece nas duas premissas) precisa realmente ligar os "
                   "outros dois termos. Estar dentro do mesmo grupo não torna dois termos iguais.",
    "somente_se": "'p somente se q' é p → q. A condição necessária fica depois do 'somente se'.",
    "nem_nem": "'Nem p nem q' é ¬p ∧ ¬q, o mesmo que ¬(p ∨ q).",
    "a_menos_que": "'p a menos que q' é ¬q → p (se não q, então p), equivalente a p ∨ q.",
    "suficiente_necessaria": "'p é suficiente para q' é p → q. 'p é necessária para q' é q → p.",
    "ou_exclusivo": "'Ou p ou q, mas não os dois' é verdadeiro quando exatamente um deles é "
                    "verdadeiro: (p ∨ q) ∧ ¬(p ∧ q).",
    "negacao_condicional": "¬(p → q) ≡ p ∧ ¬q. Negar uma condicional é afirmar o antecedente "
                           "e negar o consequente.",
    "de_morgan": "Leis de De Morgan: ¬(p ∧ q) ≡ ¬p ∨ ¬q e ¬(p ∨ q) ≡ ¬p ∧ ¬q.",
    "contrapositiva": "p → q ≡ ¬q → ¬p ≡ ¬p ∨ q. A recíproca (q → p) e a inversa (¬p → ¬q) "
                      "não são equivalentes à original.",
    "classificacao": "Tautologia: sempre V. Contradição: sempre F. "
                     "Contingência: V em algumas linhas e F em outras.",
    "equivalencia": "Duas fórmulas são equivalentes quando têm a mesma coluna final na "
                    "tabela-verdade. Exemplo: p → q ≡ ¬p ∨ q.",
    "contagem": "Com n letras, a tabela-verdade tem 2ⁿ linhas. Conte as linhas em que a "
                "fórmula dá o valor pedido.",
}

# ============================================================================
# GERADORES DINÂMICOS ORIGINAIS
# ============================================================================

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


def _q(conceito, enunciado, opcoes, correta, explicacao, **extra):
    questao = {
        "conceito": conceito,
        "prompt": enunciado,
        "options": opcoes,
        "answer": correta,
        "explanation": explicacao,
        "lines": []
    }
    questao.update(extra)
    return questao

def _frase(conceito, legenda, frase, opcoes, correta, explicacao):
    enunciado = "Qual fórmula representa a frase?"
    return _q(
        conceito, enunciado, opcoes, correta, explicacao,
        lines=[(f"“{frase}”", "text"), ("", "muted"), (f"Legenda: {legenda}", "muted")]
    )

def _argumento(conceito, premissas, conclusao, valido, explicacao):
    lines = [(f"Premissa: {p}", "text") for p in premissas]
    lines.append((conclusao, "accent"))
    return _q(
        conceito, "Este argumento é um silogismo ou um sofisma?",
        ["Silogismo (válido)", "Sofisma (inválido)"], 0 if valido else 1, explicacao,
        lines=lines
    )

EXTRA_CONECTIVOS = [
    _q("conjuncao", "A conjunção p ∧ q é verdadeira quando:",
       ["pelo menos uma das duas é verdadeira", "p e q são ambas verdadeiras", "p e q têm valores diferentes"],
       1, "O 'e' exige as duas partes verdadeiras. Basta uma ser falsa para a conjunção ser falsa."),
    _q("disjuncao", "A disjunção p ∨ q é falsa quando:",
       ["p e q são ambas falsas", "pelo menos uma delas é falsa", "p é falsa e q é verdadeira"],
       0, "O 'ou' inclusivo só falha quando nenhuma das partes é verdadeira."),
    _q("condicional", "A condicional p → q é falsa somente quando:",
       ["p é falso e q é verdadeiro", "p e q são ambos falsos", "p é verdadeiro e q é falso"],
       2, "É a promessa quebrada: o antecedente acontece (V) e o consequente não (F)."),
    _q("modus_ponens", "Sabendo que p → q é verdadeira e que p é verdadeiro, o valor de q é:",
       ["Falso", "Verdadeiro", "Pode ser verdadeiro ou falso"],
       1, "Se q fosse falso, teríamos V → F, e a condicional seria falsa. Logo, q é verdadeiro (modus ponens)."),
    _q("condicional", "Se p é falso, a condicional p → q é:",
       ["Falsa, qualquer que seja q", "Igual ao valor de q", "Verdadeira, qualquer que seja q"],
       2, "Com antecedente falso não há promessa a quebrar, então a condicional é verdadeira."),
    _q("bicondicional", "O bicondicional p ↔ q é falso quando:",
       ["p e q são ambos verdadeiros", "p e q têm valores diferentes", "p e q são ambos falsos"],
       1, "O bicondicional exige valores iguais. Quando um é V e o outro é F, ele é falso."),
    _q("avaliacao", "Sabendo que p = V e q = F, qual das proposições é verdadeira?",
       ["p ∧ q", "¬p ∨ q", "p → q", "p ∨ q"],
       3, "Com p = V e q = F, apenas p ∨ q = V ∨ F = V é verdadeira."),
    _q("avaliacao", "Sabendo que p = F e q = V, qual das proposições é falsa?",
       ["p → q", "¬p ∧ q", "q → p", "p ↔ ¬q"],
       2, "Com p = F e q = V, q → p = V → F = F. Só q → p é falsa (promessa quebrada)."),
    _q("avaliacao", "Sabendo que p = V, q = V e r = F, qual das proposições é verdadeira?",
       ["(p ∧ q) → r", "p ∧ (q → r)", "¬p ∨ r", "(p ∨ r) → q"],
       3, "Com p = V, q = V e r = F: (p ∨ r) → q = V → V = V."),
    _q("avaliacao", "Sabendo que p = F, q = F e r = V, qual das proposições é verdadeira?",
       ["p ∨ q", "(p → q) ∧ ¬r", "q ∧ r", "(p ↔ q) ∧ r"],
       3, "Com p = F, q = F e r = V: (p ↔ q) ∧ r = V ∧ V = V."),
    _q("avaliacao", "Sabendo que p = V, q = F e r = F, qual das proposições é falsa?",
       ["(p → q) ∨ r", "p ∨ (q ∧ r)", "(q → r) ∧ p", "¬q ↔ ¬r"],
       0, "Com p = V, q = F e r = F: p → q = F, então (p → q) ∨ r = F ∨ F = F."),
    _q("condicional", "Sabendo que p → q é falsa, o valor de ¬p ∨ q é:",
       ["Verdadeiro", "Falso", "Não é possível saber"],
       1, "p → q só é falsa com p = V e q = F. Então ¬p = F e q = F, e F ∨ F = F."),
]

EXTRA_FRASES = [
    _frase("condicional", "p: 'o sinal está vermelho' e q: 'o carro para'",
           "Se o sinal está vermelho, então o carro para.",
           ["q → p", "p → q", "p ∧ q", "p ∨ q"], 1,
           "'Se A, então B' é a forma direta da condicional: p → q."),
    _frase("somente_se", "p: 'Ana é aprovada' e q: 'Ana estuda'",
           "Ana é aprovada somente se estuda.",
           ["q → p", "p ↔ q", "p → q", "p ∧ q"], 2,
           "'p somente se q' significa que q é condição necessária para p, logo p → q."),
    _frase("nem_nem", "p: 'Lia canta' e q: 'Lia dança'",
           "Lia nem canta nem dança.",
           ["¬p ∧ ¬q", "¬(p ∧ q)", "p ∧ ¬q", "¬p ∨ q"], 0,
           "'Nem p nem q' nega as duas coisas ao mesmo tempo: ¬p ∧ ¬q."),
    _frase("a_menos_que", "p: 'vou à praia' e q: 'chove'",
           "Vou à praia a menos que chova.",
           ["p → ¬q", "q → p", "p ∧ ¬q", "¬q → p"], 3,
           "'p a menos que q' significa 'se não q, então p': ¬q → p."),
    _frase("de_morgan", "p: 'o aluno é aplicado' e q: 'o aluno é pontual'",
           "Não é verdade que o aluno é aplicado e pontual.",
           ["¬p ∧ ¬q", "¬(p ∧ q)", "p ∧ ¬q", "¬p → q"], 1,
           "O 'não é verdade que' vale para a frase inteira, então o ¬ fica fora dos parênteses: ¬(p ∧ q)."),
    _frase("conjuncao", "p: 'o filme é longo' e q: 'o filme é bom'",
           "O filme é longo, mas é bom.",
           ["p → q", "p ∨ q", "p ↔ q", "p ∧ q"], 3,
           "'Mas' marca um contraste, mas logicamente as duas partes são afirmadas (conjunção)."),
    _frase("bicondicional", "p: 'o número é par' e q: 'o número é divisível por 2'",
           "O número é par se, e somente se, é divisível por 2.",
           ["p → q", "q → p", "p ↔ q", "p ∧ q"], 2,
           "'Se, e somente se' é o bicondicional (↔)."),
    _frase("suficiente_necessaria", "p: 'chove' e q: 'a rua fica molhada'",
           "Chover é condição suficiente para a rua ficar molhada.",
           ["q → p", "p ↔ q", "p ∧ q", "p → q"], 3,
           "Condição suficiente: basta p acontecer para q acontecer, logo p → q."),
    _frase("suficiente_necessaria", "p: 'o aluno tem a frequência mínima' e q: 'o aluno é aprovado'",
           "Ter a frequência mínima é condição necessária para ser aprovado.",
           ["p → q", "q → p", "p ↔ q", "¬p → q"], 1,
           "Condição necessária: se q acontece então p aconteceu, ou seja, q → p."),
    _frase("ou_exclusivo", "p: 'vou de ônibus' e q: 'vou de metrô'",
           "Ou vou de ônibus, ou vou de metrô, mas não os dois.",
           ["p ∨ q", "p ↔ q", "(p ∨ q) ∧ ¬(p ∧ q)", "p ∧ ¬q"], 2,
           "É o 'ou' exclusivo: verdadeiro quando exatamente um dos dois acontece."),
    _frase("negacao_condicional", "p: 'chove' e q: 'o jogo é cancelado'",
           "Não é verdade que, se chove, o jogo é cancelado.",
           ["¬p → ¬q", "p → ¬q", "¬p ∧ q", "¬(p → q)"], 3,
           "A frase nega a condicional inteira: ¬(p → q)."),
    _frase("condicional", "p: 'Luís compra pão', q: 'Luís compra leite' e r: 'Luís vai ao mercado'",
           "Se Luís vai ao mercado, então compra pão ou leite.",
           ["(p ∨ q) → r", "r → (p ∧ q)", "r → (p ∨ q)", "r ∧ (p ∨ q)"], 2,
           "O 'pão ou leite' é o consequente: r → (p ∨ q)."),
]

EXTRA_SILOGISMOS = [
    _argumento("modus_ponens", ["Se o código compila, então o teste roda.", "O código compila."], "Logo, o teste roda.", True, "Modus ponens: de p → q e p, conclui-se q."),
    _argumento("afirmacao_consequente", ["Se Marta viaja, o apartamento fica vazio.", "O apartamento está vazio."], "Logo, Marta viajou.", False, "Afirmação do consequente. O apartamento pode estar vazio por outro motivo."),
    _argumento("silogismo_hipotetico", ["Se chove, a rua molha.", "Se a rua molha, o chão fica escorregadio."], "Logo, se chove, o chão fica escorregadio.", True, "Silogismo hipotético: p → q e q → r levam a p → r."),
    _argumento("falacia_disjuncao", ["Hoje eu como pizza ou massa.", "Hoje eu comi pizza."], "Logo, hoje eu não comi massa.", False, "Na lógica o 'ou' é inclusivo: as duas coisas podem acontecer."),
    _argumento("modus_tollens", ["Se há fumaça, então há fogo.", "Não há fogo."], "Logo, não há fumaça.", True, "Modus tollens: de p → q e ¬q, conclui-se ¬p."),
    _argumento("termo_medio", ["Todo gato é animal.", "Todo cachorro é animal."], "Logo, todo gato é cachorro.", False, "O termo médio (animal) não liga gato a cachorro. Estar no mesmo grupo não os iguala."),
    _argumento("silogismo_disjuntivo", ["O ladrão entrou pela porta ou pela janela.", "Ele não entrou pela porta."], "Logo, ele entrou pela janela.", True, "Silogismo disjuntivo: de p ∨ q e ¬p, conclui-se q."),
    _argumento("negacao_antecedente", ["Se o aluno estuda, ele é aprovado.", "O aluno não estudou."], "Logo, o aluno não foi aprovado.", False, "Negação do antecedente. p → q só garante q quando p acontece."),
    _argumento("silogismo_categorico", ["Todo mamífero é animal.", "Todo cão é mamífero."], "Logo, todo cão é animal.", True, "Silogismo clássico Barbara: o 'todo' é transitivo."),
    _argumento("termo_medio", ["Todo atleta é saudável.", "Alguns brasileiros são saudáveis."], "Logo, alguns brasileiros são atletas.", False, "O grupo 'saudável' é maior que 'atleta'. Não se pode concluir a ligação."),
    _argumento("silogismo_categorico", ["Nenhum réptil é mamífero.", "Todo jacaré é réptil."], "Logo, nenhum jacaré é mamífero.", True, "Jacarés estão dentro de répteis, e répteis não têm nada em comum com mamíferos."),
    _argumento("silogismo_categorico", ["Alguns estudantes são atletas.", "Todo atleta é disciplinado."], "Logo, alguns estudantes são disciplinados.", True, "Existe ao menos um estudante que é atleta, logo ele é disciplinado."),
]

EXTRA_TABELAS = [
    _q("classificacao", "Classifique a fórmula p ∨ ¬p:", ["Tautologia", "Contradição", "Contingência"], 0, "É sempre verdadeira: tautologia (princípio do terceiro excluído)."),
    _q("classificacao", "Classifique a fórmula p ∧ ¬p:", ["Contingência", "Contradição", "Tautologia"], 1, "A conjunção é sempre falsa: contradição."),
    _q("classificacao", "Classifique a fórmula (p → q) ∨ (q → p):", ["Contradição", "Contingência", "Tautologia"], 2, "O resultado é V nas quatro linhas: tautologia."),
    _q("classificacao", "Classifique a fórmula (p → q) ∧ p:", ["Tautologia", "Contingência", "Contradição"], 1, "Aparecem V e F: contingência."),
    _q("classificacao", "Classifique a fórmula p → ¬p:", ["Contradição", "Tautologia", "Contingência"], 2, "Aparecem V e F: contingência."),
    _q("classificacao", "Classifique a fórmula (p ∨ q) ∧ (¬p ∧ ¬q):", ["Contradição", "Tautologia", "Contingência"], 0, "As duas partes nunca são verdadeiras juntas: contradição."),
    _q("equivalencia", "Qual das fórmulas é equivalente a p → q?", ["p ∨ ¬q", "¬p ∧ q", "q → p", "¬p ∨ q"], 3, "p → q ≡ ¬p ∨ q: as duas só são falsas na linha p = V, q = F."),
    _q("contrapositiva", "A contrapositiva de p → q é:", ["¬p → ¬q", "q → p", "¬q → ¬p", "¬(p → q)"], 2, "A contrapositiva troca e nega: p → q ≡ ¬q → ¬p."),
    _q("de_morgan", "A negação de p ∨ q é equivalente a:", ["¬p ∨ ¬q", "p ∧ q", "¬p → q", "¬p ∧ ¬q"], 3, "Lei de De Morgan: ¬(p ∨ q) ≡ ¬p ∧ ¬q."),
    _q("contagem", "Na tabela-verdade de (p ∧ q) → r, quantas das 8 linhas têm resultado V?", ["5", "6", "7", "8"], 2, "Apenas p=V, q=V e r=F resulta em F. Logo, 7 das 8 linhas são V."),
]

def format_extra(q):
    """Acrescenta o resumo da teoria à explicação, se existir."""
    if "conceito" in q and q["conceito"] in RESUMOS:
        q["explanation"] = f"{q['explanation']} · Resumo: {RESUMOS[q['conceito']]}"
    return q



GENERATORS = {
    "conectivos": [make_rule_question, make_value_question] + [lambda q=q: format_extra(q.copy()) for q in EXTRA_CONECTIVOS],
    "frases": [make_sentence_question] + [lambda q=q: format_extra(q.copy()) for q in EXTRA_FRASES],
    "argumentos": [make_argument_question] + [lambda q=q: format_extra(q.copy()) for q in EXTRA_SILOGISMOS],
    "tabelas": [make_table_question] + [lambda q=q: format_extra(q.copy()) for q in EXTRA_TABELAS],
}

def make_question(topics=("conectivos",)):
    topic = random.choice([t for t in topics if t in GENERATORS] or ["conectivos"])
    question = random.choice(GENERATORS[topic])()
    question["topic"] = topic
    return question