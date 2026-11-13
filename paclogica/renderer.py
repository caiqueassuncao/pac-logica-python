import math
import pygame
from . import config
from .config import TILE, ROWS, COLS, WIDTH, HEIGHT, BG, WALL, WALL_INNER, YELLOW, WHITE, MUTED, GREEN, RED
from .logic import truth_rows, evaluate

class RendererMixin:
    def draw_text(self, text, x, y, color=WHITE, font=None, center=False):
        surf = (font or self.font).render(str(text), True, color)
        rect = surf.get_rect()
        if center: rect.center = (x,y)
        else: rect.topleft = (x,y)
        self.screen.blit(surf, rect)

    def draw_entity(self, e, pacman=False):
        x,y = e.pixel()
        if pacman:
            if self.inv > 0 and pygame.time.get_ticks()//120 % 2 == 0: return
            angle = math.atan2(e.dr,e.dc)
            mouth = .25 + .18*abs(math.sin(pygame.time.get_ticks()/110))
            points = [(x,y)]
            for i in range(31):
                a = angle + mouth*math.pi + (2-2*mouth)*math.pi*i/30
                points.append((x+math.cos(a)*TILE*.42,y+math.sin(a)*TILE*.42))
            pygame.draw.polygon(self.screen,YELLOW,points)
        else:
            r = TILE*.38
            pygame.draw.circle(self.screen,e.color,(int(x),int(y-2)),int(r))
            pygame.draw.rect(self.screen,e.color,(int(x-r),int(y-2),int(2*r),int(r)))
            for i in range(3):
                xx = x-r+(i+.5)*2*r/3
                pygame.draw.circle(self.screen,e.color,(int(xx),int(y+r-5)),int(r/3))
            for off in (-6,6):
                pygame.draw.circle(self.screen,WHITE,(int(x+off),int(y-5)),5)
                pygame.draw.circle(self.screen,(16,20,40),(int(x+off+e.dc*2),int(y-5+e.dr*2)),2)

    def draw_maze(self):
        self.screen.fill(BG)
        for r,row in enumerate(config.MAP):
            for c,ch in enumerate(row):
                if ch == "#":
                    rect = pygame.Rect(c*TILE+2,r*TILE+2,TILE-4,TILE-4)
                    pygame.draw.rect(self.screen,WALL,rect,border_radius=8)
                    pygame.draw.rect(self.screen,WALL_INNER,rect.inflate(-8,-8),border_radius=5)
        if self.state not in ("menu",):
            for (r,c),col in self.dots.items():
                x,y=(c+.5)*TILE,(r+.5)*TILE
                pygame.draw.circle(self.screen,col,(int(x),int(y)),7)
                pygame.draw.circle(self.screen,WHITE,(int(x-2),int(y-2)),2)
            self.draw_entity(self.player,True)
            for ghost in self.ghosts: self.draw_entity(ghost)
        pygame.draw.rect(self.screen,(15,18,48),(0,ROWS*TILE,WIDTH,100))
        self.draw_text("❤️ " + str(max(0,self.hearts)),18,ROWS*TILE+12,RED,self.font)
        self.draw_text(f"🍬 {self.eaten}/{config.TOTAL_DOTS}",150,ROWS*TILE+12,YELLOW,self.font)
        self.draw_text("Setas ou WASD para mover",18,ROWS*TILE+48,MUTED,self.small)

    def wrap_text(self, text, font, max_width):
        words, lines, line = text.split(), [], ""
        for word in words:
            test = (line+" "+word).strip()
            if font.size(test)[0] <= max_width: line = test
            else:
                if line: lines.append(line)
                line = word
        if line: lines.append(line)
        return lines

    def draw_overlay(self, title, body, buttons=None, title_color=WHITE):
        panel = pygame.Rect(35,55,WIDTH-70,HEIGHT-10)
        pygame.draw.rect(self.screen,(18,22,62),panel,border_radius=18)
        pygame.draw.rect(self.screen,(80,100,255),panel,2,border_radius=18)
        self.draw_text(title,WIDTH//2,85,title_color,self.big,True)
        y=130
        for line in body:
            for wrapped in self.wrap_text(line,self.font,WIDTH-110):
                self.draw_text(wrapped,WIDTH//2,y,WHITE,self.font,True); y+=31
            y+=7
        if buttons:
            n=len(buttons); bw=min(250,(WIDTH-100)//n)
            total=n*bw+(n-1)*10; x0=(WIDTH-total)//2
            self.button_rects=[]
            for i,(label,_) in enumerate(buttons):
                rect=pygame.Rect(x0+i*(bw+10),HEIGHT-95,bw,48)
                pygame.draw.rect(self.screen,(50,70,170),rect,border_radius=10)
                self.draw_text(label,rect.centerx,rect.centery,WHITE,self.small,True)
                self.button_rects.append((rect,buttons[i][1]))

    def draw(self):
        self.draw_maze()
        if self.state == "menu":
            self.draw_overlay("🟡 PAC-LÓGICA",[
                f"Coma os {config.TOTAL_DOTS} docinhos 🍬 e fuja dos fantasmas 👻.",
                "Cada docinho traz uma questão de lógica proposicional.",
                "Classifique fórmulas ou encontre uma equivalente lógica.",
                "Errar ou ser pego custa 1 coração. Há uma chance de reviver."
            ],[("Jogar","start")])
        elif self.state == "quiz":
            q=self.question
            body=[("Errar custa 1 coração." if self.quiz_mode=="eat" else "Acerte para voltar com 2 corações. Só há uma chance."),
                  ("Classifique a proposição:" if q["type"]=="class" else "Qual é logicamente equivalente a:"),
                  q["formula"]]
            if q["type"]=="class":
                labels=["Tautologia","Contingência","Contradição"]
            else: labels=q["options"]
            self.draw_overlay("🍬 QUESTÃO DE LÓGICA",body,[(label,i) for i,label in enumerate(labels)])
        elif self.state == "feedback":
            q=self.question; ok=self.feedback
            body=["Resposta correta!" if ok else "Resposta incorreta."]
            if q["type"]=="class":
                body.append("Classificação: "+["tautologia","contingência","contradição"][q["answer"]]+".")
                body.append("Tabela-verdade:")
                for row in truth_rows(q["vars"]):
                    vals="  ".join("V" if row[v] else "F" for v in q["vars"])
                    body.append(vals+"  →  "+("V" if evaluate(q["ast"],row) else "F"))
            else:
                body += ["Equivalente correta: "+q["options"][q["answer"]],
                         "Coluna final (VV, VF, FV, FF): "+" ".join("V" if x=="1" else "F" for x in q["sig"])]
            self.draw_overlay("✅ CORRETO!" if ok else "❌ ERROU!",body,[("Continuar","continue")],GREEN if ok else RED)
        elif self.state == "over":
            self.draw_overlay("GAME OVER 💀",[f"Você comeu {self.eaten} de {config.TOTAL_DOTS} docinhos."],[("Jogar novamente","restart")],RED)
        elif self.state == "win":
            self.draw_overlay("🏆 VOCÊ VENCEU!",["Todos os docinhos foram comidos!"],[("Jogar novamente","restart")],GREEN)

