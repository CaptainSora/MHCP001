DL_DICT = {
    ("hey",): "8/8f/10001_en.png",
    ("good job", "gj"): "d/d1/10002_en.png",
    ("thanks", "ty"): "c/c5/10003_en.png",
    ("sorry", "sry"): "b/b6/10004_en.png",
    ("okay", "ok", "kk"): "2/2a/10005_en.png",
    ("nope", "no"): "6/63/10006_en.png",
    ("no worries", "nw"): "1/1c/10008_en.png",
    ("yes",): "4/4b/10014_en.png",
    ("heh", "hehe"): "1/13/10016_en.png",
    ("again",): "2/22/10018_2_en.png",
    ("on my way", "omw"): "3/3c/10020_en.png",
    ("yay",): "e/ee/10021_en.png",
    ("you got this", "got it", "gotcha"): "4/45/10022_2_en.png",
    ("for real", "fr"): "c/c3/10024_en.png",
    ("whew", "wew"): "a/ac/10025_en.png",
    ("victory", "v"): "5/52/10028_en.png",
    ("boom",): "0/0f/10203.png",
    ("sup",): "9/9b/10302_en.png",
    ("hello there", "hello"): "6/63/11501_en.png",
    ("goodnight", "gnight", "gn"): "8/8b/11304_en.png",
    ("see ya", "seeya", "cya"): "2/2a/11305_en.png",
    ("time for a break", "break time", "break"): "a/a2/11306_en.png"
}
DL_PREFIX = \
    "https://static.wikia.nocookie.net/dragalialost_gamepedia_en/images/"

async def dl_emote(ctx, args):
    if len(args) == 0:
        helpstr = "List of triggers:"
        for k in DL_DICT.keys():
            helpstr += "\n"
            if len(k) == 1:
                helpstr += k[0]
            else:
                helpstr += ', '.join(k)
        await ctx.send(helpstr)
        return
    else:
        trigger = ' '.join(args)
        for k, v in DL_DICT.items():
            if trigger in k:
                await ctx.message.delete()
                await ctx.send(f"{DL_PREFIX}{v}")
                return
