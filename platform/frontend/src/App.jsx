import React, { Suspense, lazy } from "react";
import { BrowserRouter as Router, Routes, Route, useLocation } from "react-router-dom";
import Home from "./pages/Home";
import { CartProvider } from "./context/CartContext";

import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import RecoveryAdvisorChat from "./components/RecoveryAdvisorChat";

// Lazy-load subpages to reduce initial bundle size & unused JavaScript on landing page
const Terms = lazy(() => import("./pages/Terms"));
const Privacy = lazy(() => import("./pages/Privacy"));
const About = lazy(() => import("./pages/About"));
const Contact = lazy(() => import("./pages/Contact"));
const Cart = lazy(() => import("./pages/Cart"));
const Checkout = lazy(() => import("./pages/Checkout"));

const Layout = () => {
    const location = useLocation();
    const isHome = location.pathname === "/";

    return (
        <div className="App">
            <Suspense fallback={<div className="min-h-screen bg-[#181717]" />}>
                {!isHome && <Navbar />}
                <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/terms" element={<Terms />} />
                    <Route path="/privacy" element={<Privacy />} />
                    <Route path="/about" element={<About />} />
                    <Route path="/contact" element={<Contact />} />
                    <Route path="/cart" element={<Cart />} />
                    <Route path="/checkout" element={<Checkout />} />
                </Routes>
                {!isHome && <Footer />}
                <RecoveryAdvisorChat />
            </Suspense>
        </div>
    );
};

function App() {
    return (
        <CartProvider>
            <Router>
                <Layout />
            </Router>
        </CartProvider>
    );
}

export default App;
