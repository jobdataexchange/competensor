from jdxapi.app import DB
# import re
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, DateTime, Numeric, Column, func, Text, ForeignKey
from sqlalchemy.orm import validates
from sqlalchemy.dialects.postgresql import UUID
import datetime
from sqlalchemy import text as sa_text
import uuid


class FrameworkRecommendation(DB.Model):
    __tablename__ = 'framework_recommendation'

    framework_recommendation_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # We can do a join or just let the models tell us
    user_token = Column(
        UUID(as_uuid=True)
    )

    # The Numeric type is designed to receive data from a database type that is explicitly known to be a decimal type (e.g. DECIMAL, NUMERIC, others) and not a floating point type (e.g. FLOAT, REAL, others). If the database column on the server is in fact a floating-point type type, such as FLOAT or REAL, use the Float type or a subclass, otherwise numeric coercion between float/Decimal may or may not function as expected.
    value = Column(Numeric) # TODO I think this is an ID for the array, so it should be Integer
    valid_until = Column(DateTime)
    
    # Should be a FK
    # pipeline_id = Column(UUID(as_uuid=True))
    # job_description_id = Column(UUID(as_uuid=True))
    pipeline_id = Column(
        UUID(as_uuid=True)
        # ForeignKey('pipeline.pipeline_id')
    )
    
    # Types are actually ENUMs
    user_type = Column(String)
    object_type = Column(String)
    statistic_type = Column(String)
    metric_class = Column(String)
    
    # Extra info
    total_number = Column(Integer)
    recommended_content = Column(String)
    # job_description_id = Column(
    #     UUID(as_uuid=True),
    #     unique=True,
    #     # default = generate_uuid4
    #     default=uuid.uuid4
    # )
    # file_name = Column(String)
    # file_format = Column(String)  # optional?
    # file_text = Column(Text)

    # # define 'last_updated' to be populated with datetime.now()
    # last_updated = Column(
    #     DateTime,
    #     default=datetime.datetime.now,
    #     onupdate=datetime.datetime.now
    # )

    # def __repr__(self):
    #     return f'pipeline_id={self.pipeline_id}, user_token={self.user_token}, job_description_id={self.job_description_id}, file_name={self.file_name}, file_format={self.file_format}, file_text={self.file_text}, last_updated={self.last_updated}'
