from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from apex_flow.config import settings

Base = declarative_base()

class Dataset(Base):
    __tablename__ = 'datasets'
    
    id = Column(Integer, primary_key=True)
    season = Column(Integer, index=True)
    race = Column(String, index=True)
    session = Column(String, index=True)
    name = Column(String, unique=True) # Unique identifier logic
    created_at = Column(DateTime, default=datetime.utcnow)
    
    versions = relationship("DatasetVersion", back_populates="dataset")

class DatasetVersion(Base):
    __tablename__ = 'dataset_versions'
    
    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey('datasets.id'))
    dvc_hash = Column(String, nullable=False)
    git_sha = Column(String, nullable=True)
    tags = Column(JSON, nullable=True) # Store weather, track status here
    created_at = Column(DateTime, default=datetime.utcnow)
    path = Column(String)
    
    dataset = relationship("Dataset", back_populates="versions")

class MetadataRegistry:
    def __init__(self, db_url="sqlite:///apexflow_metadata.db"):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def register_dataset(self, season, race, session, path):
        session_db = self.Session()
        name = f"{season}_{race}_{session}"
        
        dataset = session_db.query(Dataset).filter_by(name=name).first()
        if not dataset:
            dataset = Dataset(season=season, race=race, session=session, name=name)
            session_db.add(dataset)
            session_db.commit()
            session_db.refresh(dataset)
        
        session_db.close()
        return dataset.id

    def register_version(self, dataset_id, dvc_hash, git_sha, path, tags=None):
        session_db = self.Session()
        version = DatasetVersion(
            dataset_id=dataset_id,
            dvc_hash=dvc_hash,
            git_sha=git_sha,
            path=str(path),
            tags=tags or {}
        )
        session_db.add(version)
        session_db.commit()
        session_db.close()

    def get_latest_version(self, season, race, session):
        # Implementation of search
        pass

registry = MetadataRegistry()
