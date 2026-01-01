from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Image, Comment, User, ImageView
from datetime import datetime

notifications_bp = Blueprint('notifications', __name__)

# 읽지 않은 알림 개수
@notifications_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    try:
        current_user_id = int(get_jwt_identity())
        
        # 내가 올린 이미지들
        my_images = Image.query.filter_by(user_id=current_user_id).all()
        
        total_unread = 0
        for image in my_images:
            # 마지막 확인 시간
            last_view = ImageView.query.filter_by(
                image_id=image.id,
                user_id=current_user_id
            ).first()
            
            if last_view:
                # 마지막 확인 이후 댓글 수
                unread = Comment.query.filter(
                    Comment.image_id == image.id,
                    Comment.created_at > last_view.last_viewed_at,
                    Comment.user_id != current_user_id
                ).count()
            else:
                # 한 번도 확인 안 했으면 내 댓글 제외한 전체
                unread = Comment.query.filter(
                    Comment.image_id == image.id,
                    Comment.user_id != current_user_id
                ).count()
            
            total_unread += unread
        
        return jsonify({'count': total_unread}), 200
        
    except Exception as e:
        print(f"에러: {str(e)}")
        return jsonify({'message': '알림 개수 조회 실패'}), 500

# 읽지 않은 알림 목록
@notifications_bp.route('', methods=['GET'])
@jwt_required()
def get_notifications():
    try:
        current_user_id = int(get_jwt_identity())
        
        # 내가 올린 이미지들
        my_images = Image.query.filter_by(user_id=current_user_id).all()
        
        notifications = []
        
        for image in my_images:
            # 마지막 확인 시간
            last_view = ImageView.query.filter_by(
                image_id=image.id,
                user_id=current_user_id
            ).first()
            
            # 읽지 않은 댓글들
            if last_view:
                unread_comments = Comment.query.filter(
                    Comment.image_id == image.id,
                    Comment.created_at > last_view.last_viewed_at,
                    Comment.user_id != current_user_id
                ).order_by(Comment.created_at.desc()).all()
            else:
                unread_comments = Comment.query.filter(
                    Comment.image_id == image.id,
                    Comment.user_id != current_user_id
                ).order_by(Comment.created_at.desc()).all()
            
            # 알림 생성
            for comment in unread_comments:
                commenter = User.query.get(comment.user_id)
                notifications.append({
                    'id': f"{image.id}_{comment.id}",
                    'imageId': image.id,
                    'imageTitle': image.title,
                    'commentId': comment.id,
                    'commenterNickname': commenter.nickname if commenter else '알 수 없음',
                    'commentPreview': comment.content[:30] + '...' if len(comment.content) > 30 else comment.content,
                    'createdAt': comment.created_at.isoformat()
                })
        
        # 최신순 정렬
        notifications.sort(key=lambda x: x['createdAt'], reverse=True)
        
        # 최대 10개만
        notifications = notifications[:10]
        
        return jsonify({'notifications': notifications}), 200
        
    except Exception as e:
        print(f"에러: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': '알림 목록 조회 실패'}), 500