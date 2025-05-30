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
        exp.EQ(this=chain_id, expression=exp.Literal.number(324)),
        exp.Literal.string("zksync_era"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(43114)),
        exp.Literal.string("avalanche"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(42220)),
        exp.Literal.string("celo"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(424)),
        exp.Literal.string("pgn"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(8453)),
        exp.Literal.string("base"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(534352)),
        exp.Literal.string("scroll"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(1329)),
        exp.Literal.string("sei"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(250)),
        exp.Literal.string("fantom"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(42)),
        exp.Literal.string("kovan"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(42161)),
        exp.Literal.string("arbitrum_one"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(137)),
        exp.Literal.string("matic"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(1088)),
        exp.Literal.string("metis"),
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
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(690)),
        exp.Literal.string("redstone"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(7560)),
        exp.Literal.string("cyber"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(5112)),
        exp.Literal.string("ham"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(291)),
        exp.Literal.string("orderly"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(252)),
        exp.Literal.string("frax"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(255)),
        exp.Literal.string("kroma"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(2702128)),
        exp.Literal.string("xterio"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(130)),
        exp.Literal.string("unichain"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(65536)),
        exp.Literal.string("automata"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(957)),
        exp.Literal.string("lyra"),
    ).when(
        exp.EQ(this=chain_id, expression=exp.Literal.number(254)),
        exp.Literal.string("swan"),
    )

    return exp.Upper(this=chain_name)