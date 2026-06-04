import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base


TEST_DB_URL = "mysql+pymysql://root:password@localhost:3306/auto_train_test"


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_DB_URL, pool_pre_ping=True)
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture
def db_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()