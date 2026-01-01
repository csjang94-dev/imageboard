from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Image, Comment, ImageView

users_bp = Blueprint('users', __name__)

# 내 프로필 조회
@users_bp.route('/me', methods=['GET'])
@jwt_required()
def get_my_profile():
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get_or_404(current_user_id)
        
        # 내가 올린 이미지 개수
        image_count = Image.query.filter_by(user_id=current_user_id).count()
        
        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username,
                'nickname': user.nickname,
                'email': user.email,
                'createdAt': user.created_at.isoformat(),
                'imageCount': image_count
            }
        }), 200
    except Exception as e:
        print(f"에러: {str(e)}")
        return jsonify({'message': '프로필을 불러오는데 실패했습니다.'}), 500

# 닉네임 수정
@users_bp.route('/me/nickname', methods=['PUT'])
@jwt_required()
def update_nickname():
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get_or_404(current_user_id)
        
        data = request.get_json()
        new_nickname = data.get('nickname')
        
        if not new_nickname or not new_nickname.strip():
            return jsonify({'message': '닉네임을 입력해주세요.'}), 400
        
        if len(new_nickname) > 20:
            return jsonify({'message': '닉네임은 20자 이하로 입력해주세요.'}), 400

        existing_user = User.query.filter_by(nickname=new_nickname).first()
        if existing_user and existing_user.id != current_user_id:
            return jsonify({'message': '이미 사용 중인 닉네임입니다.'}), 400
        
        user.nickname = new_nickname
        db.session.commit()
        
        return jsonify({
            'message': '닉네임이 변경되었습니다.',
            'nickname': user.nickname
        }), 200
    except Exception as e:
        print(f"에러: {str(e)}")
        return jsonify({'message': '닉네임 변경에 실패했습니다.'}), 500

# 내가 올린 이미지 목록
@users_bp.route('/me/images', methods=['GET'])
@jwt_required()
def get_my_images():
    try:
        current_user_id = int(get_jwt_identity())
        
        images = Image.query.filter_by(user_id=current_user_id)\
            .order_by(Image.created_at.desc()).all()
        
        result = []
        for image in images:

            total_comments = Comment.query.filter_by(image_id=image.id).count()
            last_view = ImageView.query.filter_by(
                image_id=image.id,
                user_id=current_user_id
            ).first()

            if last_view:
                # 마지막 확인 이후 댓글 수 (읽지 않은 댓글)
                unread_comments = Comment.query.filter(
                    Comment.image_id == image.id,
                    Comment.created_at > last_view.last_viewed_at,
                    Comment.user_id != current_user_id  # 내 댓글 제외
                ).count()
            else:
                # 한 번도 확인 안 했으면 내 댓글 제외한 전체
                unread_comments = Comment.query.filter(
                    Comment.image_id == image.id,
                    Comment.user_id != current_user_id
                ).count()

            result.append({
                'id': image.id,
                'title': image.title,
                'description': image.description,
                'imageUrl': f'http://localhost:5000/api/images/files/{image.image_url}',
                'createdAt': image.created_at.isoformat(),
                'totalComments': total_comments,
                'unreadComments': unread_comments
            })
        
        return jsonify({'images': result}), 200
    except Exception as e:
        print(f"에러: {str(e)}")
        return jsonify({'message': '이미지를 불러오는데 실패했습니다.'}), 500

@users_bp.route('/images/<int:image_id>/mark-viewed', methods=['POST'])
@jwt_required()
def mark_image_viewed(image_id):
    try:
        current_user_id = int(get_jwt_identity())
        
        # 이미지 존재 확인
        image = Image.query.get_or_404(image_id)
        
        # 본인 이미지가 아니면 처리 안 함
        if image.user_id != current_user_id:
            return jsonify({'message': '본인 이미지만 확인 가능합니다.'}), 403
        
        # 기존 기록 찾기
        view = ImageView.query.filter_by(
            image_id=image_id,
            user_id=current_user_id
        ).first()
        
        if view:
            # 이미 기록 있으면 시간 업데이트
            view.last_viewed_at = get_kst_now()
        else:
            # 없으면 새로 생성
            view = ImageView(
                image_id=image_id,
                user_id=current_user_id
            )
            db.session.add(view)
        
        db.session.commit()
        
        return jsonify({'message': '확인 완료'}), 200
    except Exception as e:
        print(f"에러: {str(e)}")
        return jsonify({'message': '처리 실패'}), 500  