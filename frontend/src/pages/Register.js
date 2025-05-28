import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { registerUser } from '../services/api';
import './Login.css';

const Register = () => {
    const [formData, setFormData] = useState({
        name: '',
        user_id: '',
        password: ''
    });
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const response = await registerUser(formData);

            if (response.status === 200) {
                setSuccess(true);
                setTimeout(() => {
                    navigate('/login');
                }, 2000);
            }
        } catch (err) {
            setError('Registration failed. Please try again.');
            console.error('Registration error:', err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-container">
            <div className="login-card">
                <h2>Create an Account</h2>
                {success ? (
                    <div className="success-message">
                        Registration successful! Redirecting to login...
                    </div>
                ) : (
                    <form onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label>Full Name</label>
                            <input
                                type="text"
                                value={formData.name}
                                onChange={(e) => setFormData({
                                    ...formData,
                                    name: e.target.value
                                })}
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label>Username</label>
                            <input
                                type="text"
                                value={formData.user_id}
                                onChange={(e) => setFormData({
                                    ...formData,
                                    user_id: e.target.value
                                })}
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label>Password</label>
                            <input
                                type="password"
                                value={formData.password}
                                onChange={(e) => setFormData({
                                    ...formData,
                                    password: e.target.value
                                })}
                                required
                            />
                        </div>
                        {error && <div className="error-message">{error}</div>}
                        <button
                            type="submit"
                            className="login-btn"
                            disabled={loading}
                        >
                            {loading ? 'Registering...' : 'Sign Up'}
                        </button>
                    </form>
                )}
                <p style={{ marginTop: '1rem', textAlign: 'center' }}>
                    Already have an account?{' '}
                    <a
                        href="#"
                        onClick={(e) => {
                            e.preventDefault();
                            navigate('/login');
                        }}
                        style={{ color: '#3498db' }}
                    >
                        Sign In
                    </a>
                </p>
            </div>
        </div>
    );
};

export default Register;