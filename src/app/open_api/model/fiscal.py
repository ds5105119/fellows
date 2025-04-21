import polars as pl
from sqlalchemy import BigInteger, Double, Index, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.models.base import Base
from src.core.utils.openapi.data_saver import PostgresDataSaver

mappings = [
    ["문화재청", "국가유산청"],
    ["안전행정부", "행정자치부", "행정안전부"],
    ["미래창조과학부", "과학기술정보통신부"],
    ["국가보훈처", "국가보훈부"],
]


class FiscalDataSaver(PostgresDataSaver):
    def build(self):
        if not self.manager:
            raise RuntimeError("manager not set")

        df: pl.DataFrame = self.manager[0].data
        df = df.drop("ANEXP_INQ_STND_CD")
        df = df.with_columns(pl.col("OFFC_NM").fill_null("미정").alias("OFFC_NM"))

        department_no = {k: v for v, k in enumerate(sorted(set(df["OFFC_NM"])))}
        for mapping in mappings:
            min_no = min([department_no[name] for name in mapping if department_no.get(name)])
            department_no.update({name: min_no for name in mapping})

        df = df.with_columns(
            pl.col("FSCL_YY").str.to_integer().alias("FSCL_YY"),
            pl.col("OFFC_NM")
            .map_elements(lambda x: department_no.get(x, None), return_dtype=pl.Int8)
            .alias("NORMALIZED_DEPT_NO"),
        )

        df = df.sort(by=["FSCL_YY", "NORMALIZED_DEPT_NO", "Y_YY_MEDI_KCUR_AMT"], maintain_order=True)

        return df


class FiscalByYearDataSaver(PostgresDataSaver):
    def build(self):
        if not self.manager:
            raise RuntimeError("manager not set")

        df: pl.DataFrame = self.manager[0].data
        df = df.drop("ANEXP_INQ_STND_CD")
        df = df.with_columns(pl.col("OFFC_NM").fill_null("미정").alias("OFFC_NM"))

        department_no = {k: v for v, k in enumerate(sorted(set(df["OFFC_NM"])))}
        for mapping in mappings:
            min_no = min([department_no[name] for name in mapping if department_no.get(name)])
            department_no.update({name: min_no for name in mapping})

        df = df.with_columns(
            pl.col("FSCL_YY").str.to_integer().alias("FSCL_YY"),
            pl.col("OFFC_NM")
            .map_elements(lambda x: department_no.get(x, None), return_dtype=pl.Int8)
            .alias("NORMALIZED_DEPT_NO"),
        )

        df = (
            df.group_by("FSCL_YY")
            .agg(
                pl.col("Y_YY_MEDI_KCUR_AMT").sum().alias("Y_YY_MEDI_KCUR_AMT"),
                pl.col("Y_YY_DFN_MEDI_KCUR_AMT").sum().alias("Y_YY_DFN_MEDI_KCUR_AMT"),
            )
            .sort("FSCL_YY")
            .with_columns(pl.col("Y_YY_MEDI_KCUR_AMT").pct_change().alias("Y_YY_MEDI_KCUR_AMT_PCT"))
            .with_columns(pl.col("Y_YY_DFN_MEDI_KCUR_AMT").pct_change().alias("Y_YY_DFN_MEDI_KCUR_AMT_PCT"))
        )

        df = df.sort(by=["FSCL_YY", "Y_YY_MEDI_KCUR_AMT"], maintain_order=True)

        return df


class FiscalByYearOffcDataSaver(PostgresDataSaver):
    def build(self):
        if not self.manager:
            raise RuntimeError("manager not set")

        df: pl.DataFrame = self.manager[0].data
        df = df.drop("ANEXP_INQ_STND_CD")
        df = df.with_columns(pl.col("OFFC_NM").fill_null("미정").alias("OFFC_NM"))

        department_no = {k: v for v, k in enumerate(sorted(set(df["OFFC_NM"])))}
        for mapping in mappings:
            min_no = min([department_no[name] for name in mapping if department_no.get(name)])
            department_no.update({name: min_no for name in mapping})

        df = df.with_columns(
            pl.col("FSCL_YY").str.to_integer().alias("FSCL_YY"),
            pl.col("OFFC_NM")
            .map_elements(lambda x: department_no.get(x, None), return_dtype=pl.Int8)
            .alias("NORMALIZED_DEPT_NO"),
        )

        df = (
            df.group_by(["FSCL_YY", "NORMALIZED_DEPT_NO", "OFFC_NM"])
            .agg(
                pl.col("Y_YY_MEDI_KCUR_AMT").sum().alias("Y_YY_MEDI_KCUR_AMT"),
                pl.col("Y_YY_DFN_MEDI_KCUR_AMT").sum().alias("Y_YY_DFN_MEDI_KCUR_AMT"),
                pl.count().alias("COUNT"),
            )
            .sort(["NORMALIZED_DEPT_NO", "FSCL_YY"])
            .with_columns(
                pl.col("Y_YY_MEDI_KCUR_AMT").pct_change().over("NORMALIZED_DEPT_NO").alias("Y_YY_MEDI_KCUR_AMT_PCT")
            )
            .with_columns(
                pl.col("Y_YY_DFN_MEDI_KCUR_AMT")
                .pct_change()
                .over("NORMALIZED_DEPT_NO")
                .alias("Y_YY_DFN_MEDI_KCUR_AMT_PCT")
            )
        )

        df = df.sort(by=["FSCL_YY", "NORMALIZED_DEPT_NO", "Y_YY_MEDI_KCUR_AMT"], maintain_order=True)

        return df


