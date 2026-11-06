"""7ダイス対戦ゲーム（CUIプロトタイプ・2人ホットシート）

ルール概要:
- 赤・青のダイス（+アイテムで黄ダイス）を振り、合計が7なら「番」の人の勝ち。
- アンラッキーナンバー（親交代ごとに3つ）or ちょうど13 なら「番」の人の負け。
- 親はアイテムを使ったあと、今回のロールを「自分の番」にするか「相手の番」にするか選ぶ。
  - 自分の番でハズレ → ドロー（親交代）
  - 相手の番でハズレ → 同じ親でもう一度
- 勝負がつくたびに親交代。負けた側はライフ-1。ライフ0で敗北。

実行: python3 seven-dice-game.py [--seed N] [--life N]
"""

import argparse
import random
import sys
from dataclasses import dataclass, field

MAX_ITEMS = 8
UNLUCKY_COUNT = 3
CLEAR = "\n" * 60

ITEMS = {
    "yellow": "黄ダイス追加",
    "lucky": "ラッキー追加",
    "steal": "盗む",
    "blue_hi": "青4↑",
    "red_lo": "赤3↓",
    "flip": "ひっくり返す",
    "peek": "覗き見",
}
ITEM_HELP = {
    "yellow": "今回のロールに黄ダイスを1個追加",
    "lucky": "数字を1つ選んでラッキーナンバー（勝ち目）に追加（親交代まで）",
    "steal": "相手のアイテムを1つ奪う（すぐ使える）",
    "blue_hi": "今回の青ダイスを4〜6で振る",
    "red_lo": "今回の赤ダイスを1〜3で振る",
    "flip": "振った後、選んだダイスを裏返す（x → 7-x）",
    "peek": "振った後、選んだダイス1つの出目を親だけが見る",
}


@dataclass
class Player:
    name: str
    life: int
    items: list = field(default_factory=list)


@dataclass
class RollMods:
    yellow: int = 0
    blue_hi: bool = False
    red_lo: bool = False
    flips: list = field(default_factory=list)  # ダイスラベル
    peeks: list = field(default_factory=list)  # ダイスラベル

    def dice_labels(self):
        return ["赤", "青"] + [f"黄{i + 1}" for i in range(self.yellow)]

    def describe(self):
        parts = []
        if self.yellow:
            parts.append(f"黄ダイス×{self.yellow}")
        if self.blue_hi:
            parts.append("青4↑")
        if self.red_lo:
            parts.append("赤3↓")
        if self.flips:
            parts.append("裏返し:" + ",".join(self.flips))
        if self.peeks:
            parts.append("覗き見:" + ",".join(self.peeks))
        return " / ".join(parts) if parts else "なし"


# ---------- 入力ヘルパ ----------

def read(prompt):
    try:
        return input(prompt)
    except EOFError:
        print("\n入力終了。ゲームを終了します。")
        sys.exit(0)


def ask_choice(prompt, options):
    """options: 表示文字列のリスト。選ばれた index を返す。"""
    print(prompt)
    for i, opt in enumerate(options, 1):
        print(f"  {i}) {opt}")
    while True:
        s = read("> ").strip()
        if s.isdigit() and 1 <= int(s) <= len(options):
            return int(s) - 1
        print(f"  1〜{len(options)} の番号を入力してください")


def ask_number(prompt, allowed):
    allowed = sorted(allowed)
    while True:
        s = read(f"{prompt} {allowed}: ").strip()
        if s.isdigit() and int(s) in allowed:
            return int(s)
        print("  選べない数字です")


def pause(msg="(Enterで続行)"):
    read(msg)


# ---------- ゲーム本体 ----------

