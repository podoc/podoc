from podoc.ast import AST, Block, Inline

# hello *world*
ast = AST(blocks=[Block(name='Para',
                  inlines=['hello',
                           Inline(name='Space'),
                           Inline(name='Emph', contents=['world'])
                           ])])
