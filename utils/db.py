from sqlalchemy.orm import Session
from contextlib import contextmanager
from models.models import engine, Pipeline
from copy import deepcopy

@contextmanager
def jdx_database_session_query_scope():
    session = Session(engine)
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class JDXDatabase(object):
    def __init__(self,
                 tablename='pipeline',
                 uri="postgresql+psycopg2://postgres:password@jdx-postgres:5432/jdx_reference_backend_application"):
        self.tablename = tablename
        self.uri = uri

    def get_pipeline_from_job_description(self, job_description_id):
        #  I dont' know why this is throwing an error, looks like
        # querying by uuid can be problematic
        #
        # pipeline_query = self.session.query(self.Pipeline)\
        #                              .filter_by(pipeline_id=job_description_id)
        # pipeline = pipeline_query.one()
        # for row in session.query(self.Pipeline).all():
        #     if job_description_id == vars(row)['pipeline_id']:
        #         return vars(row)
        # return pipeline

        with jdx_database_session_query_scope() as session:
            pipeline_query = session.query(Pipeline).filter_by(
                pipeline_id=job_description_id
            )
            pipeline = pipeline_query.one()
            pipeline_copy = deepcopy(pipeline)
            return pipeline_copy

    def get_raw_text_from_pipeline(self, pipeline_id):
        pipeline = self.get_pipeline_from_job_description(pipeline_id)
        with jdx_database_session_query_scope() as session:
            session.add(pipeline)
            return pipeline.file_text

    def get_context_object_json(self, pipeline_id):
        pipeline = self.get_pipeline_from_job_description(pipeline_id)

        with jdx_database_session_query_scope() as session:
            session.add(pipeline)
            return pipeline.context_object
