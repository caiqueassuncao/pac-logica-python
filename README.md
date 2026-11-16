# Pac-Lógica — Python

Jogo educativo de lógica proposicional feito com Pygame (pygame-ce).
Roda no Windows, macOS e Linux com Python 3.9 ou mais recente.

## Instalar e executar

**Windows (PowerShell)**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```
No Debian/Ubuntu, se o `venv` não existir: `sudo apt install python3-venv`.

Também é possível executar com `python -m paclogica`.

## Como jogar
- Setas ou WASD: movimentar o Pac-Man. ESC ou P: pausar. F11: tela cheia.
- No menu, escolha a proporção da tela: **4:3** (HUD embaixo) ou **16:9** (labirinto maior e
  painel lateral). A escolha fica salva; na primeira execução o jogo usa a do seu monitor.
  A janela pode ser redimensionada à vontade.
- Cada docinho traz uma questão de lógica, com 15 segundos para responder.
  Responda clicando ou com as teclas 1 a 4.
- Errar, deixar o tempo acabar ou ser pego por um fantasma custa 1 coração. Há uma chance de reviver.

### Tipos de questão
- **Regras dos conectivos**: “O bicondicional p ↔ q é verdadeiro quando:” com 3 alternativas,
  ou “p = V, q = F. Qual proposição é verdadeira?”.
- **Frase → fórmula**: “Se está chovendo, então eu levo guarda-chuva.” → `p → q`.
- **Silogismo ou sofisma**: duas premissas e uma conclusão; diga se o argumento é válido.
- **Tabela-verdade**: classificar fórmulas e achar equivalências (só nos níveis finais).

O banco de questões fica em `paclogica/questions.py`.

### Modos e escala de níveis
- **Tradicional**: cada nível tem uma meta de pontos. Ao atingi-la você sobe de nível.
  Se os docinhos acabarem antes da meta, o labirinto é reabastecido.
- **Arcade**: sem metas. Limpar o labirinto inicia uma nova onda, mais difícil.
  Some pontos até perder todos os corações e entre no ranking.

| Nível | Meta | Questões |
|---|---|---|
| 1–2 | 6 / 8 | Regras dos conectivos |
| 3 | 9 | Conectivos + Frase → fórmula |
| 4 | 10 | Frase → fórmula |
| 5 | 12 | Frase → fórmula + Silogismo ou sofisma |
| 6 | 13 | Silogismo ou sofisma |
| 7 | 15 | Conectivos, frases e argumentos |
| 8 | 18 | Tudo, incluindo tabela-verdade |

Cada nível também tem mais fantasmas, mais docinhos e fantasmas mais rápidos.
No arcade, a onda N usa as questões do nível N.

### Pontuação
| Ação | Pontos |
|---|---|
| Docinho com resposta correta | 1 |
| Cereja / Morango / Melancia | +2 / +3 / +5 |
| Laranja / Uva | multiplicador ×2 por 12 s / ×3 por 9 s |

As frutas aparecem de tempos em tempos e somem depois de alguns segundos.
O multiplicador vale para todos os pontos, inclusive para as respostas das questões.

## Banco de dados
O jogo usa SQLite (já incluso no Python), em um arquivo `paclogica.db` na pasta de dados do usuário:

| Sistema | Pasta |
|---|---|
| Windows | `%APPDATA%\PacLogica` |
| macOS | `~/Library/Application Support/PacLogica` |
| Linux | `~/.local/share/paclogica` (ou `$XDG_DATA_HOME/paclogica`) |

Para usar outra pasta, defina a variável de ambiente `PACLOGICA_DATA_DIR`.

Tabelas:
- `levels`: escala de níveis (meta, docinhos, fantasmas, velocidade, intervalo das frutas
  e tipos de questão, ex.: `conectivos,frases`).
  É preenchida na primeira execução e pode ser editada para ajustar ou criar níveis.
- `scores`: histórico de partidas, usado no ranking de cada modo.
- `players`: melhor nível alcançado e número de partidas de cada jogador.
- `settings`: preferências, como o último nome digitado e a proporção da tela.

## Testes
```bash
python -m unittest discover -s tests -t .
```

## Arquitetura
```text
pac-logica-python/
├── main.py
├── requirements.txt
├── tests/              # testes de pontuação, banco de dados e fluxo do jogo
└── paclogica/
    ├── config.py       # mapa, dimensões, cores e balanceamento
    ├── database.py     # SQLite: níveis, ranking, jogadores e preferências
    ├── effects.py      # partículas, textos flutuantes e avisos
    ├── entities.py     # Pac-Man, fantasmas e frutas
    ├── fonts.py        # escolha de fontes com suporte aos símbolos lógicos
    ├── game.py         # estados, modos de jogo, colisões e loop principal
    ├── input.py        # comandos do teclado
    ├── layout.py       # posição do labirinto e do HUD em 4:3 e 16:9
    ├── logic.py        # fórmulas, tabelas-verdade e perguntas
    ├── maze.py         # caminhos e distribuição dos docinhos
    ├── questions.py    # banco de questões por tipo
    ├── renderer.py     # desenho do jogo, HUD, menu, ranking e telas
    └── scoring.py      # pontuação, frutas especiais e multiplicadores
```
