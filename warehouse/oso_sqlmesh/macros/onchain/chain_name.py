from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def chain_name(evaluator: MacroEvaluator, chain: exp.Expression):
    """Standardizes chain names across models."""
    return exp.Upper(
        this=exp.Case(
            ifs=[
                exp.If(
                    this=exp.EQ(this=chain, expression=exp.Literal.string("op")),
                    true=exp.Literal.string("optimism"),
                ),
                exp.If(
                    this=exp.EQ(this=chain, expression=exp.Literal.string("fraxtal")),
                    true=exp.Literal.string("frax"),
                ),
            ],
            default=chain,
        )
    )


@macro()
def chain_id_name(evaluator: MacroEvaluator, chain_id: exp.Expression):
    """Maps chain IDs to standardized chain names.
    
    Args:
        evaluator: The macro evaluator
        chain_id: The expression containing the chain ID (integer)
        
    Returns:
        An expression that returns the standardized chain name for the given chain ID,
        or NULL if the chain ID is not recognized
    """
    return exp.Case(
        ifs=[
            exp.If(
                this=exp.EQ(this=chain_id, expression=exp.Literal.number(1)),
                true=exp.Literal.string("MAINNET"),
            ),
            exp.If(
                this=exp.EQ(this=chain_id, expression=exp.Literal.number(10)),
                true=exp.Literal.string("OPTIMISM"),
            ),
            exp.If(
                this=exp.EQ(this=chain_id, expression=exp.Literal.number(324)),
                true=exp.Literal.string("ZKSYNC_ERA"),
            ),
            exp.If(
                this=exp.EQ(this=chain_id, expression=exp.Literal.number(43114)),
                true=exp.Literal.string("AVALANCHE"),
            ),
            exp.If(
                this=exp.EQ(this=chain_id, expression=exp.Literal.number(42220)),
                true=exp.Literal.string("CELO"),
            ),
            exp.If(
                this=exp.EQ(this=chain_id, expression=exp.Literal.number(424)),
                true=exp.Literal.string("PGN"),
            ),
            exp.If(
                this=exp.EQ(this=chain_id, expression=exp.Literal.number(8453)),
                true=exp.Literal.string("BASE"),
            ),
            exp.If(
                this=exp.EQ(this=chain_id, expression=exp.Literal.number(534352)),
                true=exp.Literal.string("SCROLL"),
            ),
            exp.If(
                this=exp.EQ(this=chain_id, expression=exp.Literal.number(1329)),
                true=exp.Literal.string("SEI"),
            ),
            exp.If(
                this=exp.EQ(this=chain_id, expression=exp.Literal.number(250)),
                true=exp.Literal.string("FANTOM"),
            ),
            exp.If(
                this=exp.EQ(this=chain_id, expression=exp.Literal.number(42)),
                true=exp.Literal.string("KOVAN"),
            ),
            exp.If(
                this=exp.EQ(this=chain_id, expression=exp.Literal.number(42161)),
                true=exp.Literal.string("ARBITRUM_ONE"),
            ),
            exp.If(
                this=exp.EQ(this=chain_id, expression=exp.Literal.number(137)),
                true=exp.Literal.string("MATIC"),
            ),
            exp.If(
                this=exp.EQ(this=chain_id, expression=exp.Literal.number(1088)),
                true=exp.Literal.string("METIS"),
            ),
        ],
        else_=exp.Null(),
    )
