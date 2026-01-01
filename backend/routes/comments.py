from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Comment, Image, User

comments_bp = Blueprint('comments', __name__)

# 특정 이미지의 댓글 목록 조회
@comments_bp.route('/image/<int:image_id>', methods=['GET'])
def get_comments(image_id):
    comments = Comment.query.filter_by(image_id=image_id).order_by(Comment.created_at.asc()).all()
    
    result = []
    for comment in comments:
        user = User.query.get(comment.user_id)

        result.append({
            'id': comment.id,
            'content': comment.content,
            'userId': comment.user_id,
            'username': user.nickname if user else '알 수 없음',
            'createdAt': comment.created_at.isoformat()
        })
    
    return jsonify({'comments': result}), 200

# 댓글 작성
@comments_bp.route('', methods=['POST'])
@jwt_required()
def create_comment():
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    content = data.get('content')
    image_id = data.get('imageId')
    
    if not content or not image_id:
        return jsonify({'message': '내용과 이미지 ID를 입력해주세요.'}), 400
    
    # 이미지 존재 확인
    image = Image.query.get_or_404(image_id)
    
    new_comment = Comment(
        content=content,
        image_id=image_id,
        user_id=current_user_id
    )
    
    db.session.add(new_comment)
    db.session.commit()

    user = User.query.get(current_user_id)
    
    return jsonify({
        'message': '댓글 작성 완료!',
        'comment': {
            'id': new_comment.id,
            'content': new_comment.content,
            'username': new_comment.user.username,
            'createdAt': new_comment.created_at.isoformat()
        }
    }), 201

# 댓글 삭제
@comments_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_comment(id):
    current_user_id = int(get_jwt_identity())
    comment = Comment.query.get_or_404(id)
    
    if comment.user_id != current_user_id:
        return jsonify({'message': '권한이 없습니다.'}), 403
    
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({'message': '댓글 삭제 완료!'}), 200