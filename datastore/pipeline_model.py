from jdxapi.app import DB
# import re
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, DateTime, Numeric, Column, func, Text, and_, ForeignKey
from sqlalchemy.orm import validates, relationship
from sqlalchemy.dialects.postgresql import UUID
import datetime
from sqlalchemy import text as sa_text
import uuid
from sqlalchemy.dialects.postgresql import JSONB

junc_table = DB.Table('pipeline_framework_junc', DB.Model.metadata,
    Column('pipeline_id', UUID(as_uuid=True), ForeignKey('pipeline.pipeline_id')),
    Column('framework_id', UUID(as_uuid=True), ForeignKey('framework.framework_id'))
)

class Pipeline(DB.Model):
    __tablename__ = 'pipeline'

    pipeline_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        # default = generate_uuid4
        default=uuid.uuid4
    )
    user_token = Column(
        UUID(as_uuid=True),
        unique=True
    )

    frameworks = relationship(
        "Framework",
        secondary=junc_table
        # backref="pipelines"
    )

    # Future one-to-many?
    job_description_id = Column(
        UUID(as_uuid=True),
        unique=True,
        # default = generate_uuid4
        default=uuid.uuid4
    )
    file_name = Column(String)
    file_format = Column(String)  # optional?
    file_text = Column(Text)

    # define 'last_updated' to be populated with datetime.now()
    last_updated = Column(
        DateTime,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now
    )

    primary_economic_activity = Column(String)
    location_name = Column(String)
    location_description = Column(String)
    location_fax_number = Column(String)
    location_telephone = Column(String)
    location_address_name = Column(String)
    location_address_street_address = Column(String)
    location_address_locality = Column(String)
    location_address_region = Column(String)
    location_address_country = Column(String)
    location_address_postal_code = Column(Integer)
    location_geo_latitude = Column(Numeric)
    location_geo_longitude = Column(Numeric)
    
    occupation_category_name = Column(String)
    occupation_category_description = Column(String)
    occupation_category_term_code = Column(String)
    occupation_category_defined_term_set = Column(String)
    
    industry_category_name = Column(String)
    industry_category_description = Column(String)
    industry_category_term_code = Column(String)
    industry_category_defined_term_set = Column(String)
    
    competency_category_name = Column(String)
    competency_category_description = Column(String)
    competency_category_term_code = Column(String)
    competency_category_defined_term_set = Column(String)
    
    match_table_data = Column(JSONB)
    match_table_selections = Column(JSONB)

    def __repr__(self):
        return f'pipeline_id={self.pipeline_id}, user_token={self.user_token}, job_description_id={self.job_description_id}, file_name={self.file_name}, file_format={self.file_format}, file_text={self.file_text}, last_updated={self.last_updated}'

    # # This will be used once we have OAuth
    # def user_is_authorized_to_access_pipeline(user_token, pipeline_id):
    #     # When given a user token and pipeline, this will
    #     # return True or False if that user owns the pipleine id
    #     query = DB.session.query(Pipeline).filter(
    #         and_(
    #             Pipeline.user_token==user_token,
    #             Pipeline.pipeline_id==pipeline_id
    #         )
    #     )
    #     results = query.all()
    #     return not not results