class Fiscal(Base):
    __tablename__ = "open_fiscal"
    __table_args__ = (
        Index(
            "ix_for_open_fiscal_FSCL_YY",
            *("FSCL_YY",),
        ),
        Index(
            "ix_for_open_fiscal_NORMALIZED_DEPT_NO",
            *("OFFC_NM",),
        ),
        Index(
            "ix_for_open_fiscal_Y_YY_MEDI_KCUR_AMT",
            *("Y_YY_MEDI_KCUR_AMT",),
        ),
        Index(
            "ix_for_open_fiscal_Y_YY_DFN_MEDI_KCUR_AMT",
            *("Y_YY_DFN_MEDI_KCUR_AMT",),
        ),
        Index(
            "ix_for_open_fiscal_Fiscal_MEDI",
            *("FSCL_YY", "NORMALIZED_DEPT_NO", "Y_YY_MEDI_KCUR_AMT"),
        ),
        Index(
            "ix_for_open_fiscal_Fiscal_DFN",
            *("FSCL_YY", "NORMALIZED_DEPT_NO", "Y_YY_DFN_MEDI_KCUR_AMT"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    FSCL_YY: Mapped[str] = mapped_column(Integer)
    OFFC_NM: Mapped[str] = mapped_column(Text)
    NORMALIZED_DEPT_NO: Mapped[int] = mapped_column(Integer)
    FSCL_NM: Mapped[int] = mapped_column(Text)
    ACCT_NM: Mapped[str] = mapped_column(Text, nullable=True)
    FLD_NM: Mapped[str] = mapped_column(Text)
    SECT_NM: Mapped[str] = mapped_column(Text)
    PGM_NM: Mapped[str] = mapped_column(Text)
    ACTV_NM: Mapped[str] = mapped_column(Text)
    SACTV_NM: Mapped[str] = mapped_column(Text)
    BZ_CLS_NM: Mapped[str] = mapped_column(Text)
    FIN_DE_EP_NM: Mapped[str] = mapped_column(Text)
    Y_PREY_FIRST_KCUR_AMT: Mapped[int] = mapped_column(BigInteger, nullable=True)
    Y_PREY_FNL_FRC_AMT: Mapped[int] = mapped_column(BigInteger, nullable=True)
    Y_YY_MEDI_KCUR_AMT: Mapped[int] = mapped_column(BigInteger, nullable=True)
    Y_YY_DFN_MEDI_KCUR_AMT: Mapped[int] = mapped_column(BigInteger, nullable=True)


class FiscalByYear(Base):
    __tablename__ = "open_fiscal_by_year"
    __table_args__ = (
        Index(
            "ix_for_open_fiscal_by_year_FSCL_YY",
            *("FSCL_YY",),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    FSCL_YY: Mapped[int] = mapped_column(Integer)
    Y_YY_MEDI_KCUR_AMT: Mapped[int] = mapped_column(BigInteger, nullable=True)
    Y_YY_DFN_MEDI_KCUR_AMT: Mapped[int] = mapped_column(BigInteger, nullable=True)
    Y_YY_MEDI_KCUR_AMT_PCT: Mapped[int] = mapped_column(Double, nullable=True)
    Y_YY_DFN_MEDI_KCUR_AMT_PCT: Mapped[int] = mapped_column(Double, nullable=True)


class FiscalByYearOffc(Base):
    __tablename__ = "open_fiscal_by_year_offc"
    __table_args__ = (
        Index(
            "ix_for_open_fiscal_by_year_offc_FSCL_YY",
            *("FSCL_YY",),
        ),
        Index(
            "ix_for_open_fiscal_by_year_offc_OFFC_NM",
            *("OFFC_NM",),
        ),
        Index(
            "ix_for_open_fiscal_by_year_offc_Fiscal_MEDI",
            *("FSCL_YY", "NORMALIZED_DEPT_NO", "Y_YY_MEDI_KCUR_AMT"),
        ),
        Index(
            "ix_for_open_fiscal_by_year_offc_Fiscal_DFN",
            *("FSCL_YY", "NORMALIZED_DEPT_NO", "Y_YY_DFN_MEDI_KCUR_AMT"),
        ),
        Index(
            "ix_for_open_fiscal_by_year_offc_Fiscal_MEDI_PCT",
            *("FSCL_YY", "NORMALIZED_DEPT_NO", "Y_YY_MEDI_KCUR_AMT_PCT"),
        ),
        Index(
            "ix_for_open_fiscal_by_year_offc_Fiscal_DFN_PCT",
            *("FSCL_YY", "NORMALIZED_DEPT_NO", "Y_YY_DFN_MEDI_KCUR_AMT_PCT"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    FSCL_YY: Mapped[int] = mapped_column(Integer)
    OFFC_NM: Mapped[str] = mapped_column(Text)
    NORMALIZED_DEPT_NO: Mapped[int] = mapped_column(Integer)
    Y_YY_MEDI_KCUR_AMT: Mapped[int] = mapped_column(BigInteger, nullable=True)
    Y_YY_DFN_MEDI_KCUR_AMT: Mapped[int] = mapped_column(BigInteger, nullable=True)
    Y_YY_MEDI_KCUR_AMT_PCT: Mapped[int] = mapped_column(Double, nullable=True)
    Y_YY_DFN_MEDI_KCUR_AMT_PCT: Mapped[int] = mapped_column(Double, nullable=True)
    COUNT: Mapped[int] = mapped_column(Integer)
