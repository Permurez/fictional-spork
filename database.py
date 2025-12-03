"""
Database models for OLX iPhone listings scraper
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Listing(Base):
    """Model for storing iPhone listings from OLX"""
    __tablename__ = 'listings'
    
    id = Column(Integer, primary_key=True)
    olx_id = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    price = Column(Float)
    currency = Column(String, default='PLN')
    url = Column(String, nullable=False)
    location = Column(String)
    description = Column(String)
    posted_date = Column(DateTime)
    scraped_date = Column(DateTime, default=datetime.utcnow)
    notified = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Listing(olx_id='{self.olx_id}', title='{self.title}', price={self.price})>"


class ClientCriteria(Base):
    """Model for storing client notification criteria"""
    __tablename__ = 'client_criteria'
    
    id = Column(Integer, primary_key=True)
    client_name = Column(String, nullable=False)
    client_email = Column(String)
    min_price = Column(Float)
    max_price = Column(Float)
    keywords = Column(String)  # Comma-separated keywords
    location_filter = Column(String)
    active = Column(Boolean, default=True)
    created_date = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ClientCriteria(client_name='{self.client_name}', price_range={self.min_price}-{self.max_price})>"


class DatabaseManager:
    """Manager for database operations"""
    
    def __init__(self, database_url):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        """Get a new database session"""
        return self.Session()
    
    def add_listing(self, listing_data):
        """Add a new listing to the database"""
        session = self.get_session()
        try:
            # Check if listing already exists
            existing = session.query(Listing).filter_by(olx_id=listing_data['olx_id']).first()
            if existing:
                return None
            
            listing = Listing(**listing_data)
            session.add(listing)
            session.commit()
            session.refresh(listing)
            # Expunge so it can be used after session closes
            session.expunge(listing)
            return listing
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_unnotified_listings(self):
        """Get all listings that haven't been notified yet"""
        session = self.get_session()
        try:
            listings = session.query(Listing).filter_by(notified=False).all()
            # Expunge objects so they can be used after session closes
            for listing in listings:
                session.expunge(listing)
            return listings
        finally:
            session.close()
    
    def mark_as_notified(self, listing_id):
        """Mark a listing as notified"""
        session = self.get_session()
        try:
            listing = session.query(Listing).filter_by(id=listing_id).first()
            if listing:
                listing.notified = True
                session.commit()
        finally:
            session.close()
    
    def get_active_criteria(self):
        """Get all active client criteria"""
        session = self.get_session()
        try:
            criteria = session.query(ClientCriteria).filter_by(active=True).all()
            # Expunge objects so they can be used after session closes
            for criterion in criteria:
                session.expunge(criterion)
            return criteria
        finally:
            session.close()
    
    def add_client_criteria(self, criteria_data):
        """Add new client criteria"""
        session = self.get_session()
        try:
            criteria = ClientCriteria(**criteria_data)
            session.add(criteria)
            session.commit()
            session.refresh(criteria)
            criteria_id = criteria.id
            criteria_name = criteria.client_name
            return criteria_id, criteria_name
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
