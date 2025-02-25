from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def chain_id_to_chain_name(
    evaluator: MacroEvaluator,
    chain_id: exp.Expression,
):
    """
    Macro to translate chain_id to chain_name
    Note: we need to keep this synced with
    https://github.com/voteagora/op-atlas/blob/main/app/src/lib/oso.ts#L6
    https://github.com/opensource-observer/oss-directory/blob/main/src/resources/schema/blockchain-address.json
    """
    chain_name = exp.Case(
        ifs=[
            exp.If(
                this=exp.EQ(
                    this=chain_id,
                    expression=exp.Literal.number(1),
                ),
                true=exp.Literal.string("mainnet"),
            ),
        ],
        default=exp.cast(chain_id, "string"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(10)),
        exp.Literal.string("optimism"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(8453)),
        exp.Literal.string("base"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(34443)),
        exp.Literal.string("mode"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(480)),
        exp.Literal.string("worldchain"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(8008)),
        exp.Literal.string("polynomial"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(60808)),
        exp.Literal.string("bob"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(57073)),
        exp.Literal.string("ink"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(1135)),
        exp.Literal.string("lisk"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(1750)),
        exp.Literal.string("metal"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(185)),
        exp.Literal.string("mint"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(6805)),
        exp.Literal.string("race"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(360)),
        exp.Literal.string("shape"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(1868)),
        exp.Literal.string("soneium"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(1923)),
        exp.Literal.string("swell"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(7777777)),
        exp.Literal.string("zora"),
    )
    return exp.Upper(this=chain_name)