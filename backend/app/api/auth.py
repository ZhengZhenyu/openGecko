import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_current_active_superuser
from app.core.logging import get_logger
from app.core.rate_limit import limiter
from app.core.security import create_access_token, verify_password, get_password_hash
from app.config import settings
from app.database import get_db
from app.models import User
from app.models.password_reset import PasswordResetToken
from app.schemas import (
    LoginRequest, Token, UserCreate, UserUpdate, UserOut, UserInfoResponse,
    InitialSetupRequest, PasswordResetRequest,
    PasswordResetConfirm, SystemStatusResponse,
)

router = APIRouter()

logger = get_logger(__name__)


@router.get("/status", response_model=SystemStatusResponse)
def get_system_status(db: Session = Depends(get_db)):
    """
    Check if the system needs initial setup.
    Returns True if only the default admin exists (no real admin has been created).
    """
    default_admin = db.query(User).filter(User.is_default_admin == True).first()  # noqa: E712
    if default_admin:
        return SystemStatusResponse(
            needs_setup=True,
            message="系统需要初始化设置，请使用默认管理员账号登录并创建新管理员。",
        )
    return SystemStatusResponse(
        needs_setup=False,
        message="系统已完成初始化设置。",
    )


@router.post("/login", response_model=Token)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
def login(request: Request, login_request: LoginRequest, db: Session = Depends(get_db)):
    """
    User login endpoint.
    If the logged-in user is the default admin, the response will include
    is_default_admin=True to prompt the frontend to redirect to initial setup.
    """
    # Find user by username
    user = db.query(User).filter(User.username == login_request.username).first()

    # Verify user exists and password is correct
    if not user or not verify_password(login_request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )

    # Create access token
    access_token = create_access_token(data={"sub": user.username})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "is_default_admin": user.is_default_admin,
    }


