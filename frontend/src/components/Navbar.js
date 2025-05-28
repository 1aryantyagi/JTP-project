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
                {user ? (
                    <>
                        <Link to="/">Home</Link>
                        <Link to="/cart">
                            Cart ({cartItems.length})
                        </Link>
                        <span style={{ margin: '0 10px', color: '#3498db' }}>
                            {user.name || user.username}
                        </span>
                        <button onClick={logout} className="logout-btn">
                            Logout
                        </button>
                    </>
                ) : (
                    <>
                        <Link to="/login">Login</Link>
                        <Link to="/register">Register</Link>
                    </>
                )}
            </div>
        </nav>
    );
};

export default Navbar;