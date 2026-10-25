"""Small educational REST API demonstrating common security controls."""
from __future__ import annotations

import html
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Callable

import jwt
from flask import Flask, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=os.environ.get("DATABASE_PATH", str(Path(__file__).with_name("app.db"))),
        JWT_SECRET=os.environ.get("JWT_SECRET"),
        JWT_ISSUER="work1-secure-api",
        JWT_TTL_MINUTES=30,
    )
    if test_config:
        app.config.update(test_config)
    if not app.config["JWT_SECRET"]:
        raise RuntimeError("Set JWT_SECRET to a high-entropy secret before starting the API")

    def db() -> sqlite3.Connection:
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_error: BaseException | None = None) -> None:
        connection = g.pop("db", None)
        if connection is not None:
            connection.close()

    def init_db() -> None:
        with closing(sqlite3.connect(app.config["DATABASE"])) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL
                );
                """
            )
            if connection.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
                connection.execute(
                    "INSERT INTO users(username, password_hash) VALUES (?, ?)",
                    ("student", generate_password_hash("ChangeMe123!", method="scrypt")),
                )
            if connection.execute("SELECT COUNT(*) FROM posts").fetchone()[0] == 0:
                connection.execute(
                    "INSERT INTO posts(title, body) VALUES (?, ?)",
                    ("Welcome", "Authenticated sample data."),
                )
            connection.commit()

    init_db()

    def issue_token(username: str) -> str:
        now = datetime.now(timezone.utc)
        return jwt.encode(
            {
                "sub": username,
                "iss": app.config["JWT_ISSUER"],
                "iat": now,
                "exp": now + timedelta(minutes=app.config["JWT_TTL_MINUTES"]),
            },
            app.config["JWT_SECRET"],
            algorithm="HS256",
        )

    def token_required(view: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(view)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            value = request.headers.get("Authorization", "")
            scheme, _, token = value.partition(" ")
            if scheme.lower() != "bearer" or not token:
                return jsonify(error="Bearer token required"), 401
            try:
                claims = jwt.decode(
                    token,
                    app.config["JWT_SECRET"],
                    algorithms=["HS256"],
                    issuer=app.config["JWT_ISSUER"],
                    options={"require": ["exp", "iat", "iss", "sub"]},
                )
            except jwt.PyJWTError:
                return jsonify(error="Invalid or expired token"), 401
            g.current_user = claims["sub"]
            return view(*args, **kwargs)

        return wrapped

    @app.post("/auth/login")
    def login() -> Any:
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="JSON object required"), 400
        username, password = payload.get("login"), payload.get("password")
        if not isinstance(username, str) or not isinstance(password, str):
            return jsonify(error="login and password must be strings"), 400
        # Bound input size to avoid unnecessary work on attacker-controlled values.
        if len(username) > 128 or len(password) > 256:
            return jsonify(error="Credentials are too long"), 400
        user = db().execute(
            "SELECT username, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if user is None or not check_password_hash(user["password_hash"], password):
            return jsonify(error="Invalid credentials"), 401
        # Bandit B105 treats the standard HTTP auth-scheme label as a password.
        response = {"access_token": issue_token(user["username"]), "token_type": "Bearer"}  # nosec B105
        return jsonify(response), 200

    @app.get("/api/data")
    @token_required
    def get_data() -> Any:
        rows = db().execute("SELECT id, title, body FROM posts ORDER BY id").fetchall()
        # JSON is not executable HTML, but escaping keeps reflected/stored markup inert
        # for clients that render these fields in an HTML context.
        return jsonify(
            user=g.current_user,
            data=[
                {
                    "id": row["id"],
                    "title": html.escape(row["title"], quote=True),
                    "body": html.escape(row["body"], quote=True),
                }
                for row in rows
            ],
        )

    @app.post("/api/posts")
    @token_required
    def create_post() -> Any:
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="JSON object required"), 400
        title, body = payload.get("title"), payload.get("body")
        if not isinstance(title, str) or not isinstance(body, str):
            return jsonify(error="title and body must be strings"), 400
        if not title.strip() or not body.strip() or len(title) > 200 or len(body) > 5000:
            return jsonify(error="Invalid title or body length"), 400
        cursor = db().execute(
            "INSERT INTO posts(title, body) VALUES (?, ?)", (title.strip(), body.strip())
        )
        db().commit()
        return jsonify(id=cursor.lastrowid, message="Post created"), 201

    @app.get("/health")
    def health() -> Any:
        return jsonify(status="ok")

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
