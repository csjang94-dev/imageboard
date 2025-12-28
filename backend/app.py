from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db
import os

app = Flask(__name__)
app.config.from_object(Config)

# CORS 설정 (React와 통신하기 위해)
CORS(app, origins=['http://localhost:3000'])

# JWT 설정
jwt = JWTManager(app)

# JWT 에러 핸들러 추가
@jwt.unauthorized_loader
def unauthorized_callback(callback):
    return jsonify({
        'message': '로그인이 필요합니다. (토큰 없음)'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(callback):
    return jsonify({
        'message': '유효하지 않은 토큰입니다.'
    }), 422

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'message': '토큰이 만료되었습니다.'
    }), 401

# 데이터베이스 초기화
db.init_app(app)

if not os.path.exists('uploads'):
    os.makedirs('uploads')

from routes.auth import auth_bp
from routes.images import images_bp
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(images_bp, url_prefix='/api/images')

@app.route('/')
def index():
    return {'message': 'Image Board API'}

# 데이터베이스 테이블 생성
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)