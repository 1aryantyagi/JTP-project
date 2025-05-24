import React from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  Outlet
} from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { CartProvider } from './contexts/CartContext';
import { ViewedProductsProvider } from './contexts/ViewedProductsContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Recommendations from './pages/Recommendations';
import Cart from './pages/Cart';
import Layout from './components/Layout';
import './App.css';

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <CartProvider>
          <ViewedProductsProvider>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/" element={<ProtectedRoute />}>
                <Route path="/" element={<Layout />}>
                  <Route index element={<Dashboard />} />
                  <Route
                    path="recommendations/:productId"
                    element={<Recommendations />}
                  />
                  <Route path="cart" element={<Cart />} />
                </Route>
              </Route>
            </Routes>
          </ViewedProductsProvider>
        </CartProvider>
      </AuthProvider>
    </Router>
  );
}

function ProtectedRoute() {
  const { user } = useAuth();
  return user ? <Outlet /> : <Navigate to="/login" />;
}