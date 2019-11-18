from jdxapi.app import DB
# import re
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, DateTime, Numeric, Column, func, Text, ForeignKey
from sqlalchemy.orm import validates, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text as sa_text
import uuid


class Framework(DB.Model):
    __tablename__ = 'framework'

    framework_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    framework_type_id = Column(Integer, ForeignKey('framework_type.framework_type_id'))
    framework_type = relationship("FrameworkType")

    framework_name = Column(String)
    framework_description = Column(String)
    framework_uri = Column(String)


class FrameworkType(DB.Model):
    __tablename__ = 'framework_type'

    framework_type_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    framework_type = Column(String)
