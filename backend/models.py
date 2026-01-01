from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

db = SQLAlchemy()

KST = pytz.timezone('Asia/Seoul')

def get_kst_now():
    """한국 시간 반환 함수"""
    return datetime.now(KST)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    nickname = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=get_kst_now)
    
    images = db.relationship('Image', backref='user', lazy=True)
    comments = db.relationship('Comment', backref='user', lazy=True)
    reactions = db.relationship('Reaction', backref='user', lazy=True)
    image_views = db.relationship('ImageView', backref='user', lazy=True)

class Image(db.Model):
    __tablename__ = 'images'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=get_kst_now)
    updated_at = db.Column(db.DateTime, default=get_kst_now, onupdate=get_kst_now)

    comments = db.relationship('Comment', backref='image', lazy=True, cascade='all, delete-orphan')
    reactions = db.relationship('Reaction', backref='image', lazy=True, cascade='all, delete-orphan')
    views = db.relationship('ImageView', backref='image', lazy=True, cascade='all, delete-orphan')

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    image_id = db.Column(db.Integer, db.ForeignKey('images.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=get_kst_now)

class Reaction(db.Model):
    __tablename__ = 'reactions'
    
    id = db.Column(db.Integer, primary_key=True)
    emoji = db.Column(db.String(10), nullable=False)  # 👍, 😂, 😍, 😮 등
    image_id = db.Column(db.Integer, db.ForeignKey('images.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=get_kst_now)

    # 한 사용자가 같은 이미지에 같은 이모티콘은 한 번만
    __table_args__ = (db.UniqueConstraint('emoji', 'image_id', 'user_id', name='unique_reaction'),)


class ImageView(db.Model):
    __tablename__ = 'image_views'
    
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('images.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    last_viewed_at = db.Column(db.DateTime, default=get_kst_now, onupdate=get_kst_now)
    
    # 한 사용자가 한 이미지는 하나의 기록만
    __table_args__ = (db.UniqueConstraint('image_id', 'user_id', name='unique_view'),)