class Game:
    def __init__(self, names, life, rng):
        self.players = [Player(n, life) for n in names]
        self.rng = rng
        self.parent_idx = 0
        self.unlucky = set()
        self.lucky = set()

    @property
    def parent(self):
        return self.players[self.parent_idx]

    @property
    def child(self):
        return self.players[1 - self.parent_idx]

    # --- 表示 ---
    def show_status(self, mods=None):
        print("=" * 56)
        for p in self.players:
            mark = "【親】" if p is self.parent else "      "
            hearts = "♥" * p.life + "♡" * max(0, self.initial_life - p.life)
            items = ", ".join(ITEMS[i] for i in p.items) or "(なし)"
            print(f"{mark}{p.name:<6} {hearts}  所持: {items}")
        lucky = ",".join(map(str, sorted(self.lucky))) or "-"
        print(f"勝ち目: 7 + ラッキー[{lucky}]   負け目: 13 + アンラッキー[{','.join(map(str, sorted(self.unlucky)))}]")
        if mods is not None:
            print(f"今回の効果: {mods.describe()}")
        print("=" * 56)

    # --- 親交代 ---
    def new_parent_phase(self):
        self.lucky = set()
        self.unlucky = set(self.rng.sample([n for n in range(2, 13) if n != 7], UNLUCKY_COUNT))
        nums = ", ".join(map(str, sorted(self.unlucky)))
        print(f"\n>>> {self.parent.name} が親です。アンラッキーナンバーは {nums} ！")

    def give_items(self):
        p = self.parent
        if len(p.items) < MAX_ITEMS:
            it = self.rng.choice(list(ITEMS))
            p.items.append(it)
            print(f"  {p.name} に「{ITEMS[it]}」が配られた")
        else:
            print(f"  {p.name} は所持上限のため配布なし")

    # --- アイテムフェーズ ---
    def item_phase(self):
        mods = RollMods()
        while True:
            self.show_status(mods)
            p = self.parent
            opts = [f"{ITEMS[i]} - {ITEM_HELP[i]}" for i in p.items] + ["アイテム使用を終える"]
            idx = ask_choice(f"{p.name}: アイテムを使いますか？", opts)
            if idx == len(p.items):
                return mods
            item = p.items[idx]
            if self.use_item(item, mods):
                p.items.pop(idx)

    def use_item(self, item, mods):
        """使用成功なら True（アイテム消費）。"""
        p, c = self.parent, self.child
        if item == "yellow":
            mods.yellow += 1
            print("  黄ダイスが1個追加された")
        elif item == "lucky":
            max_sum = 12 + 6 * mods.yellow
            allowed = {n for n in range(2, max(13, max_sum + 1))
                       if n not in (7, 13) and n not in self.unlucky and n not in self.lucky}
            n = ask_number("  ラッキーナンバーにする数字", allowed)
            self.lucky.add(n)
            print(f"  ラッキーナンバーに {n} を追加")
        elif item == "steal":
            if not c.items:
                print("  相手はアイテムを持っていない（使用されません）")
                return False
            j = ask_choice("  どれを盗む？", [ITEMS[i] for i in c.items])
            stolen = c.items.pop(j)
            p.items.append(stolen)
            print(f"  {c.name} から「{ITEMS[stolen]}」を盗んだ")
        elif item == "blue_hi":
            if mods.blue_hi:
                print("  既に効果中です（使用されません）")
                return False
            mods.blue_hi = True
            print("  青ダイスは4〜6で振られる")
        elif item == "red_lo":
            if mods.red_lo:
                print("  既に効果中です（使用されません）")
                return False
            mods.red_lo = True
            print("  赤ダイスは1〜3で振られる")
        elif item == "flip":
            labels = mods.dice_labels()
            j = ask_choice("  どのダイスを裏返す？（振った後に適用）", labels)
            mods.flips.append(labels[j])
            print(f"  {labels[j]}を振った後に裏返す")
        elif item == "peek":
            labels = mods.dice_labels()
            j = ask_choice("  どのダイスを覗く？", labels)
            mods.peeks.append(labels[j])
            print(f"  {labels[j]}を振った後に覗き見する")
        return True

    # --- ロール ---
    def roll(self, mods):
        dice = {}
        dice["赤"] = self.rng.randint(1, 3) if mods.red_lo else self.rng.randint(1, 6)
        dice["青"] = self.rng.randint(4, 6) if mods.blue_hi else self.rng.randint(1, 6)
        for i in range(mods.yellow):
            dice[f"黄{i + 1}"] = self.rng.randint(1, 6)
        for label in mods.flips:
            if label in dice:
                dice[label] = 7 - dice[label]
        return dice

    def peek(self, mods, dice):
        print(CLEAR)
        print(f"*** {self.child.name} は画面を見ないでください ***")
        pause(f"{self.parent.name} だけが見ている状態で Enter > ")
        for label in mods.peeks:
            print(f"  [覗き見] {label}ダイス = {dice[label]}")
        pause("確認したら Enter（画面を消します） > ")
        print(CLEAR)

    def judge(self, total):
        """番の人から見た結果: 'win' / 'lose' / 'miss'"""
        if total == 7 or total in self.lucky:
            return "win"
        if total == 13 or total in self.unlucky:
            return "lose"
        return "miss"

    # --- 1回の親の手番 ---
    def play_parent_turn(self):
        """勝負 or ドローがついたら True（親交代）、もう一度なら False。"""
        print(f"\n--- アイテム配布 ---")
        self.give_items()
        mods = self.item_phase()

        dice = self.roll(mods)
        print("\n🎲 ダイスを振った（伏せたまま）")
        if mods.peeks:
            self.peek(mods, dice)
            self.show_status(mods)

        p, c = self.parent, self.child
        t = ask_choice(f"{p.name}: このロールは誰の番にする？",
                       [f"自分（{p.name}）の番", f"相手（{c.name}）の番"])
        turn_player = p if t == 0 else c
        other = c if t == 0 else p

        print("\n--- 公開 ---")
        print("  " + "  ".join(f"{k}:{v}" for k, v in dice.items()))
        total = sum(dice.values())
        print(f"  合計 = {total}  （{turn_player.name} の番）")

        result = self.judge(total)
        if result == "win":
            other.life -= 1
            print(f"  ★ {turn_player.name} の勝ち！ {other.name} のライフ -1")
            return True
        if result == "lose":
            turn_player.life -= 1
            print(f"  ✖ {turn_player.name} の負け！ {turn_player.name} のライフ -1")
            return True
        if turn_player is p:
            print("  ドロー。親が交代します。")
            return True
        print(f"  ハズレ。{p.name} がもう一度親を続けます。")
        return False

    def run(self):
        self.initial_life = self.players[0].life
        print("7ダイス対戦ゲーム 開始！")
        while True:
            self.new_parent_phase()
            while not self.play_parent_turn():
                pause()
            pause()
            losers = [p for p in self.players if p.life <= 0]
            if losers:
                winner = [p for p in self.players if p.life > 0][0]
                self.show_status()
                print(f"\n🏆 {winner.name} の勝利！")
                return
            self.parent_idx = 1 - self.parent_idx


def main():
    ap = argparse.ArgumentParser(description="7ダイス対戦ゲーム（CUI）")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--life", type=int, default=3)
    ap.add_argument("--names", nargs=2, default=["P1", "P2"])
    args = ap.parse_args()
    Game(args.names, args.life, random.Random(args.seed)).run()


if __name__ == "__main__":
    main()
