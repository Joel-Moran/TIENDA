from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models.models import db, User, Carrito, Producto

app = Flask(__name__)
app.secret_key = "clave_secreta"

# Configuracion de base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tienda.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Configurar login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Crea la base de datos
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    productos = Producto.query.all()
    return render_template('index.html', productos=productos)

# Página de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        # Verificar si el correo ya existe
        existing_user = User.query.filter_by(correo=correo).first()
        if existing_user:
            flash('El correo ya está registrado.', 'warning')
            return redirect(url_for('register'))
        
        nuevo_usario = User(nombre=nombre, correo=correo, password=hashed_password)
        db.session.add(nuevo_usario)
        db.session.commit()
        flash('Registro exitoso. Inicia sesión ahora.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Página de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        password = request.form['password']
        user = User.query.filter_by(correo=correo).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Inicio de sesión exitoso.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Correo o contraseña incorrectos.', 'danger')
            return redirect(url_for('login'))
        
    return render_template('login.html')

@app.route('/agregar_carrito/<int:producto_id>')
@login_required
def agregar_carrito(producto_id):
    producto = Producto.query.get_or_404(producto_id)

    item = Carrito.query.filter_by(
        producto_id=producto.id,
        usuario_id=current_user.id
    ).first()

    if item:
        item.cantidad += 1
    else:
        nuevo_item = Carrito(
            producto_id=producto.id,
            usuario_id=current_user.id,
            cantidad=1
        )
        db.session.add(nuevo_item)

    db.session.commit()
    flash('Producto agregado al carrito 🛒', 'success')
    return redirect(url_for('home'))

@app.route('/carrito')
@login_required
def carrito():
    items = Carrito.query.filter_by(usuario_id=current_user.id).all()
    total = sum(item.producto.precio * item.cantidad for item in items)
    return render_template('carrito.html', items=items, total=total)

@app.route('/eliminar_carrito/<int:item_id>')
@login_required
def eliminar_carrito(item_id):
    item = Carrito.query.get_or_404(item_id)

    if item.usuario_id != current_user.id:
        flash('Acceso no permitido', 'danger')
        return redirect(url_for('carrito'))

    db.session.delete(item)
    db.session.commit()
    flash('Producto eliminado del carrito', 'info')
    return redirect(url_for('carrito'))

@app.route('/crear_productos')
def crear_productos():
    if Producto.query.count() == 0:
        p1 = Producto(
            nombre='Mouse Gamer',
            descripcion='Mouse RGB para gaming',
            precio=10.00,
            imagen='producto1.jpg'
        )
        p2 = Producto(
            nombre='Teclado Gamer',
            descripcion='Teclado mecánico RGB',
            precio=20.00,
            imagen='producto2.jpg'
        )
        db.session.add_all([p1, p2])
        db.session.commit()
        return 'Productos creados'
    return 'Los productos ya existen'

    
# Cerrar sesión
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)