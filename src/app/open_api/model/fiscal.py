from sqlalchemy import BigInteger, Double, Index, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.models.base import Base


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
