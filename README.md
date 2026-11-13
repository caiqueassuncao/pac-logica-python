# Pac-Lógica — Python

Jogo educativo de lógica proposicional, convertido para Python com Pygame.

## Executar
```bash
python -m pip install -r requirements.txt
python main.py
```

## Controles
- Setas ou WASD: movimentar o Pac-Man.
- Mouse: selecionar alternativas e botões.

## Arquitetura
```text
PacLogica_Python/
├── main.py
├── requirements.txt
├── README.md
└── paclogica/
    ├── __init__.py
    ├── config.py       # mapa, dimensões, cores e balanceamento
    ├── entities.py     # entidade móvel (Pac-Man e fantasmas)
    ├── game.py         # regras, estados, colisões e loop principal
    ├── input.py        # comandos do teclado
    ├── logic.py        # fórmulas, tabelas-verdade e perguntas
    ├── maze.py         # caminhos e distribuição dos docinhos
    └── renderer.py     # desenho do jogo e telas
```

## Mudanças nesta versão
- Labirinto ampliado para 17 linhas × 23 colunas.
- Docinhos reduzidos de 20 para 12.
- Fantasmas reduzidos de 3 para 2.
- Projeto separado em módulos com responsabilidades específicas.
