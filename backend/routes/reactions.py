from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Reaction, Image, User
from sqlalchemy.exc import IntegrityError

reactions_bp = Blueprint('reactions', __name__)

# 특정 이미지의 반응 통계 조회
@reactions_bp.route('/image/<int:image_id>', methods=['GET'])
def get_reactions(image_id):
    reactions = Reaction.query.filter_by(image_id=image_id).all()
    
    # 이모티콘별 개수 집계
    reaction_counts = {}
    user_reactions = {}
    
    for reaction in reactions:
        emoji = reaction.emoji
        if emoji not in reaction_counts:
            reaction_counts[emoji] = []
        
        user = User.query.get(reaction.user_id)
        reaction_counts[emoji].append({
            'userId': reaction.user_id,
            'username': reaction.user.username
        })
    
    # 결과: {"👍": 4, "😂": 2, ...}
    result = {}
    for emoji, users in reaction_counts.items():
        result[emoji] = {
            'count': len(users),
            'users': users
        }
    
    return jsonify({'reactions': result}), 200

# 반응 추가/제거 (토글)
@reactions_bp.route('', methods=['POST'])
@jwt_required()
def toggle_reaction():
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    emoji = data.get('emoji')
    image_id = data.get('imageId')
    
    if not emoji or not image_id:
        return jsonify({'message': '이모티콘과 이미지 ID를 입력해주세요.'}), 400
    
    # 이미지 존재 확인
    image = Image.query.get_or_404(image_id)
    
    # 이미 반응했는지 확인
    existing = Reaction.query.filter_by(
        emoji=emoji,
        image_id=image_id,
        user_id=current_user_id
    ).first()
    
    if existing:
        # 이미 있으면 제거 (토글)
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'message': '반응 제거!', 'action': 'removed'}), 200
    else:
        # 없으면 추가
        new_reaction = Reaction(
            emoji=emoji,
            image_id=image_id,
            user_id=current_user_id
        )
        db.session.add(new_reaction)
        db.session.commit()
        return jsonify({'message': '반응 추가!', 'action': 'added'}), 201