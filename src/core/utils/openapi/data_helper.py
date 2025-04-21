import polars as pl


def join(*df: pl.DataFrame, by: list[str]):
    table = df[0]
    for frame in df[1:]:
        columns = sorted(set(frame.columns) - set(col for col in table.columns if col not in by))
        table = table.join(frame.select(columns), on=by, how="left")
    return table


def cast_y_null_to_bool(df: pl.DataFrame):
    is_target = lambda col: col.drop_nulls().unique().len() == 1 and col.drop_nulls().unique()[0] == "Y"
    target = [col for col in df.columns if df[col].dtype == pl.Utf8 and is_target(df[col])]
    converted_df = [pl.when(pl.col(col) == "Y").then(True).otherwise(False).alias(col) for col in target]
    return df.with_columns(converted_df)
