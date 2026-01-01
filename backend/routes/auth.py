from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from models import db, User

auth_bp = Blueprint('auth', __name__)

# 회원가입
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    username = data.get('username')
    nickname = data.get('nickname')
    email = data.get('email')
    password = data.get('password')
    
    # 입력 검증
    if not username or not email or not password:
        return jsonify({'message': '모든 필드를 입력해주세요.'}), 400
    
    # 중복 확인
    if User.query.filter_by(username=username).first():
        return jsonify({'message': '이미 존재하는 아이디입니다.'}), 400

    if User.query.filter_by(nickname=nickname).first():
        return jsonify({'message': '이미 존재하는 닉네임입니다.'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'message': '이미 존재하는 이메일입니다.'}), 400
    
    # 비밀번호 해싱
    hashed_password = generate_password_hash(password)
    
    # 새 사용자 생성
    new_user = User(
        username=username,
        nickname=nickname,
        email=email,
        password=hashed_password
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': '회원가입 성공!'}), 201

# 로그인
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    
    # 입력 검증
    if not username or not password:
        return jsonify({'message': '아이디와 비밀번호를 입력해주세요.'}), 400
    
    # 사용자 찾기
    user = User.query.filter_by(username=username).first()
    
    # 비밀번호 확인
    if not user or not check_password_hash(user.password, password):
        return jsonify({'message': '아이디 또는 비밀번호가 잘못되었습니다.'}), 401
    
    # JWT 토큰 생성
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'token': access_token,
        'user': {
            'id': user.id,
            'username': user.username,
            'nickname': user.nickname,
            'email': user.email
        }
    }), 200

@auth_bp.route('/find-username', methods=['POST'])
def find_username():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'message': '이메일을 입력해주세요.'}), 400
        
        # 이메일로 사용자 찾기
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({'message': '해당 이메일로 가입된 계정이 없습니다.'}), 404
        
        # 아이디 일부 마스킹 (선택사항)
        # 예: "testuser" → "test***"
        username = user.username
        if len(username) > 4:
            masked_username = username[:4] + '*' * (len(username) - 4)
        else:
            masked_username = username[0] + '*' * (len(username) - 1)
        
        return jsonify({
            'message': '아이디를 찾았습니다.',
            'username': user.username,  # 전체 아이디
            'maskedUsername': masked_username,  # 마스킹된 아이디
            'nickname': user.nickname
        }), 200
        
    except Exception as e:
        print(f"에러: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': '아이디 찾기에 실패했습니다.'}), 500