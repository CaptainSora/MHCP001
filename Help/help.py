async def help_page(ctx, app):
    """
    Prints the help page for the app.
    app.txt must exist in the Help folder.
    """
    with open(f'Help/{app}.txt') as f:
        helpstr = f.read()
    await ctx.send(helpstr)
