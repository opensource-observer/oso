
from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def deps_parse_namespace(evaluator: MacroEvaluator, event_source: exp.Expression, artifact_name: exp.Expression):
    """
    Macro to parse the namespace from the artifact name based on the event source.
    Arguments:
        - event_source: The event source of the artifact.
        - artifact_name: The name of the artifact.
    Returns the namespace based on event source rules.
    """
    
    name = exp.Case(
        ifs=[
            exp.If(
                this=exp.And(
                    this=exp.EQ(
                        this=event_source,
                        expression=exp.Literal.string('NPM'),
                    ),
                    expression=exp.GT(
                        this=exp.StrPosition(
                            this=artifact_name,
                            substr=exp.Literal.string('/'),
                        ),
                        expression=exp.Literal.number(0),
                    ),
                ),
                true=exp.SplitPart(
                    this=exp.SplitPart(
                        this=artifact_name,
                        delimiter=exp.Literal.string('/'),
                        part_index=exp.Literal.number(1),
                    ),
                    delimiter=exp.Literal.string('@'),
                    part_index=exp.Literal.number(2),
                ),
            ),
            exp.If(
                this=exp.And(
                    this=exp.EQ(
                        this=event_source,
                        expression=exp.Literal.string('GO'),
                    ),
                    expression=exp.GT(
                        this=exp.StrPosition(
                            this=artifact_name,
                            substr=exp.Literal.string('/'),
                        ),
                        expression=exp.Literal.number(0),
                    ),
                ),
                true=exp.SplitPart(
                    this=artifact_name,
                    delimiter=exp.Literal.string('/'),
                    part_index=exp.Literal.number(2),
                ),
            ),
            exp.If(
                this=exp.EQ(
                    this=event_source,
                    expression=exp.Literal.string('MAVEN'),
                ),
                true=exp.SplitPart(
                    this=artifact_name,
                    delimiter=exp.Literal.string(':'),
                    part_index=exp.Literal.number(1),
                ),
            ),
            exp.If(
                this=exp.And(
                    this=exp.EQ(
                        this=event_source,
                        expression=exp.Literal.string('NUGET'),
                    ),
                    expression=exp.GT(
                        this=exp.StrPosition(
                            this=artifact_name,
                            substr=exp.Literal.string('.'),
                        ),
                        expression=exp.Literal.number(0),
                    ),
                ),
                true=exp.SplitPart(
                    this=artifact_name,
                    delimiter=exp.Literal.string('.'),
                    part_index=exp.Literal.number(1),
                ),
            ),
        ],
        default=artifact_name,
    )
    return name
    
@macro()
def deps_parse_name(evaluator: MacroEvaluator, event_source: exp.Expression, artifact_name: exp.Expression):
    """
    Macro to parse the name from the artifact name based on the event source.
    Arguments:
        - event_source: The event source of the artifact.
        - artifact_name: The name of the artifact.
    Returns the name based on event source rules.
    """
    name = exp.Case(
        ifs=[
            exp.If(
                this=exp.And(
                    this=exp.EQ(
                        this=event_source,
                        expression=exp.Literal.string('NPM'),
                    ),
                    expression=exp.GT(
                        this=exp.StrPosition(
                            this=artifact_name,
                            substr=exp.Literal.string('/'),
                        ),
                        expression=exp.Literal.number(0),
                    ),
                ),
                true=exp.SplitPart(
                    this=artifact_name,
                    delimiter=exp.Literal.string('/'),
                    part_index=exp.Literal.number(2),
                ),
            ),
            exp.If(
                this=exp.And(
                    this=exp.EQ(
                        this=event_source,
                        expression=exp.Literal.string('GO'),
                    ),
                    expression=exp.GT(
                        this=exp.StrPosition(
                            this=artifact_name,
                            substr=exp.Literal.string('/'),
                        ),
                        expression=exp.Literal.number(0),
                    ),
                ),
                true=exp.SplitPart(
                    this=artifact_name,
                    delimiter=exp.Literal.string('/'),
                    part_index=exp.Literal.number(3),
                ),
            ),
            exp.If(
                this=exp.EQ(
                    this=event_source,
                    expression=exp.Literal.string('MAVEN'),
                ),
                true=exp.SplitPart(
                    this=artifact_name,
                    delimiter=exp.Literal.string(':'),
                    part_index=exp.Literal.number(2),
                ),
            ),
            exp.If(
                this=exp.And(
                    this=exp.EQ(
                        this=event_source,
                        expression=exp.Literal.string('NUGET'),
                    ),
                    expression=exp.GT(
                        this=exp.StrPosition(
                            this=artifact_name,
                            substr=exp.Literal.string('.'),
                        ),
                        expression=exp.Literal.number(0),
                    ),
                ),
                true=exp.RegexpReplace(
                    this=artifact_name,
                    expression=exp.Literal.string(r'^[^.]+\.'), 
                    replacement=exp.Literal.string(''),
                ),
            ),
        ],
        default=artifact_name,
    )
    return name