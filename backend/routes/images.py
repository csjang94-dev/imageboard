from flask import Blueprint, request, jsonify, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from models import db, Image, User
import os
from datetime import datetime

images_bp = Blueprint('images', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# 파일 확장자 체크
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 모든 이미지 조회 (페이지네이션)
@images_bp.route('', methods=['GET'])
def get_all_images():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    images = Image.query.order_by(Image.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    result = []
    for image in images.items:
        result.append({
            'id': image.id,
            'title': image.title,
            'description': image.description,
            'imageUrl': f'http://localhost:5000/api/images/files/{image.image_url}',
            'userId': image.user_id,
            'username': image.user.username,
            'createdAt': image.created_at.isoformat()
        })
    
    return jsonify({
        'images': result,
        'totalPages': images.pages,
        'currentPage': page
    }), 200

# 이미지 검색
@images_bp.route('/search', methods=['GET'])
def search_images():
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'images': []}), 200
    
    images = Image.query.filter(
        Image.title.contains(query) | Image.description.contains(query)
    ).order_by(Image.created_at.desc()).all()
    
    result = []
    for image in images:
        result.append({
            'id': image.id,
            'title': image.title,
            'description': image.description,
            'imageUrl': f'http://localhost:5000/api/images/files/{image.image_url}',
            'userId': image.user_id,
            'username': image.user.username,
            'createdAt': image.created_at.isoformat()
        })
    
    return jsonify({'images': result}), 200

# 특정 이미지 조회
@images_bp.route('/<int:id>', methods=['GET'])
def get_image(id):
    image = Image.query.get_or_404(id)
    
    return jsonify({
        'id': image.id,
        'title': image.title,
        'description': image.description,
        'imageUrl': f'http://localhost:5000/api/images/files/{image.image_url}',
        'userId': image.user_id,
        'username': image.user.username,
        'createdAt': image.created_at.isoformat()
    }), 200

# 이미지 업로드
@images_bp.route('', methods=['POST'])
@jwt_required()
def upload_image():
    current_user_id = int(get_jwt_identity())
    
    # 파일 체크
    if 'image' not in request.files:
        return jsonify({'message': '이미지 파일이 없습니다.'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'message': '파일이 선택되지 않았습니다.'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'message': '허용되지 않는 파일 형식입니다.'}), 400
    
    # 파일 저장
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{timestamp}_{filename}"
    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(filepath)
    
    # 데이터베이스에 저장
    title = request.form.get('title')
    description = request.form.get('description', '')
    
    if not title:
        os.remove(filepath)  # 파일 삭제
        return jsonify({'message': '제목을 입력해주세요.'}), 400
    
    new_image = Image(
        title=title,
        description=description,
        image_url=unique_filename,
        user_id=current_user_id
    )
    
    db.session.add(new_image)
    db.session.commit()
    
    return jsonify({
        'message': '업로드 성공!',
        'image': {
            'id': new_image.id,
            'title': new_image.title,
            'imageUrl': f'http://localhost:5000/api/images/files/{unique_filename}'
        }
    }), 201

# 이미지 수정
@images_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_image(id):
    current_user_id = int(get_jwt_identity())
    image = Image.query.get_or_404(id)
    
    # 권한 체크
    if image.user_id != current_user_id:
        return jsonify({'message': '권한이 없습니다.'}), 403
    
    # 제목, 설명 업데이트
    title = request.form.get('title')
    description = request.form.get('description', '')
    
    if title:
        image.title = title
    if description:
        image.description = description
    
    # 새 이미지 파일이 있으면 교체
    if 'image' in request.files:
        file = request.files['image']
        
        if file.filename != '' and allowed_file(file.filename):
            # 기존 파일 삭제
            old_filepath = os.path.join(UPLOAD_FOLDER, image.image_url)
            if os.path.exists(old_filepath):
                os.remove(old_filepath)
            
            # 새 파일 저장
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(filepath)
            
            image.image_url = unique_filename
    
    db.session.commit()
    
    return jsonify({'message': '수정 완료!'}), 200

# 이미지 삭제
@images_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_image(id):
    current_user_id = int(get_jwt_identity())
    image = Image.query.get_or_404(id)
    
    # 권한 체크
    if image.user_id != current_user_id:
        return jsonify({'message': '권한이 없습니다.'}), 403
    
    # 파일 삭제
    filepath = os.path.join(UPLOAD_FOLDER, image.image_url)
    if os.path.exists(filepath):
        os.remove(filepath)
    
    # 데이터베이스에서 삭제
    db.session.delete(image)
    db.session.commit()
    
    return jsonify({'message': '삭제 완료!'}), 200

# 이미지 파일 서빙
@images_bp.route('/files/<filename>', methods=['GET'])
def serve_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)