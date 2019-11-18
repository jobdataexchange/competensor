from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base


Base = automap_base()
uri = "postgresql+psycopg2://postgres:password@jdx-postgres:5432/jdx_reference_backend_application"
engine = create_engine(uri)
Base.prepare(engine, reflect=True)

Pipeline = Base.classes.pipeline
