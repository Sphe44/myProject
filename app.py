from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime
import os
from dotenv import load_dotenv
from db import db
# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///devsphere.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# Initialize extensions
db.init_app(app)
mail = Mail(app)

# Import models after db initialization
from models import Service, Portfolio, Contact, TeamMember, Testimonial

@app.route('/')
def index():
    """Home page route"""
    services = Service.query.all()
    portfolio_items = Portfolio.query.limit(6).all()
    team_members = TeamMember.query.all()
    testimonials = Testimonial.query.all()
    
    return render_template('index.html',
                         services=services,
                         portfolio_items=portfolio_items,
                         team_members=team_members,
                         testimonials=testimonials)

@app.route('/contact', methods=['POST'])
def contact_submit():
    """Handle contact form submission"""
    try:
        data = request.get_json()
        
        # Create new contact entry
        contact = Contact(
            name=data['name'],
            email=data['email'],
            subject=data['subject'],
            message=data['message']
        )
        
        db.session.add(contact)
        db.session.commit()
        
        # Send email notification
        msg = Message(
            subject=f'New Contact Form Submission: {data["subject"]}',
            recipients=[os.getenv('CONTACT_EMAIL')],
            body=f'From: {data["name"]} ({data["email"]})\n\n{data["message"]}'
        )
        mail.send(msg)
        
        return jsonify({
            'status': 'success',
            'message': 'Thank you for your message. We will contact you soon!'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'An error occurred. Please try again later.'
        }), 500

@app.route('/portfolio')
def portfolio():
    """Portfolio page route"""
    category = request.args.get('category')
    if category:
        portfolio_items = Portfolio.query.filter_by(category=category).all()
    else:
        portfolio_items = Portfolio.query.all()
    
    categories = db.session.query(Portfolio.category).distinct()
    
    return render_template('portfolio.html',
                         portfolio_items=portfolio_items,
                         categories=categories)

@app.route('/api/portfolio/load-more')
def load_more_portfolio():
    """API endpoint to load more portfolio items"""
    page = int(request.args.get('page', 1))
    per_page = 6
    
    portfolio_items = Portfolio.query.paginate(page=page, per_page=per_page, error_out=False)
    
    data = [{
        'id': item.id,
        'title': item.title,
        'description': item.description,
        'image_url': item.image_url,
        'category': item.category,
    } for item in portfolio_items.items]
    
    return jsonify({
        'items': data,
        'has_more': portfolio_items.has_next
    })

@app.route('/api/testimonials')
def get_testimonials():
    """API endpoint to get testimonials"""
    testimonials = Testimonial.query.all()
    data = [{
        'client_name': t.client_name,
        'client_position': t.client_position,
        'company': t.company,
        'testimonial': t.testimonial,
        'rating': t.rating,
        'image_url': t.image_url
    } for t in testimonials]
    
    return jsonify({'testimonials': data})

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