@router.post("/setup", response_model=Token)
def initial_setup(
    setup_request: InitialSetupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Initial setup endpoint: Create a new admin account and delete the default admin.
    Only the default admin can call this endpoint.
    """
    # Only the default admin can perform initial setup
    if not current_user.is_default_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有默认管理员账号可以执行初始化设置",
        )

    # Validate: new username cannot be the same as the default admin
    if setup_request.username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新管理员用户名不能与默认管理员相同",
        )

    # Check if username already exists
    existing_user = db.query(User).filter(User.username == setup_request.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该用户名已被注册",
        )

    # Check if email already exists
    existing_email = db.query(User).filter(User.email == setup_request.email).first()
    if existing_email and existing_email.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册",
        )

    # Create the new admin account
    hashed_password = get_password_hash(setup_request.password)
    new_admin = User(
        username=setup_request.username,
        email=setup_request.email,
        full_name=setup_request.full_name,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=True,
        is_default_admin=False,
    )
    db.add(new_admin)
    db.flush()  # Get new_admin.id

    # Delete the default admin account
    db.delete(current_user)

    db.commit()
    db.refresh(new_admin)

    # Create a new token for the new admin
    access_token = create_access_token(data={"sub": new_admin.username})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "is_default_admin": False,
    }


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(
    user_create: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
):
    """
    User registration endpoint. Only superusers can create new users.
    Superusers can optionally create other superusers.

    Note: In production, you may want to require admin approval.
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_create.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_create.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Only superusers can create superuser accounts
    # Regular users will always have is_superuser=False
    is_superuser = user_create.is_superuser if current_user.is_superuser else False

    # Create new user
    hashed_password = get_password_hash(user_create.password)
    new_user = User(
        username=user_create.username,
        email=user_create.email,
        full_name=user_create.full_name,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=is_superuser,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get("/me", response_model=UserInfoResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get current user information and their accessible communities with roles.
    """
    from app.core.dependencies import get_user_community_role
    from app.schemas.community import CommunityWithRole
    from app.models.community import Community

    # Superusers can see all communities
    if current_user.is_superuser:
        communities = db.query(Community).all()
    else:
        communities = current_user.communities

    # Build communities with roles
    communities_with_roles = []
    for community in communities:
        role = get_user_community_role(current_user, community.id, db)
        communities_with_roles.append(
            CommunityWithRole(
                id=community.id,
                name=community.name,
                slug=community.slug,
                url=community.url,
                logo_url=community.logo_url,
                is_active=community.is_active,
                role=role or "user",
            )
        )
    
    return UserInfoResponse(
        user=current_user,
        communities=communities_with_roles
    )


@router.get("/users", response_model=list[UserOut])
def list_all_users(
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """
    List all users in the system.
    Only superusers can list all users.
    """
    users = db.query(User).filter(User.is_default_admin == False).order_by(User.id).all()  # noqa: E712
    return users


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """
    Update a user's information. Only superusers can update users.
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    # Prevent demoting yourself
    if user_update.is_superuser is False and target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能取消自己的超级管理员权限",
        )

    # Prevent demoting the last superuser
    if user_update.is_superuser is False and target_user.is_superuser:
        superuser_count = db.query(User).filter(
            User.is_superuser == True, User.is_default_admin == False  # noqa: E712
        ).count()
        if superuser_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能取消最后一个超级管理员的权限",
            )

    # Check email uniqueness if updating email
    if user_update.email is not None:
        existing = db.query(User).filter(
            User.email == user_update.email, User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被其他用户使用",
            )

    # Apply updates
    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data:
        target_user.hashed_password = get_password_hash(update_data.pop("password"))
    for field, value in update_data.items():
        setattr(target_user, field, value)

    db.commit()
    db.refresh(target_user)
    return target_user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """
    Delete a user. Only superusers can delete users.
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    # Cannot delete yourself
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己的账号",
        )

    # Cannot delete the last superuser
    if target_user.is_superuser:
        superuser_count = db.query(User).filter(
            User.is_superuser == True, User.is_default_admin == False  # noqa: E712
        ).count()
        if superuser_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除最后一个超级管理员",
            )

    db.delete(target_user)
    db.commit()


@router.post("/password-reset/request", status_code=status.HTTP_200_OK)
def request_password_reset(
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    """
    Request a password reset. Generates a reset token.
    If SMTP is configured, sends an email; otherwise returns the token directly
    (for development/testing).
    """
    user = db.query(User).filter(User.email == reset_request.email).first()
    if not user:
        # Don't reveal whether the email exists
        return {"message": "如果该邮箱已注册，您将收到密码重置邮件。"}

    # Don't allow password reset for default admin
    if user.is_default_admin:
        return {"message": "如果该邮箱已注册，您将收到密码重置邮件。"}

    # Invalidate any existing unused tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used == False,  # noqa: E712
    ).update({"used": True})

    # Generate a new reset token
    token_value = secrets.token_urlsafe(48)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token_value,
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    db.add(reset_token)
    db.commit()

    # Try to send email if SMTP is configured
    if settings.SMTP_HOST and settings.SMTP_USER:
        try:
            _send_password_reset_email(user.email, token_value)
            return {"message": "如果该邮箱已注册，您将收到密码重置邮件。"}
        except Exception as e:
            logger.warning("发送密码重置邮件失败", extra={"email": user.email, "error": str(e)})
            # Fall through to return token directly in dev mode

    # In development mode (no SMTP), return the token directly
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token_value}"
    return {
        "message": "密码重置链接已生成（开发模式）。",
        "reset_url": reset_url,
        "token": token_value,
    }


@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
def confirm_password_reset(
    reset_confirm: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    """
    Confirm a password reset using the token and set a new password.
    """
    # Find the token
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == reset_confirm.token,
    ).first()

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的密码重置令牌",
        )

    if not reset_token.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码重置令牌已过期或已使用",
        )

    # Update the user's password
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    user.hashed_password = get_password_hash(reset_confirm.new_password)
    reset_token.used = True

    db.commit()

    return {"message": "密码已成功重置，请使用新密码登录。"}


def _send_password_reset_email(to_email: str, token: str) -> None:
    """Send a password reset email via SMTP."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{settings.APP_NAME} - 密码重置"
    msg["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
    msg["To"] = to_email

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #409eff;">{settings.APP_NAME} 密码重置</h2>
        <p>您好，</p>
        <p>我们收到了您的密码重置请求。请点击下方链接重置密码：</p>
        <p style="margin: 20px 0;">
            <a href="{reset_url}"
               style="background-color: #409eff; color: white; padding: 12px 24px;
                      text-decoration: none; border-radius: 4px; display: inline-block;">
                重置密码
            </a>
        </p>
        <p>此链接将在 1 小时后过期。</p>
        <p>如果您没有请求密码重置，请忽略此邮件。</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #999; font-size: 12px;">此邮件由 {settings.APP_NAME} 系统自动发送，请勿回复。</p>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(msg["From"], [to_email], msg.as_string())

