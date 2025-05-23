import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useCart } from '../contexts/CartContext';
import './Navbar.css';

const Navbar = () => {
    const { user, logout } = useAuth();
    const { cartItems } = useCart();

    return (
        <nav className="navbar">
            <div className="navbar-brand">
                <Link to="/">Product Recommendations</Link>
            </div>
            <div className="navbar-links">
                <Link to="/">Home</Link>
                <Link to="/cart">
                    Cart ({cartItems.length})
                </Link>
                {user && (
                    <button onClick={logout} className="logout-btn">
                        Logout
                    </button>
                )}
            </div>
        </nav>
    );
};

export default Navbar;