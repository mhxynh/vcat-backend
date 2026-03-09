from utils.auth_utils import AuthUtils
from utils.db_utils import DbUtils
from utils.logger import Logger


class UserResolver:
    """
    Resolves a Cognito-authenticated user to a database user_id.

    Flow:
    1. Extract `sub` and `email` from Cognito claims
    2. Look up by cognito_sub → return user_id if found
    3. Look up by email → link cognito_sub and return user_id
    4. Auto-provision a new user row if neither match
    """

    @staticmethod
    def resolve(event):
        """
        Returns the DB user_id for the authenticated Cognito user,
        or None if claims cannot be extracted.
        """
        claims = AuthUtils.get_user_claims(event)
        cognito_sub = claims.get("sub")
        email = (
            claims.get("email")
            or claims.get("cognito:email")
            or claims.get("preferred_username")
        )

        Logger.log(
            level="INFO",
            message="UserResolver: extracted claims",
            extra_fields={
                "cognito_sub": cognito_sub,
                "email": email,
                "claim_keys": list(claims.keys()) if claims else [],
            },
        )

        if not cognito_sub and not email:
            Logger.log(level="WARNING", message="UserResolver: no sub or email in claims")
            return None

        conn = DbUtils.get_db_connection()
        try:
            with conn.cursor() as cur:
                # 1. Look up by cognito_sub
                if cognito_sub:
                    cur.execute(
                        "SELECT user_id FROM users WHERE cognito_sub = %s",
                        (cognito_sub,),
                    )
                    row = cur.fetchone()
                    if row:
                        return row["user_id"]

                # 2. Look up by email and link cognito_sub
                if email:
                    cur.execute(
                        "SELECT user_id, cognito_sub FROM users WHERE email = %s",
                        (email,),
                    )
                    row = cur.fetchone()
                    if row:
                        if cognito_sub and not row["cognito_sub"]:
                            cur.execute(
                                "UPDATE users SET cognito_sub = %s WHERE user_id = %s",
                                (cognito_sub, row["user_id"]),
                            )
                            conn.commit()
                        return row["user_id"]

                # 3. Auto-provision new user
                if email:
                    role = UserResolver._resolve_role(event)
                    display_name = UserResolver._resolve_display_name(claims, email)
                    Logger.log(
                        level="INFO",
                        message="UserResolver: auto-provisioning new user",
                        extra_fields={"email": email, "role": role, "display_name": display_name},
                    )
                    cur.execute(
                        """
                        INSERT INTO users (cognito_sub, email, role, display_name)
                        VALUES (%s, %s, %s, %s)
                        RETURNING user_id
                        """,
                        (cognito_sub, email, role, display_name),
                    )
                    user_id = cur.fetchone()["user_id"]
                    conn.commit()
                    Logger.log(
                        level="INFO",
                        message="Auto-provisioned user from Cognito",
                        extra_fields={"user_id": user_id, "email": email},
                    )
                    return user_id

            return None
        except Exception as e:
            Logger.log(
                level="ERROR",
                message="Error resolving user",
                extra_fields={"error": str(e), "cognito_sub": cognito_sub, "email": email},
            )
            return None
        finally:
            conn.close()

    @staticmethod
    def _resolve_role(event):
        """Map Cognito groups to DB role. Default to TESTER."""
        if AuthUtils.is_manager(event):
            return "MANAGER"
        return "TESTER"

    @staticmethod
    def _resolve_display_name(claims, email):
        """Extract display name from claims, fall back to email prefix."""
        name = claims.get("name") or claims.get("cognito:username") or claims.get("preferred_username")
        if name:
            return name
        return email.split("@")[0]
