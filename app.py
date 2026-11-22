"""Portal académico de negocios y orientación para Gamarra."""

from __future__ import annotations

import os
import secrets
import sqlite3
from functools import wraps
from pathlib import Path

import click
from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'comerciante' CHECK(role IN ('comerciante', 'admin')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS businesses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    gallery TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pendiente' CHECK(status IN ('pendiente', 'publicado')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS guidance_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    topic TEXT NOT NULL,
    details TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pendiente' CHECK(status IN ('pendiente', 'revisada')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

CATEGORIES = ('Confección', 'Telas', 'Accesorios', 'Servicios', 'Otros')
TOPICS = ('Registro de negocio', 'Licencia municipal', 'Obligaciones tributarias', 'Orientación general')
GUIDE_STEPS = (
    ('Inscribir el negocio en el RUC', 'La inscripción y la elección del régimen tributario se gestionan ante la SUNAT.',
     'Portal de la SUNAT', 'https://www.sunat.gob.pe/'),
    ('Tramitar la licencia de funcionamiento', 'La licencia la otorga la municipalidad del distrito donde opera el negocio.',
     'Municipalidad de La Victoria', 'https://www.munilavictoria.gob.pe/'),
    ('Consultar trámites y requisitos del Estado', 'El portal único del Estado reúne la información oficial de trámites y servicios.',
     'Portal gob.pe', 'https://www.gob.pe/'),
)


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('GAMARRA_SECRET_KEY') or secrets.token_hex(32),
        DATABASE=str(Path(app.instance_path) / 'gamarra.sqlite3'),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.environ.get('GAMARRA_ENV') == 'production',
        MAX_CONTENT_LENGTH=32 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    if os.environ.get('GAMARRA_ENV') == 'production' and not os.environ.get('GAMARRA_SECRET_KEY'):
        raise RuntimeError('GAMARRA_SECRET_KEY es obligatoria en producción')
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    def db() -> sqlite3.Connection:
        if 'db' not in g:
            connection = sqlite3.connect(app.config['DATABASE'])
            connection.row_factory = sqlite3.Row
            connection.execute('PRAGMA foreign_keys = ON')
            g.db = connection
        return g.db

    @app.teardown_appcontext
    def close_db(_error: BaseException | None) -> None:
        connection = g.pop('db', None)
        if connection is not None:
            connection.close()

    with app.app_context():
        db().executescript(SCHEMA)
        db().commit()

    @app.before_request
    def load_user_and_check_csrf() -> None:
        user_id = session.get('user_id')
        g.user = db().execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone() if user_id else None
        if '_csrf' not in session:
            session['_csrf'] = secrets.token_urlsafe(32)
        if request.method == 'POST' and not secrets.compare_digest(
            str(request.form.get('_csrf', '')), session['_csrf']
        ):
            abort(400, 'Token de formulario inválido')

    @app.context_processor
    def template_context() -> dict:
        return {'csrf_token': session.get('_csrf'), 'categories': CATEGORIES}

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.user is None:
                flash('Inicia sesión para continuar.', 'warning')
                return redirect(url_for('login'))
            return view(*args, **kwargs)
        return wrapped

    def admin_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.user is None or g.user['role'] != 'admin':
                abort(403)
            return view(*args, **kwargs)
        return wrapped

    @app.get('/')
    def index():
        count = db().execute("SELECT COUNT(*) FROM businesses WHERE status = 'publicado'").fetchone()[0]
        return render_template('index.html', count=count)

    @app.route('/registro', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            if not name or len(name) > 100 or not email or len(email) > 254 or '@' not in email or len(password) < 10:
                flash('Completa los datos. La contraseña debe tener al menos 10 caracteres.', 'error')
            else:
                try:
                    with db():
                        db().execute(
                            'INSERT INTO users(name, email, password_hash) VALUES(?, ?, ?)',
                            (name, email, generate_password_hash(password)),
                        )
                except sqlite3.IntegrityError:
                    flash('Ese correo ya está registrado.', 'error')
                else:
                    flash('Cuenta creada. Ya puedes iniciar sesión.', 'success')
                    return redirect(url_for('login'))
        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            user = db().execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            if user is None or not check_password_hash(user['password_hash'], request.form.get('password', '')):
                flash('Credenciales incorrectas.', 'error')
            else:
                session.clear()
                session['user_id'] = user['id']
                session['_csrf'] = secrets.token_urlsafe(32)
                return redirect(url_for('admin') if user['role'] == 'admin' else url_for('my_business'))
        return render_template('login.html')

    @app.post('/logout')
    @login_required
    def logout():
        session.clear()
        return redirect(url_for('index'))

    @app.get('/negocios')
    def businesses():
        category = request.args.get('rubro', '').strip()
        query = request.args.get('q', '').strip()[:100]
        if category and category not in CATEGORIES:
            abort(400, 'Rubro inválido')
        sql = "SELECT id, name, category, description, gallery FROM businesses WHERE status = 'publicado'"
        args: list[str] = []
        if category:
            sql += ' AND category = ?'
            args.append(category)
        if query:
            sql += ' AND (name LIKE ? OR description LIKE ?)'
            args.extend((f'%{query}%', f'%{query}%'))
        sql += ' ORDER BY name COLLATE NOCASE'
        rows = db().execute(sql, args).fetchall()
        return render_template('businesses.html', businesses=rows, category=category, query=query)

    @app.get('/negocios/<int:business_id>')
    def business_detail(business_id: int):
        business = db().execute(
            "SELECT id, name, category, description, gallery FROM businesses WHERE id = ? AND status = 'publicado'",
            (business_id,),
        ).fetchone()
        if business is None:
            abort(404)
        return render_template('business_detail.html', business=business)

    @app.get('/guia')
    def formalization_guide():
        return render_template('guide.html', steps=GUIDE_STEPS)

    @app.route('/mi-negocio', methods=['GET', 'POST'])
    @login_required
    def my_business():
        business = db().execute('SELECT * FROM businesses WHERE owner_id = ?', (g.user['id'],)).fetchone()
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            category = request.form.get('category', '')
            description = request.form.get('description', '').strip()
            gallery = request.form.get('gallery', '').strip()
            if not name or len(name) > 120 or category not in CATEGORIES or not description or len(description) > 700 or not gallery or len(gallery) > 120:
                flash('Revisa los campos y sus longitudes.', 'error')
            else:
                with db():
                    if business:
                        db().execute(
                            "UPDATE businesses SET name=?, category=?, description=?, gallery=?, status='pendiente' WHERE owner_id=?",
                            (name, category, description, gallery, g.user['id']),
                        )
                    else:
                        db().execute(
                            'INSERT INTO businesses(owner_id, name, category, description, gallery) VALUES(?, ?, ?, ?, ?)',
                            (g.user['id'], name, category, description, gallery),
                        )
                flash('Perfil guardado y enviado a revisión.', 'success')
                return redirect(url_for('my_business'))
        return render_template('my_business.html', business=business)

    @app.route('/orientacion', methods=['GET', 'POST'])
    @login_required
    def guidance():
        if request.method == 'POST':
            topic = request.form.get('topic', '')
            details = request.form.get('details', '').strip()
            if topic not in TOPICS or not details or len(details) > 1000:
                flash('Elige un tema y describe tu consulta en hasta 1000 caracteres.', 'error')
            else:
                with db():
                    db().execute(
                        'INSERT INTO guidance_requests(user_id, topic, details) VALUES(?, ?, ?)',
                        (g.user['id'], topic, details),
                    )
                flash('Solicitud registrada.', 'success')
                return redirect(url_for('guidance'))
        rows = db().execute(
            'SELECT * FROM guidance_requests WHERE user_id = ? ORDER BY id DESC', (g.user['id'],)
        ).fetchall()
        return render_template('guidance.html', topics=TOPICS, requests=rows)

    @app.get('/admin')
    @admin_required
    def admin():
        pending = db().execute(
            "SELECT b.*, u.email FROM businesses b JOIN users u ON u.id=b.owner_id WHERE b.status='pendiente' ORDER BY b.id"
        ).fetchall()
        guidance_rows = db().execute(
            "SELECT r.*, u.email FROM guidance_requests r JOIN users u ON u.id=r.user_id WHERE r.status='pendiente' ORDER BY r.id"
        ).fetchall()
        counts = {
            'usuarios': db().execute('SELECT COUNT(*) FROM users').fetchone()[0],
            'negocios': db().execute('SELECT COUNT(*) FROM businesses').fetchone()[0],
            'publicados': db().execute("SELECT COUNT(*) FROM businesses WHERE status='publicado'").fetchone()[0],
            'solicitudes': db().execute('SELECT COUNT(*) FROM guidance_requests').fetchone()[0],
        }
        return render_template('admin.html', pending=pending, guidance_rows=guidance_rows, counts=counts)

    @app.post('/admin/negocios/<int:business_id>/publicar')
    @admin_required
    def publish_business(business_id: int):
        with db():
            result = db().execute("UPDATE businesses SET status='publicado' WHERE id=? AND status='pendiente'", (business_id,))
        if result.rowcount == 0:
            abort(404)
        flash('Negocio publicado.', 'success')
        return redirect(url_for('admin'))

    @app.post('/admin/solicitudes/<int:guidance_id>/revisar')
    @admin_required
    def review_guidance(guidance_id: int):
        with db():
            result = db().execute("UPDATE guidance_requests SET status='revisada' WHERE id=? AND status='pendiente'", (guidance_id,))
        if result.rowcount == 0:
            abort(404)
        flash('Solicitud marcada como revisada.', 'success')
        return redirect(url_for('admin'))

    @app.cli.command('create-admin')
    @click.argument('email')
    @click.option('--name', default='Administrador', help='Nombre mostrado')
    @click.password_option()
    def create_admin(email: str, name: str, password: str):
        """Crear una cuenta administrativa sin contraseñas predeterminadas."""
        if len(password) < 10:
            raise click.ClickException('La contraseña debe tener al menos 10 caracteres')
        try:
            with db():
                db().execute(
                    "INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,'admin')",
                    (name.strip(), email.strip().lower(), generate_password_hash(password)),
                )
        except sqlite3.IntegrityError as exc:
            raise click.ClickException('El correo ya existe') from exc
        click.echo('Administrador creado')

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=os.environ.get('GAMARRA_ENV') != 'production')
