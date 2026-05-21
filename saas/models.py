#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modelos SQLAlchemy — usuários, acessos, planos e histórico de cálculos."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TenantUser(Base):
    __tablename__ = "tenant_users"

    id_usuario: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    plano_assinatura: Mapped[str] = mapped_column(String(64), default="free", nullable=False)
    ativo: Mapped[bool] = mapped_column(default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    acessos: Mapped[list["AccessLog"]] = relationship(back_populates="usuario")
    calculos: Mapped[list["CalculationHistory"]] = relationship(back_populates="usuario")


class AccessLog(Base):
    __tablename__ = "access_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("tenant_users.id_usuario"), index=True)
    data_acesso: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)
    pagina: Mapped[str] = mapped_column(String(128), default="demo_calculo")
    ip_cliente: Mapped[str] = mapped_column(String(64), default="")

    usuario: Mapped["TenantUser"] = relationship(back_populates="acessos")


class CalculationHistory(Base):
    __tablename__ = "historico_calculos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("tenant_users.id_usuario"), index=True)
    data_calculo: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)
    modo: Mapped[str] = mapped_column(String(64), default="caixa_preta")
    plano_no_momento: Mapped[str] = mapped_column(String(64), default="free")
    entrada_json: Mapped[str] = mapped_column(Text, default="{}")
    resultado_json: Mapped[str] = mapped_column(Text, default="{}")
    sucesso: Mapped[bool] = mapped_column(default=True)
    mensagem_erro: Mapped[str] = mapped_column(Text, default="")

    usuario: Mapped["TenantUser"] = relationship(back_populates="calculos")


def create_engine_from_url(database_url: str):
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(database_url, echo=False, connect_args=connect_args)


def init_db(engine) -> None:
    Base.metadata.create_all(bind=engine)
