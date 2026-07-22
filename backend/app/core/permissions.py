# app/core/permissions.py

def get_department_filter(user: dict):
    """
    Kullanıcının rolüne göre görmesi gereken departman filtresini döner.
    - hr veya superadmin ise filtre yok (None).
    - manager ise bağlı olduğu departman ismi döner.
    - Yetkisiz ise False döner.
    """
    role = user.get("role")
    if role in ("hr", "admin"):
        return None
    elif role == "manager":
        return user.get("department")
    return False

def can_delete_candidate(user: dict) -> bool:
    """Sadece superadmin aday silebilir."""
    return user.get("role") == "admin"

def can_manage_users(user: dict) -> bool:
    """Sadece superadmin sistem kullanıcısı (hr, manager) yönetebilir."""
    return user.get("role") == "admin"

def can_export(user: dict) -> bool:
    """Sadece hr ve superadmin veri dışa aktarabilir (export)."""
    return user.get("role") in ("hr", "admin")